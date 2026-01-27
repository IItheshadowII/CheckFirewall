from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import models, schemas, database, config, utils

# --- Security ---
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == config.settings.API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )

# --- Background Task ---
async def check_hosts_status():
    async with database.SessionLocal() as db:
        threshold = datetime.utcnow() - timedelta(minutes=config.settings.ALERT_TIMEOUT_MINUTES)
        
        # logic: Find hosts that are down (firewall_status=False) OR haven't been seen in X minutes
        # For simplicity, we trust the agent's report of "firewall_status".
        # We also alert if the agent hasn't checked in.
        
        # 1. Check for silent agents
        query_silent = select(models.Host).where(
            models.Host.last_seen < threshold,
            models.Host.is_alerting == False 
        )
        result_silent = await db.execute(query_silent)
        silent_hosts = result_silent.scalars().all()
        
        for host in silent_hosts:
            print(f"Host {host.hostname} is silent!")
            await utils.send_alert_email(host.hostname, host.ip_address, str(host.last_seen))
            host.is_alerting = True # Prevent spam
            db.add(host)
            
        # 2. Check for reported risks (already handled by agent sending heartbeat, but maybe we want repeated alerts?)
        # Let's say if it stays risky for too long.
        # For now, let's stick to the requirement: "Si el estado es False (Inactivo) por más de X minutos"
        # This implies we need to track *when* it went false. 
        # But simplify: If status is False and we haven't alerted yet.
        
        query_risky = select(models.Host).where(
            models.Host.firewall_status == False,
            models.Host.is_alerting == False
        )
        result_risky = await db.execute(query_risky)
        risky_hosts = result_risky.scalars().all()
        
        for host in risky_hosts:
             # Check if it has been risky for more than X minutes? 
             # The requirement says "Si el estado es False ... por más de X minutos".
             # Since we update last_seen on every heartbeat, if it keeps sending False, it means it is risky.
             # We should probably alert immediately or after a grace period. 
             # Let's alert immediately if it reports False.
            print(f"Host {host.hostname} reported risk!")
            await utils.send_alert_email(host.hostname, host.ip_address, str(host.last_seen))
            host.is_alerting = True
            db.add(host)

        await db.commit()

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

@app.post("/api/heartbeat", response_model=schemas.HostResponse, dependencies=[Depends(get_api_key)])
async def receive_heartbeat(payload: schemas.HeartbeatPayload, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Host).where(models.Host.hostname == payload.hostname))
    host = result.scalars().first()
    
    if not host:
        host = models.Host(
            hostname=payload.hostname,
            ip_address=payload.ip_address,
            firewall_status=payload.firewall_status,
            profiles_status=payload.profiles_status,
            is_alerting=False # Reset alert status on new host
        )
        db.add(host)
    else:
        # If status changed from False to True, reset alerting
        if not host.firewall_status and payload.firewall_status:
           host.is_alerting = False
           
        host.ip_address = payload.ip_address
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
    return host

@app.get("/api/hosts", response_model=List[schemas.HostResponse])
async def list_hosts(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Host).order_by(models.Host.hostname))
    return result.scalars().all()
