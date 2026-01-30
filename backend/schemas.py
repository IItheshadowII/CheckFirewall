from typing import Dict
from datetime import datetime
from pydantic import BaseModel

class HeartbeatPayload(BaseModel):
    hostname: str
    ip_address: str
    firewall_status: bool
    profiles_status: Dict[str, bool]

class HostResponse(HeartbeatPayload):
    id: int
    last_seen: datetime

    class Config:
        from_attributes = True


class SettingsResponse(BaseModel):
    alert_timeout_minutes: int
    alert_recipient_email: str
