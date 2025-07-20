import warnings
import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
from transformers import MarianMTModel, MarianTokenizer
from gtts import gTTS
import tempfile
import os
import pyaudio
import wave
import threading
from pydub import AudioSegment
from pydub.playback import play

# Make sure ffmpeg is available
AudioSegment.converter = "ffmpeg"
warnings.filterwarnings("ignore", category=FutureWarning)


# Define models for different language pairs
models = {
    'en-es': 'Helsinki-NLP/opus-mt-en-es',  # English to Spanish
    'es-en': 'Helsinki-NLP/opus-mt-es-en',  # Spanish to English
    'en-fr': 'Helsinki-NLP/opus-mt-en-fr',  # English to French
    'fr-en': 'Helsinki-NLP/opus-mt-fr-en',  # French to English
    'en-de': 'Helsinki-NLP/opus-mt-en-de',  # English to German
    'de-en': 'Helsinki-NLP/opus-mt-de-en',  # German to English
    'en-zh': 'Helsinki-NLP/opus-mt-en-zh',  # English to Chinese
    'zh-en': 'Helsinki-NLP/opus-mt-zh-en',  # Chinese to English
}

# Language names mapping
language_names = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'zh': 'Chinese',
}

# Reverse mapping for language codes
reverse_language_names = {v: k for k, v in language_names.items()}

# Translation pairs
translation_pairs = [
    'English to Spanish',
    'Spanish to English',
    'English to French',
    'French to English',
    'English to German',
    'German to English',
    'English to Chinese',
    'Chinese to English',
]

recording_thread = None
stop_event = threading.Event()


def load_model_and_tokenizer(language_pair):
    """Load the model and tokenizer for the given language pair."""
    model_name = models[language_pair]
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    return tokenizer, model


def translate_text(text, tokenizer, model):
    """Translate text using the given tokenizer and model."""
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    translated_tokens = model.generate(**inputs, max_new_tokens=512)
    translated_text = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
    return translated_text


def text_to_speech(text, lang='es'):
    """Convert text to speech and save it to a temporary file."""
    tts = gTTS(text=text, lang=lang)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name


def record_audio(filename, duration=30):
    """Record audio from the microphone and save it to a file."""
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 1
    rate = 48000  # Higher sample rate for better quality

    p = pyaudio.PyAudio()

    stream = p.open(format=sample_format, channels=channels, rate=rate, frames_per_buffer=chunk, input=True)
    frames = []

    stop_event.clear()  # Clear the stop event

    print("Recording...")

    while True:
        if stop_event.is_set():
            break
        data = stream.read(chunk)
        frames.append(data)

    print("Finished recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()


def play_audio(file_path):
    """Play the audio file with increased volume."""
    try:
        audio = AudioSegment.from_mp3(file_path)
        # Increase volume by 10 dB
        audio = audio + 10
        play(audio)
    except Exception as e:
        print(f"Error playing audio: {e}")


def start_recording():
    """Start recording audio."""
    global recording_thread
    stop_event.clear()
    status_label.config(text="Recording...")
    recording_thread = threading.Thread(target=record_audio, args=("input_audio.wav", 30))
    recording_thread.start()
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)


def stop_recording():
    """Stop recording audio."""
    stop_event.set()  # Signal the recording thread to stop
    recording_thread.join()  # Wait for the recording thread to finish
    status_label.config(text="Recording stopped.")
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    process_translation()


