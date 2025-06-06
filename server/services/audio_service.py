import asyncio
import io
import wave
import numpy as np
import pyaudio
from datetime import timedelta, datetime
import os
import threading
import queue
import yaml
import requests

# Load the configuration from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

FORMAT = pyaudio.paInt16

def rms_energy(samples: np.ndarray) -> float:
    """
    Computes RMS energy for a NumPy array of int16 audio samples.
    """
    return np.sqrt(np.mean(samples.astype(np.float32) ** 2))

class AudioService:
    def __init__(self, audio_device_info,
                 whisper_model, meeting_id,
                 sample_rate=16000, chunk_size=1024,
                 transcribe_rate=config.get('TRANSCRIBE_RATE', .5),
                 silence_seconds=config.get('SILENCE_SECONDS', 1),
                 threshold=config.get('THRESHOLD', 0),
                 max_record_time=config.get('MAX_RECORD_TIME', 30),
                 output_dir=config.get('OUTPUT_DIR', "./recordings/")):

        # audio_device_info: list of objects with name, channel, n_channels
        self.audio_device_info = audio_device_info
        self.whisper_model = whisper_model
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.transcribe_rate = timedelta(seconds=transcribe_rate)
        self.silence_seconds = silence_seconds
        self.threshold = threshold
        self.max_record_time = max_record_time
        self.transcript = ''
        self.current_phrase = ''
        self.running = False
        self.output_dir = output_dir
        self.meeting_id = meeting_id
        self.data_queue = queue.Queue()
        self.record_thread = None

    def _find_device_index(self, name):
        pa = pyaudio.PyAudio()
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if name.lower() in info.get('name', '').lower():
                pa.terminate()
                return i
        pa.terminate()
        raise ValueError(f"Audio device '{name}' not found")

    def recording_thread(self):
        """
        Thread function to capture audio and enqueue it for processing, and save to WAV file.
        """
        pa = pyaudio.PyAudio()

        # Open streams for each audio device
        streams = []
        for dev in self.audio_device_info:
            idx = self._find_device_index(dev.name)
            stream = pa.open(format=FORMAT,
                             channels=dev.n_channels,
                             rate=self.sample_rate,
                             input=True,
                             input_device_index=idx,
                             frames_per_buffer=self.chunk_size)
            streams.append(stream)

        # Create a wave file to save the mixed audio
        wav_filename = os.path.join(self.output_dir, f"{self.meeting_id}.wav")
        wf = wave.open(wav_filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(pa.get_sample_size(FORMAT))
        wf.setframerate(self.sample_rate)
        
        # Start recording, mixing, and saving audio
        # Write to the queue for processing
        while self.running:
            channel_audios = []
            for stream, dev in zip(streams, self.audio_device_info):
                raw_audio = np.frombuffer(stream.read(self.chunk_size), dtype=np.int16)
                channel_audio = raw_audio[dev.channel::dev.n_channels]
                channel_audios.append(channel_audio)
            mixed_audio = np.mean(channel_audios, axis=0).astype(np.int16).tobytes()
            wf.writeframes(mixed_audio)
            self.data_queue.put(mixed_audio)

        # Close the wave file and streams
        wf.close()
        for stream in streams:
            stream.stop_stream()
            stream.close()
        pa.terminate()

    async def start(self):
        buffer = bytearray()
        samples_with_silence = 0
        silence_limit = int(self.sample_rate / self.chunk_size * self.silence_seconds)
        next_transcribe_time = datetime.utcnow() + self.transcribe_rate

        self.running = True

        # Start the recording thread
        self.record_thread = threading.Thread(target=self.recording_thread)
        self.record_thread.start()

        while self.running:
            now = datetime.utcnow()
            if now >= next_transcribe_time:
                next_transcribe_time = now + self.transcribe_rate
                while not self.data_queue.empty():
                    data = self.data_queue.get()

                    energy = rms_energy(np.frombuffer(data, dtype=np.int16))
                    samples_with_silence += 1 if energy < self.threshold else 0
                    
                    # If silence_limit is reached, or greater than 30 seconds, reset buffer
                    if samples_with_silence > silence_limit or len(buffer) > self.max_record_time * self.sample_rate:
                        buffer = bytearray()
                        self.transcript += self.current_phrase + '\n'
                        self.current_phrase = ''
                    
                    buffer.extend(data)


                buffer_io = io.BytesIO()
                wf = wave.open(buffer_io, 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(pyaudio.get_sample_size(FORMAT))
                wf.setframerate(self.sample_rate)
                wf.writeframes(buffer)
                wf.close()

                # Reset buffer position to start
                buffer_io.seek(0)

                # Prepare request
                form_data = {
                    'file': ('file', buffer_io),
                    'response_format': 'text'
                }

                asyncio.create_task(self._transcribe_audio(buffer_io))

            await asyncio.sleep(.1)

    async def _transcribe_audio(self, buffer_io):
        response = requests.post('http://localhost:8081/inference', files={'file': ('file', buffer_io), 'response_format': 'text'})
        self.current_phrase = response.text.strip()

    def stop(self):
        self.running = False
        if self.record_thread:
            self.record_thread.join()

    def get_transcription(self):
        return self.transcript + self.current_phrase