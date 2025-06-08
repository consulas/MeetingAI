import asyncio
import yaml
from library.prompts import SummarizePrompt
from openai import OpenAI

import torch
from pyannote.audio import Pipeline
import soundfile as sf
import nemo.collections.asr as nemo_asr

# Load the configuration from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Extract the API keys and models
INSTANT_API_KEY = config['INSTANT_API_KEY']
INSTANT_BASE_URL = config['INSTANT_BASE_URL']
INSTANT_MODEL = config['INSTANT_MODEL']
HUGGINGFACE_TOKEN = config['HUGGINGFACE_TOKEN']

# Mock async functions for diarization and summarization
async def diarize(audio_file):
    # Transcribe the audio
    asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")
    audio_signal, sample_rate = sf.read(audio_file)
    transcript = asr_model.transcribe(audio_signal, timestamps=True)
    # May change to 'character'/'word'/'segment'
    text_type = 'word'
    transcript = transcript[0].timestamp[text_type]

    # Perform diarization
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=HUGGINGFACE_TOKEN)
    pipeline.to(torch.device("cuda"))
    diarization = pipeline(audio_file)

    del asr_model
    del pipeline
    torch.cuda.empty_cache()

    result = []
    current_speaker = None
    current_text = []

    for segment in transcript:
        start = segment['start']
        end = segment['end']
        text = segment[text_type].strip()

        # Find the speaker label that overlaps the most with this segment
        speaker = "Unknown"
        max_overlap = 0

        for turn, _, label in diarization.itertracks(yield_label=True):
            overlap = max(0, min(end, turn.end) - max(start, turn.start))
            if overlap > max_overlap:
                max_overlap = overlap
                speaker = label

        if current_speaker is None:
            current_speaker = speaker
            current_text.append((start, end, text))
        elif speaker == current_speaker:
            current_text.append((start, end, text))
        else:
            # Append the current speaker's text
            result.append({
                "speaker": current_speaker,
                "text": ' '.join([t[2] for t in current_text])
            })
            # Reset for the new speaker
            current_speaker = speaker
            current_text = [(start, end, text)]

    # Append the last speaker's text
    if current_text:
        result.append({
            "speaker": current_speaker,
            "text": ' '.join([t[2] for t in current_text])
        })

    return result

async def summarize(transcript):
    client = OpenAI(base_url = INSTANT_BASE_URL, api_key = INSTANT_API_KEY)
    prompt_object = SummarizePrompt(transcript)
    messages = prompt_object.get_messages()

    # Send to client
    response = client.chat.completions.create(
        model=INSTANT_MODEL,
        stream=False,
        messages=messages,
    )

    response_message = response.choices[0].message.content if response.choices else ""

    return response_message
