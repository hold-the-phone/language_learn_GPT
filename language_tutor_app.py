import numpy as np
import pandas as pd
import openai
import requests
import json
import time
from pathlib import Path
import threading
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tkinter as tk

import openai_utils

language_lookup = {'Italian':'it', 'French': 'fr', 'Spanish': 'es'}

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.frames = []
        self.fs = 44100  # Sample rate
        self.channels = 1  # Adjust as per your microphone's capability

    def callback(self, indata, frames, time, status):
        if self.recording:
            self.frames.append(indata.copy())

    def start_recording(self):
        self.frames = []
        self.recording = True
        with sd.InputStream(samplerate=self.fs, channels=self.channels, callback=self.callback):
            while self.recording:
                sd.sleep(1000)

    def stop_recording(self, filename):
        self.recording = False
        sd.stop()
        if self.frames:
            data = np.concatenate(self.frames, axis=0)
            wav.write(filename, self.fs, data)


def start_recording_thread():
    global recorder
    
    recording_thread = threading.Thread(target=recorder.start_recording)
    recording_thread.start()

def stop_recording_and_transcribe():
    global recorder
    global thread
    
    recorder.stop_recording("test.mp3")
    transcript = openai_utils.openai_transcribe_speech(client, './test.mp3', language_lookup[thread_language])
    
    label_transcript = openai_utils.run_italian_echo(client, transcript,thread_language)
    label.config(text=label_transcript)
    label_raw.config(text=transcript)
    
    mock_tutor_response = openai_utils.run_italian_tutor(client, transcript, thread, thread_language)
    
    tutor_label.config(text= "\n".join(mock_tutor_response))
    
    # this is not working correctly
    openai_utils.open_ai_text_to_speech(client, "response_file.flac", mock_tutor_response[0][6:], 0.8)
    openai_utils.play_sound_file("response_file.flac")
    
def replay_tutor_response():
    openai_utils.play_sound_file("response_file.flac")
    
def confirm_inputs():
    global client
    global thread
    global thread_language
    thread_language = language_variable.get()
    
    try:
        inputValue=textBox.get("1.0","end-1c")
        client = openai.OpenAI(api_key=inputValue)
        
        openai_utils.create_assistants(client,thread_language)

        thread = client.beta.threads.create()
        tutor_label.config(text= "Credentials validated by OpenAI")
        label_raw.config(text="")
        label.config(text="")
        
    except Exception as e:
        tutor_label.config(text= "Credentials were not correctly validated by OpenAI")
    

if __name__ == '__main__':
    recorder = AudioRecorder()

    # Tkinter GUI setup
    root = tk.Tk()
    root.title("Voice Recorder")
    root.geometry("700x700")
    language_variable = tk.StringVar(root)
    language_variable.set("Italian")

    replay_button = tk.Button(root, text="Play Response", command=replay_tutor_response)
    replay_button.pack(side=tk.BOTTOM, padx=10, pady=10)

    stop_button = tk.Button(root, text="Stop Recording", command=stop_recording_and_transcribe)
    stop_button.pack(side=tk.BOTTOM, padx=10, pady=10)

    start_button = tk.Button(root, text="Start Recording", command=start_recording_thread)
    start_button.pack(side=tk.BOTTOM, padx=10, pady=10)

    dropdown_language = tk.OptionMenu(root, language_variable, "Italian", "Spanish", "French")
    dropdown_language.pack()

    title_input_box = tk.Label(root, text="OpenAI Credentials:")
    title_input_box.pack(anchor='center', pady=(10, 0))

    textBox=tk.Text(root, height=2, width=10)
    textBox.pack()

    buttonCommit=tk.Button(root, height=1, width=10, text="Confirm Inputs", 
                        command=lambda: confirm_inputs())
    buttonCommit.pack()


    # Title and raw speech label
    title_label_raw = tk.Label(root, text="Your raw input:")
    title_label_raw.pack(anchor='center', pady=(10, 0))

    label_raw = tk.Label(root, text="", wraplength=500, borderwidth=2, relief="groove")
    label_raw.pack(anchor='center', padx=20, pady=10)

    # Title and echo display label
    title_label = tk.Label(root, text="Your Input with Grammatical Corrections:")
    title_label.pack(anchor='center', pady=(10, 0))

    label = tk.Label(root, text="", wraplength=500, borderwidth=2, relief="groove")
    label.pack(anchor='center', padx=20, pady=10)

    # Title and response display label
    tutor_title_label = tk.Label(root, text="Tutor Response:")
    tutor_title_label.pack(anchor='center', pady=(10, 0))

    tutor_label = tk.Label(root, text="", wraplength=500, borderwidth=2, relief="groove")
    tutor_label.pack(anchor='center', padx=20, pady=10)

    root.mainloop()




