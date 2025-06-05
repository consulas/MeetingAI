from pydantic import BaseModel
from typing import List, Optional

# Use device_name as the key because device_idx can change
class AudioDevicesSchema(BaseModel):
    name: str
    channel: int
    n_channels: Optional[int] = None

class AudioSchema(BaseModel):
    company: str
    audio_id: Optional[int] = None
    devices: List[AudioDevicesSchema]
