from pydantic import BaseModel
from typing import List, Optional
from schemas.tag_schema import TagSchema

class MeetingStart(BaseModel):
    audio_id: int

class MeetingBase(MeetingStart):
    meeting_id: int
    title: str
    # audio_id: int
    status: str
    start_time: str
    end_time: Optional[str]
    audio_file: Optional[str]
    transcript: Optional[str]
    summary: Optional[str]

class MeetingTags(MeetingBase):
    tags: List[TagSchema] = []

class UpdateTitleRequest(BaseModel):
    title: str