def process_translation():
    """Process the translation based on user input."""
    if not os.path.exists("input_audio.wav"):
        result_label.config(text="Error: No audio file found.")
        return

    translation_pair = translation_combobox.get()
    if translation_pair not in translation_pairs:
        result_label.config(text="Error: Invalid translation pair.")
        return

    try:
        input_lang, output_lang = translation_pair.split(' to ')
        # Find the corresponding code for the language pair
        language_pair = f'{reverse_language_names[input_lang]}-{reverse_language_names[output_lang]}'
    except KeyError as e:
        result_label.config(text=f"Error: Language code not found for {e}.")
        return

    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile("input_audio.wav")

    with audio_file as source:
        audio_data = recognizer.record(source)

    try:
        transcription = recognizer.recognize_google(audio_data)
        tokenizer, model = load_model_and_tokenizer(language_pair)

        translated_text = translate_text(transcription, tokenizer, model)
        global audio_path
        audio_path = text_to_speech(translated_text, lang=reverse_language_names[output_lang])

        # Clear and update the translated text box with the result
        translated_text_box.config(state=tk.NORMAL)  # Enable editing to update content
        translated_text_box.delete(1.0, tk.END)  # Clear existing text
        translated_text_box.insert(tk.END, f"Translated Text ({translation_pair}):\n\n{translated_text}")
        translated_text_box.config(state=tk.DISABLED)  # Disable editing

        # Center-align the text in the text box
        translated_text_box.tag_configure('center', justify='center')
        translated_text_box.tag_add('center', 1.0, tk.END)

        result_label.config(text="")
        play_button.config(state=tk.NORMAL)

    except sr.RequestError:
        result_label.config(text="Error: Speech recognition API unavailable.")
    except sr.UnknownValueError:
        result_label.config(text="Error: Unable to recognize speech.")
    except Exception as e:
        result_label.config(text=f"Error: {str(e)}")


def play_translation():
    """Play the translated audio."""
    if 'audio_path' in globals():
        play_audio(audio_path)


def reset():
    """Reset the output and UI elements."""
    result_label.config(text="")
    status_label.config(text="")
    play_button.config(state=tk.DISABLED)
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    translation_combobox.set('English to Spanish')

    # Clear the translated text box
    translated_text_box.config(state=tk.NORMAL)  # Enable editing to clear content
    translated_text_box.delete(1.0, tk.END)
    translated_text_box.config(state=tk.DISABLED)  # Disable editing


# GUI setup
root = tk.Tk()
root.title("Real-Time Language Translation")

root.configure(bg="#f0f0f0")

tk.Label(root, text="Select Translation:", bg="#f0f0f0", font=("Arial", 14)).grid(row=0, column=0, columnspan=4,
                                                                                  pady=10)

translation_combobox = ttk.Combobox(root, values=translation_pairs, width=30, font=("Arial", 12))
translation_combobox.set('English to Spanish')
translation_combobox.grid(row=1, column=0, columnspan=4, pady=5)
translation_combobox.config(state='readonly')  # Make combobox read-only but selectable

start_button = tk.Button(root, text="Start Recording", command=start_recording, bg="#4CAF50", fg="white",
                         font=("Arial", 12))
start_button.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

stop_button = tk.Button(root, text="Stop Recording", command=stop_recording, state=tk.DISABLED, bg="#F44336",
                        fg="white", font=("Arial", 12))
stop_button.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

play_button = tk.Button(root, text="Play Translation", command=play_translation, state=tk.DISABLED, bg="#2196F3",
                        fg="white", font=("Arial", 12))
play_button.grid(row=2, column=2, padx=5, pady=5, sticky="ew")

reset_button = tk.Button(root, text="Reset", command=reset, bg="#FFC107", fg="white", font=("Arial", 12))
reset_button.grid(row=2, column=3, padx=5, pady=5, sticky="ew")

result_label = tk.Label(root, text="", bg="#f0f0f0", font=("Arial", 12))
result_label.grid(row=3, column=0, columnspan=4, pady=10)

status_label = tk.Label(root, text="", bg="#f0f0f0", font=("Arial", 12))
status_label.grid(row=4, column=0, columnspan=4, pady=10)

translated_text_box = tk.Text(root, height=10, width=50, wrap=tk.WORD, font=("Arial", 12, "bold"), bg="#ffffff",
                              padx=10, pady=10, state=tk.DISABLED)
translated_text_box.grid(row=5, column=0, columnspan=4, padx=10, pady=10)

root.mainloop()
