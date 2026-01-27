from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from database import Base

class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True)
    ip_address = Column(String)
    firewall_status = Column(Boolean)  # True = OK, False = Risk
    profiles_status = Column(JSON)     # Dict of profiles
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_alerting = Column(Boolean, default=False) # To track if we have already sent an alert for this down state

    def __repr__(self):
        return f"<Host(hostname={self.hostname}, status={self.firewall_status})>"
