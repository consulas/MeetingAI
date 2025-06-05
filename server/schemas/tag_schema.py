from pydantic import BaseModel
from typing import Optional

class TagSchema(BaseModel):
    tag_id: Optional[int] = None
    name: str