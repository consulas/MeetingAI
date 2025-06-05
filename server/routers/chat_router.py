
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.database import SessionLocal
from schemas.chat_schema import ChatRequest, ChatResponse, Classification, Category, SettingSchema, ChatCompletionsRequest
from models.models import Setting
from library.prompts import ClassifyPrompt, TriviaPrompt, ResumePrompt, CodingPrompt, SystemDesignPrompt, ClarifyPrompt
import yaml
from typing import List
from openai import OpenAI
import instructor
import mss
from PIL import Image
import base64
from io import BytesIO

# Load the configuration from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Extract the API keys and models
INSTANT_API_KEY = config['INSTANT_API_KEY']
INSTANT_BASE_URL = config['INSTANT_BASE_URL']
INSTANT_MODEL = config['INSTANT_MODEL']
REASONING_API_KEY = config['REASONING_API_KEY']
REASONING_BASE_URL = config['REASONING_BASE_URL']
REASONING_MODEL = config['REASONING_MODEL']

router = APIRouter()

classification_client = instructor.from_openai(OpenAI(base_url = INSTANT_BASE_URL, api_key = INSTANT_API_KEY))
instant_client = OpenAI(base_url = INSTANT_BASE_URL, api_key = INSTANT_API_KEY)
reasoning_client = OpenAI(base_url = REASONING_BASE_URL, api_key = REASONING_API_KEY)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_encoded_screenshot(monitor_number):
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[monitor_number])  # Change index if needed

        # Convert to PIL Image and save to buffer
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Encode as base64
        return base64.b64encode(buffer.read()).decode('utf-8')

def classify_conversation(conversation):
    prompt = ClassifyPrompt(conversation)
    completion = classification_client.chat.completions.create(
        model = INSTANT_MODEL,
        messages=prompt.get_messages(),
        response_model=Classification,
    )
    return completion.category.value

def get_settings_map(db: Session):
    settings = db.query(Setting).all()
    return {setting.key: setting.value for setting in settings}

@router.get("/settings", response_model=List[SettingSchema])
def get_all_settings(db: Session = Depends(get_db)):
    settings = db.query(Setting).all()
    return [{"key": setting.key, "value": setting.value} for setting in settings]

@router.post("/settings", response_model=SettingSchema)
def save_setting(request: SettingSchema, db: Session = Depends(get_db)):
    existing_setting = db.query(Setting).filter_by(key=request.key).first()
    if existing_setting:
        existing_setting.value = request.value
    else:
        setting = Setting(key=request.key, value=request.value)
        db.add(setting)
    db.commit()
    db.refresh(existing_setting or setting)
    return existing_setting or setting

@router.post("/chat", response_model=ChatResponse)
def getChatResponse(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    # Classify the request if question_type is null
    if request.question_type is None:  
        request.question_type = classify_conversation(request.conversation)

    # What model to use
    client = instant_client
    model = INSTANT_MODEL
    if request.use_reasoning:
        client = reasoning_client
        model = REASONING_MODEL

    # Get resume, job_description, and monitor # from settings if requested
    settings = get_settings_map(db)
    resume = settings.get('resume', "")
    job_description = settings.get('job_description', "")
    monitor_number = int(settings.get('monitor_number', "1"))

    # Create the appropriate prompt based on the question type
    if request.question_type == "trivia":
        prompt_object = TriviaPrompt(request.conversation, resume)
    elif request.question_type == "resume":
        prompt_object = ResumePrompt(request.conversation, resume)
    elif request.question_type == "coding":
        prompt_object = CodingPrompt(request.conversation)
    elif request.question_type == "system_design":
        prompt_object = SystemDesignPrompt(request.conversation)
    elif request.question_type == "clarify":
        prompt_object = ClarifyPrompt(request.conversation)
    else:
        raise HTTPException(status_code=400, detail="Invalid question type")

    messages = prompt_object.get_messages()    
    if request.use_image:
        messages=[
            {"role": "system", "content": prompt_object.system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_object.prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{get_encoded_screenshot(monitor_number)}",
                        },
                    },
                ]
            }
        ]

    # Send to client
    response = client.chat.completions.create(
        model=model,
        stream=False,
        messages=messages,
    )

    response_message = response.choices[0].message.content if response.choices else ""

    # Send response message back
    return ChatResponse(response=response_message, question_type = request.question_type)


@router.post("/chat/completions", response_model=str)
def getChatCompletions(request: ChatCompletionsRequest, db: Session = Depends(get_db)) -> str:
    # Pass the messages to the instant_client
    response = instant_client.chat.completions.create(
        model=INSTANT_MODEL,
        stream=False,
        messages=request.messages,
    )

    # Return the response message
    response_message = response.choices[0].message.content if response.choices else ""
    return response_message