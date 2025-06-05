import asyncio
import yaml
from library.prompts import SummarizePrompt
from openai import OpenAI

# Load the configuration from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Extract the API keys and models
INSTANT_API_KEY = config['INSTANT_API_KEY']
INSTANT_BASE_URL = config['INSTANT_BASE_URL']
INSTANT_MODEL = config['INSTANT_MODEL']

# Mock async functions for diarization and summarization
async def diarize(audio_file, whisper_model, diarization_pipeline):
    # --- Step 1: Run Diarization ---
    diarization = diarization_pipeline(audio_file)

    # --- Step 2: Run Whisper Transcription ---
    # transcription = whisper_model.transcribe(audio_path, verbose=False, word_timestamps=True)
    transcription = whisper_model.transcribe(
        audio_file,
        verbose=False,
        logprob_threshold=-.4,
        no_speech_threshold=.4,
        word_timestamps=True,  # Enable word-level timestamps
        hallucination_silence_threshold=1.0  # Skip silent periods longer than 2.0 seconds
    )

    result = []
    current_speaker = None
    current_text = []

    for segment in transcription['segments']:
        start = segment['start']
        end = segment['end']
        text = segment['text'].strip()

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
