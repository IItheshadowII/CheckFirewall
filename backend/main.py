from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Security, status, Response, WebSocket, WebSocketDisconnect, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import models, schemas, database, config, utils
from fastapi.encoders import jsonable_encoder
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        data = jsonable_encoder(message)
        to_remove = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                to_remove.append(connection)
        for c in to_remove:
            self.disconnect(c)


manager = ConnectionManager()

# --- Security ---
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == config.settings.API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )

async def _collect_alert_hosts(db: AsyncSession, include_already_alerting: bool = False):
    """Return hosts that should trigger an alert.

    - Silent: last_seen older than threshold
    - Risky: firewall_status == False
    - Skip acknowledged hosts
    - Optionally skip hosts we already alerted on (is_alerting=True)
    """

    threshold = datetime.utcnow() - timedelta(minutes=config.settings.ALERT_TIMEOUT_MINUTES)

    # Treat NULL booleans as False for backward compatibility with older DBs.
    base_filters = [or_(models.Host.is_acknowledged.is_(False), models.Host.is_acknowledged.is_(None))]
    if not include_already_alerting:
        base_filters.append(or_(models.Host.is_alerting.is_(False), models.Host.is_alerting.is_(None)))

    query_silent = select(models.Host).where(
        models.Host.last_seen < threshold,
        *base_filters,
    )
    result_silent = await db.execute(query_silent)
    silent_hosts = result_silent.scalars().all()

    query_risky = select(models.Host).where(
        or_(models.Host.firewall_status.is_(False), models.Host.firewall_status.is_(None)),
        *base_filters,
    )
    result_risky = await db.execute(query_risky)
    risky_hosts = result_risky.scalars().all()

    unique = {h.id: h for h in silent_hosts + risky_hosts}
    return list(unique.values())


# --- Background Task ---
async def check_hosts_status():
    async with database.SessionLocal() as db:
        alert_hosts = await _collect_alert_hosts(db, include_already_alerting=False)
        if not alert_hosts:
            return

        print(f"Found {len(alert_hosts)} host(s) requiring alert")
        await utils.send_alert_email(alert_hosts, manual=False)

        # Mark them as alerted to avoid spam
        for host in alert_hosts:
            host.is_alerting = True
            db.add(host)

        await db.commit()

        # Broadcast updated hosts if their alerting state changed
        for host in alert_hosts:
            try:
                await manager.broadcast({"action": "upsert", "host": jsonable_encoder(host)})
            except Exception:
                pass

# --- Jobs & Lifespan ---
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with database.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        
    scheduler.add_job(check_hosts_status, "interval", minutes=1)
    scheduler.start()
    
    yield
    
    # Shutdown
    scheduler.shutdown()

app = FastAPI(title="FirewallWatch API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---

@app.get("/api/settings", response_model=schemas.SettingsResponse)
async def get_settings():
    return schemas.SettingsResponse(
        alert_timeout_minutes=config.settings.ALERT_TIMEOUT_MINUTES,
        alert_recipient_email=config.settings.ALERT_RECIPIENT_EMAIL,
    )

@app.post("/api/heartbeat", response_model=schemas.HostResponse, dependencies=[Depends(get_api_key)])
async def receive_heartbeat(payload: schemas.HeartbeatPayload, request: Request, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Host).where(models.Host.hostname == payload.hostname))
    host = result.scalars().first()
    
    if not host:
        # Use payload ip_address if provided, otherwise fallback to request client IP
        host_ip = None
        if getattr(payload, 'ip_address', None):
            host_ip = payload.ip_address
        elif request and request.client:
            host_ip = request.client.host
        host = models.Host(
            hostname=payload.hostname,
            ip_address=host_ip,
            firewall_status=payload.firewall_status,
            profiles_status=payload.profiles_status,
            is_alerting=False # Reset alert status on new host
        )
        db.add(host)
    else:
        # If status changed from False to True, reset alerting
        if not host.firewall_status and payload.firewall_status:
           host.is_alerting = False
           
        # Update ip_address if provided in payload, otherwise override if currently empty or 'Unknown'
        if getattr(payload, 'ip_address', None):
            host.ip_address = payload.ip_address
        elif request and request.client and (not host.ip_address or host.ip_address == 'Unknown'):
            host.ip_address = request.client.host
        host.firewall_status = payload.firewall_status
        host.profiles_status = payload.profiles_status
        host.last_seen = datetime.utcnow()
        # If we are getting a heartbeat, it means it's alive.
        # If it was silent (alerting=True due to timeout), reset it?
        # Only reset alerting if the specific condition is cleared. 
        # If it was alerting due to Risk, and it is still Risk, keep alerting = True (to avoid spam).
        # If it was alerting due to Timeout, and now it answers, we should reset.
        
        # Heuristic: If it is OK, always reset alerting.
        if payload.firewall_status:
            host.is_alerting = False
        
    await db.commit()
    await db.refresh(host)
    # Notify websocket clients about new or updated host
    try:
        await manager.broadcast({"action": "upsert", "host": jsonable_encoder(host)})
    except Exception:
        pass
    return host

@app.get("/api/hosts", response_model=List[schemas.HostResponse])
async def list_hosts(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Host).order_by(models.Host.hostname))
    return result.scalars().all()


@app.post("/api/hosts/{host_id}/ack", status_code=204, dependencies=[Depends(get_api_key)])
async def set_host_acknowledged(host_id: int, payload: schemas.HostAckPayload, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Host).where(models.Host.id == host_id))
    host = result.scalars().first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    host.is_acknowledged = payload.acknowledged
    # If user acknowledges, we also clear is_alerting to avoid confusing state
    if host.is_acknowledged:
        host.is_alerting = False
    db.add(host)
    await db.commit()
    await db.refresh(host)

    try:
        await manager.broadcast({"action": "upsert", "host": jsonable_encoder(host)})
    except Exception:
        pass

    return Response(status_code=204)


@app.post("/api/alerts/send", dependencies=[Depends(get_api_key)])
async def send_manual_alerts(db: AsyncSession = Depends(database.get_db)):
    alert_hosts = await _collect_alert_hosts(db, include_already_alerting=True)
    if not alert_hosts:
        return {"sent": False, "count": 0}

    await utils.send_alert_email(alert_hosts, manual=True)
    return {"sent": True, "count": len(alert_hosts)}


@app.delete("/api/hosts/{host_id}", status_code=204, dependencies=[Depends(get_api_key)])
async def delete_host(host_id: int, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Host).where(models.Host.id == host_id))
    host = result.scalars().first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    await db.delete(host)
    await db.commit()
    # Notify websocket clients that host was deleted
    try:
        await manager.broadcast({"action": "delete", "host": {"id": host_id}})
    except Exception:
        pass
    return Response(status_code=204)


@app.websocket("/ws/hosts")
async def websocket_hosts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open; clients are not required to send messages.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
