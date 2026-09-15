from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Classification(Base):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    signal_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    metadata_json = Column(JSON, nullable=True)