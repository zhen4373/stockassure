import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from core.database import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("locations.id", ondelete="RESTRICT"), default=None)

    parent = relationship("Location", remote_side=[id], backref="children")


class CoreObject(Base):
    __tablename__ = "objects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    template_type = Column(String, nullable=False)
    extra_data = Column(Text, nullable=False, default="{}")

    location = relationship("Location", backref="objects")