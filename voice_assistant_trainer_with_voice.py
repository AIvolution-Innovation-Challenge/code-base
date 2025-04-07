import os
import time
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
from faster_whisper import WhisperModel
import platform
import threading
import queue
import re
from groq import Groq
import soundfile as sf
from kokoro import KPipeline
import scenarios

# Variable setup
scenario = scenarios.customer_service_agent_support_scenario
MAX_DIALOGUES = 12
AI_VOICE = "af_heart"
EVALUATION_VOICE = "am_michael"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["GROQ_API_KEY"] = "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"

# ----------------------- Speech-to-Text Setup -----------------------
SAMPLE_RATE = 16000
THRESHOLD = 700
SILENCE_DURATION = 5
MAX_RECORD_TIME = 30
MAX_CHUNK_LENGTH = 100

recorded_chunks = []
silence_time = 0
recording_stopped = False
recording_started = False

def audio_callback(indata, frames, time_info, status):
    global recorded_chunks, silence_time, recording_stopped, recording_started
    chunk = indata.flatten()
    recorded_chunks.append(chunk)
    amplitude = np.abs(chunk).mean()

    if not recording_started:
        if amplitude >= THRESHOLD:
            recording_started = True
            silence_time = 0
    else:
        if amplitude < THRESHOLD:
            silence_time += frames / SAMPLE_RATE
        else:
            silence_time = 0

    if recording_started and silence_time >= SILENCE_DURATION:
        recording_stopped = True
        raise sd.CallbackStop

def record_audio(filename="user_input.wav"):
    global recorded_chunks, silence_time, recording_stopped, recording_started
    recorded_chunks = []
    silence_time = 0
    recording_stopped = False
    recording_started = False

    print("🎙️ Recording... Speak now.")
    start_time = time.time()

    with sd.InputStream(callback=audio_callback, samplerate=SAMPLE_RATE, channels=1, dtype='int16'):
        while not recording_stopped and (time.time() - start_time < MAX_RECORD_TIME):
            sd.sleep(50)

    audio_data = np.concatenate(recorded_chunks)
    wavfile.write(filename, SAMPLE_RATE, audio_data)
    print(f"✅ Audio saved to {filename}")
    return filename

# ----------------------- Faster-Whisper Transcription -----------------------
whisper_model = WhisperModel("base", device="cpu", compute_type="float32")

def transcribe_audio(filename, language="en"):
    segments, info = whisper_model.transcribe(filename, beam_size=5, language=language)
    return " ".join([segment.text for segment in segments])

# ----------------------- TTS Setup -----------------------
pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M') # lang_code='a' stands for American English https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md

def play_audio(file_path):
    system = platform.system()
    if system == "Darwin":
        os.system(f"afplay {file_path}")
    elif system == "Linux":
        os.system(f"mpg123 {file_path}")
    elif system == "Windows":
        os.system(f"start {file_path}")
    else:
        print("Unsupported OS")

def process_audio(chunks, audio_queue, voice):
    for index, chunk in enumerate(chunks):
        generator = pipeline(chunk, voice=voice, speed=1.2)
        for _, _, audio in generator:
            audio_filename = f"assistant_response_{index}.wav"
            sf.write(audio_filename, audio, 24000)
        audio_queue.put(audio_filename)
    audio_queue.put(None)

def play_audio_worker(audio_queue):
    while True:
        audio_file = audio_queue.get()
        if audio_file is None:
            break
        play_audio(audio_file)
        if os.path.exists(audio_file):
            os.remove(audio_file)
        audio_queue.task_done()

def chunk_text_by_sentences(text, max_length=100):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
        if len(potential_chunk) <= max_length:
            current_chunk = potential_chunk
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def tts_threaded_playback(text, voice, max_chunk_length):
    chunks = chunk_text_by_sentences(text, max_length=max_chunk_length)
    audio_queue = queue.Queue()
    processor_thread = threading.Thread(target=process_audio, args=(chunks, audio_queue, voice))
    player_thread = threading.Thread(target=play_audio_worker, args=(audio_queue,))
    processor_thread.start()
    player_thread.start()
    processor_thread.join()
    player_thread.join()

# ----------------------- LLM Setup -----------------------
client = Groq(api_key=os.environ["GROQ_API_KEY"])

def get_ai_response(message, messages_history, system_prompt):
    messages = [{"role": "system", "content": system_prompt}] + messages_history + [{"role": "user", "content": message}]
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

def evaluate_conversation(messages_history, scenario):
    transcript = ""
    for msg in messages_history:
        if msg["role"] == "user":
            transcript += f"{scenario['persona_user']}: {msg['content']}\n"
        elif msg["role"] == "assistant":
            transcript += f"{scenario['persona_ai']}: {msg['content']}\n"

    evaluation_prompt = f"""
You are evaluating a [{scenario['conversation_type']}] conversation between a [{scenario['persona_ai']}] and a [{scenario['persona_user']}]. The conversation transcript is provided below:

{transcript}

Please evaluate the [{scenario['persona_user']}]’s performance using the following criteria:
{scenario['evaluation_criteria']}

Please keep your evaluation succinct as you are delivering this over speech.
    """

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": evaluation_prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

# ----------------------- Main Loop -----------------------
def voice_conversation(scenario, max_dialogues=MAX_DIALOGUES): 
    system_prompt = scenario["system_prompt"]
    messages_history = []
    dialogue_count = 0

    while dialogue_count < max_dialogues:
        audio_file = record_audio("user_input.wav")
        user_text = transcribe_audio(audio_file)
        print("You said:", user_text)

        ai_response = get_ai_response(user_text, messages_history, system_prompt)
        print(f"{scenario['persona_ai']}:", ai_response)

        messages_history.extend([
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": ai_response}
        ])

        tts_threaded_playback(ai_response, voice=AI_VOICE, max_chunk_length=MAX_CHUNK_LENGTH)

        os.remove(audio_file)
        dialogue_count += 1
        print("\n--------------------------------\n")

    print("Conversation ended after {} dialogue rounds.".format(dialogue_count))
    print("\nEvaluating conversation performance...")
    evaluation = evaluate_conversation(messages_history, scenario)
    print("Evaluation:\n", evaluation)
    tts_threaded_playback(evaluation, voice=EVALUATION_VOICE, max_chunk_length=MAX_CHUNK_LENGTH)

if __name__ == "__main__":
    voice_conversation(scenario)