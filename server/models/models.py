from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from .database import Base
import enum

class StatusEnum(enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

class Meeting(Base):
    __tablename__ = "meetings"

    meeting_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    audio_id = Column(Integer, ForeignKey("audio.audio_id"))
    status = Column(Enum(StatusEnum), nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=True)
    audio_file = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)

    tags = relationship("Tag", secondary="meetings_tags", back_populates="meetings")

class MeetingTag(Base):
    __tablename__ = "meetings_tags"

    meeting_id = Column(Integer, ForeignKey("meetings.meeting_id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.tag_id"), primary_key=True)

class Tag(Base):
    __tablename__ = "tags"

    tag_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    meetings = relationship("Meeting", secondary="meetings_tags", back_populates="tags")

class Audio(Base):
    __tablename__ = "audio"

    audio_id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False, unique=True)  # Ensure company is unique

    devices = relationship("AudioDevices", back_populates="audio")

class AudioDevices(Base):
    __tablename__ = "audio_devices"

    audio_id = Column(Integer, ForeignKey("audio.audio_id"), primary_key=True)
    name = Column(String, nullable=False, primary_key=True)
    channel = Column(Integer, nullable=False, primary_key=True)
    n_channels = Column(Integer, nullable=False)

    audio = relationship("Audio", back_populates="devices")

class Setting(Base):
    __tablename__ = "setting"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(String, nullable=False)