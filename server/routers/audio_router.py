from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.models import Audio, AudioDevices
from schemas.audio_schema import AudioSchema, AudioDevicesSchema
from pydantic import BaseModel
from typing import List
import pyaudio

router = APIRouter()
devices = None

def get_pyaudio_devices():
    """
    :return: dict of device names to number of channels
    """
    global devices
    if devices is not None: 
        return devices
    audio = pyaudio.PyAudio()
    devices = {}
    # print("Flag")
    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0 and device_info['hostApi'] == 0:
            devices[device_info['name']] = device_info["maxInputChannels"]
    audio.terminate()
    return devices

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_audio_devices_by_audio_id(audio_id: int, db: Session) -> List[AudioDevicesSchema]:
    devices = db.query(AudioDevices).filter(AudioDevices.audio_id == audio_id).all()
    return [
        AudioDevicesSchema(
            name=device.name,
            channel=device.channel,
            n_channels=device.n_channels
        ) for device in devices
    ]

def get_audio_with_devices(audio_id: int, db: Session) -> AudioSchema:
    audio_record = db.query(Audio).filter(Audio.audio_id == audio_id).first()
    if not audio_record:
        raise HTTPException(status_code=404, detail="Audio record not found")

    devices = get_audio_devices_by_audio_id(audio_id, db)
    return AudioSchema(
        company=audio_record.company,
        audio_id=audio_record.audio_id,
        devices=devices
    )

def delete_audio_devices_by_audio_id(audio_id: int, db: Session):
    db.query(AudioDevices).filter(AudioDevices.audio_id == audio_id).delete()

@router.get("/audio-devices")
def get_audio_devices():
    return get_pyaudio_devices()

@router.get("/audio", response_model=List[AudioSchema])
def get_all_audio_with_devices(db: Session = Depends(get_db)):
    audio_records = db.query(Audio).all()
    return [get_audio_with_devices(audio.audio_id, db) for audio in audio_records]

@router.post("/audio", response_model=AudioSchema)
def create_or_update_audio(audio: AudioSchema, db: Session = Depends(get_db)):
    audio_record = db.query(Audio).filter(Audio.company == audio.company).first()
    if not audio_record:
        audio_record = Audio(company=audio.company)
        db.add(audio_record)
        db.commit()
        db.refresh(audio_record)

    audio_id = audio_record.audio_id
    delete_audio_devices_by_audio_id(audio_id, db)

    pyaudio_devices = get_pyaudio_devices()
    for device in audio.devices:
        n_channels = pyaudio_devices.get(device.name)
        if not n_channels:
            raise HTTPException(status_code=400, detail=f"Device with index {device.name} not found")
        db.add(AudioDevices(
            audio_id=audio_id,
            name=device.name,
            n_channels=n_channels,
            channel=device.channel
        ))
    db.commit()

    return get_audio_with_devices(audio_id, db)

@router.get("/audio/{audio_id}", response_model=AudioSchema)
def get_audio_by_id(audio_id: int, db: Session = Depends(get_db)):
    return get_audio_with_devices(audio_id, db)

# 
# Disabled delete endpoint
# Maybe in the future, just delete audio_devices rows?
# 
# @router.delete("/audio/{audio_id}", response_model=dict)
# def delete_audio(audio_id: int, db: Session = Depends(get_db)):
#     delete_audio_devices_by_audio_id(audio_id, db)

#     audio_record = db.query(Audio).filter(Audio.audio_id == audio_id).first()
#     if not audio_record:
#         raise HTTPException(status_code=404, detail="Audio record not found")
#     db.delete(audio_record)
#     db.commit()
#     return {"message": "Audio record and related devices deleted successfully"}
