from pydantic import BaseModel
from enum import Enum
from typing import List

class Category(str, Enum):
    trivia = "trivia"
    resume = "resume"
    coding = "coding"
    system_design = "system_design"
    clarify = "clarify"

class Classification(BaseModel):
    category: Category

class ChatRequest(BaseModel):
    conversation: str
    question_type: str = None
    use_image: bool = False
    use_reasoning: bool = False

class ChatResponse(BaseModel):
    response: str
    question_type: str

class SettingSchema(BaseModel):
    key: str
    value: str

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionsRequest(BaseModel):
    messages: List[Message]