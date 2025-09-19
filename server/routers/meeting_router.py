import os, time, asyncio, json
from fastapi import APIRouter, HTTPException, Depends, WebSocket, Query
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.models import Meeting, MeetingTag, Tag
from schemas.meeting_schema import MeetingStart, MeetingBase, MeetingTags, UpdateTitleRequest
from schemas.tag_schema import TagSchema
from typing import List
from routers.audio_router import get_audio_devices_by_audio_id
from services.audio_service import AudioService
from services.post_processing import diarize, summarize
from pydantic import BaseModel
import torch
import whisper
from pyannote.audio import Pipeline

import yaml
# Load the configuration from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

router = APIRouter()

# meeting_id -> AudioService
services = {}  

if torch.backends.cuda.is_built():
    device = "cuda"
else:
    device = "cpu"

# whisper_model = whisper.load_model("base.en", device=device)
whisper_model = whisper.load_model("turbo", device=device)
HUGGINGFACE_TOKEN = config.get("HUGGINGFACE_TOKEN", "") 

diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=HUGGINGFACE_TOKEN)
diarization_pipeline.to(torch.device(device))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_time() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())

def get_meeting_by_id(meeting_id: int, db: Session) -> Meeting:
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

def get_tags_for_meeting(meeting_id: int, db: Session) -> List[TagSchema]:
    tags = db.query(Tag).join(MeetingTag).filter(MeetingTag.meeting_id == meeting_id).all()
    return [TagSchema(tag_id=tag.tag_id, name=tag.name) for tag in tags]

def create_meeting_tags_response(meeting: Meeting, db: Session) -> MeetingTags:
    tags = get_tags_for_meeting(meeting.meeting_id, db)
    return MeetingTags(
        meeting_id=meeting.meeting_id,
        title=meeting.title,
        audio_id=meeting.audio_id,
        status=meeting.status,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        audio_file=meeting.audio_file,
        transcript=meeting.transcript,
        summary=meeting.summary,
        tags=tags
    )

def get_or_create_tag(tag_name: str, db: Session) -> Tag:
    tag = db.query(Tag).filter(Tag.name == tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        db.commit()
        db.refresh(tag)
    return tag

def add_meeting_tag_relationship(meeting_id: int, tag_id: int, db: Session):
    meeting_tag = db.query(MeetingTag).filter(
        MeetingTag.meeting_id == meeting_id,
        MeetingTag.tag_id == tag_id
    ).first()
    if not meeting_tag:
        meeting_tag = MeetingTag(meeting_id=meeting_id, tag_id=tag_id)
        db.add(meeting_tag)
        db.commit()

@router.post("/meetings/start", response_model=MeetingBase)
async def start_meeting(meeting: MeetingStart, db: Session = Depends(get_db)):
    new_meeting = Meeting(
        title="Untitled Meeting",
        audio_id=meeting.audio_id,
        status="ACTIVE",
        start_time=get_current_time(),
    )
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    # Start the audio service for this meeting
    audio_device_info = get_audio_devices_by_audio_id(meeting.audio_id, db)
    service = AudioService(audio_device_info, whisper_model, new_meeting.meeting_id)
    services[new_meeting.meeting_id] = service
    asyncio.create_task(service.start())

    return new_meeting

@router.websocket("/meetings/{meeting_id}")
async def meeting_websocket(websocket: WebSocket, meeting_id: int):
    await websocket.accept()
    service = services.get(meeting_id)
    if not service:
        await websocket.send_text("No audio service running for this meeting.")
        await websocket.close()
        return

    try:
        while True:
            transcription = service.get_transcription()
            await websocket.send_text(transcription)
            await asyncio.sleep(1)  # Send updates every second
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        print("Closing WebSocket connection")

@router.post("/meetings/{meeting_id}/stop", response_model=MeetingTags)
async def stop_meeting(meeting_id: int, db: Session = Depends(get_db)):
    # Stop the audio service and print the transcription
    meeting = get_meeting_by_id(meeting_id, db)
    service = services.pop(meeting_id, None)
    transcript = ""
    if service:
        transcript = service.get_transcription()
        meeting.transcript = json.dumps([{'speaker': 'Unknown', 'text': transcript}])
        service.stop()
    else:
        print("No audio service running for this meeting.")

    audio_file = os.path.join(config.get('OUTPUT_DIR', './recordings/'), f"{meeting_id}.wav")
    meeting.status = "COMPLETED"
    meeting.audio_file = audio_file
    meeting.end_time = get_current_time()

    db.commit()  # Commit status before async services

    # Kick off the diarization_service and summarization_service
    # diarization_task = asyncio.create_task(diarize(audio_file, whisper_model, diarization_pipeline))
    # summarization_task = asyncio.create_task(summarize(transcript))

    # Wait for both services to complete
    # diarized_transcript, finished_summary = await asyncio.gather(diarization_task, summarization_task)
    # finished_summary = await asyncio.gather(summarization_task)

    # meeting.transcript = json.dumps(diarized_transcript)
    # meeting.summary = finished_summary

    db.commit()  # Commit status after async services

    db.refresh(meeting)

    return create_meeting_tags_response(meeting, db)

@router.delete("/meetings/{meeting_id}", response_model=dict)
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    # Stop the audio service if it's running
    service = services.pop(meeting_id, None)
    if service:
        service.stop()

    db.query(MeetingTag).filter(MeetingTag.meeting_id == meeting_id).delete()
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    db.delete(meeting)
    db.commit()
    return {"message": "Meeting and associated tags deleted successfully"}

# TODO Add offset if meetings > 100
@router.get("/meetings", response_model=List[MeetingTags])
def get_all_meetings(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    tags: List[str] = Query(None)
):
    # offset = (page - 1) * 10
    query = db.query(Meeting).order_by(Meeting.start_time.desc())
    if tags:
        query = query.join(MeetingTag).join(Tag).filter(Tag.name.in_(tags)).distinct()
    meetings = query.all()
    # meetings = query.offset(offset).limit(10).all()
    return [create_meeting_tags_response(meeting, db) for meeting in meetings]

@router.get("/meetings/{meeting_id}", response_model=MeetingTags)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = get_meeting_by_id(meeting_id, db)
    return create_meeting_tags_response(meeting, db)

@router.post("/meetings/{meeting_id}", response_model=MeetingTags)
def update_meeting_title(meeting_id: int, request: UpdateTitleRequest, db: Session = Depends(get_db)):
    meeting = get_meeting_by_id(meeting_id, db)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    meeting.title = request.title
    db.commit()
    db.refresh(meeting)

    return create_meeting_tags_response(meeting, db)

@router.post("/meetings/{meeting_id}/tags", response_model=TagSchema)
def add_meeting_tag(meeting_id: int, tag: TagSchema, db: Session = Depends(get_db)):
    tag = get_or_create_tag(tag.name, db)
    add_meeting_tag_relationship(meeting_id, tag.tag_id, db)
    return tag

@router.delete("/meetings/{meeting_id}/tags/{tag_id}", response_model=dict)
def delete_meeting_tag(meeting_id: int, tag_id: int, db: Session = Depends(get_db)):
    meeting_tag = db.query(MeetingTag).filter(
        MeetingTag.meeting_id == meeting_id,
        MeetingTag.tag_id == tag_id
    ).first()
    if not meeting_tag:
        raise HTTPException(status_code=404, detail="Meeting tag not found")
    db.delete(meeting_tag)
    db.commit()
    return {"message": "Meeting tag deleted successfully"}
