from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    portal = Column(String, nullable=True)  # LinkedIn/Naukri/etc.
    status = Column(String, default="Pending")  # Applied/Rejected/Interview/...
    applied_date = Column(DateTime, default=datetime.utcnow)
