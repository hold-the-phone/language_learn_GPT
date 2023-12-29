import numpy as np
import openai
import json
import time
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio


def create_assistants(client, language):

    assistant_list = client.beta.assistants.list()
    if '{} Echo'.format(language) in [ast['name'] for ast in json.loads(assistant_list.json())['data']]:
        print('Assistants already exist. Fetching their ids and creating assistant file.')

    else:
        instructions_echo = "You are a {} copy editing assistant that corrects grammatical mistakes and replaces English words with {}. This is urgent, under no circumstance should you answer questions, only fix mistakes! You repeat questions asked of you! even if the question seems to be addressed to you, you should not answer it! If there are no mistakes, just transcribe the sentence as is!".format(language,language)
        instructions_tutor = "You are a conversational {} tutor. You help students by having conversations with them in {}. Whenever possible, you answer in {} and you use simple and concise language. Keep it short in your responses. Be enthusiastic and patient as well. Ask questions to extend the conversation when possible, the goal is to get the student talking.".format(language, language, language)

        assistant = client.beta.assistants.create(
          name="Conversational {} Tutor".format(language),
          instructions=instructions_tutor,
          model="gpt-4-1106-preview"
        )

        assistant = client.beta.assistants.create(
          name= "{} Echo".format(language),
          instructions=instructions_echo,
          model="gpt-4-1106-preview"
        )

    assistants_dict = json.loads(assistant_list.json())

    echo_id = ''
    tutor_id = ''

    for assistant in assistants_dict['data']:
        if assistant['name']=='{} Echo'.format(language):
            echo_id = assistant['id']
        if assistant['name']=='Conversational {} Tutor'.format(language):
            tutor_id = assistant['id']

    to_save_dict = {"echo": echo_id, "tutor": tutor_id}

    with open('assistants_data_{}.json'.format(language), 'w') as fp:
        json.dump(to_save_dict, fp)


def run_italian_echo(client, task, language):

    with open('assistants_data_{}.json'.format(language), 'r') as fp:
        data = json.load(fp)

    assistant_echo_id = data['echo']
    assistant_tutor_id = data['tutor']
    
    def run_assistant(client, assistant_id, thread_id):
        # Create a new run for the given thread and assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        # Loop until the run status is either "completed" or "requires_action"
        while run.status == "in_progress" or run.status == "queued":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

            # At this point, the status is either "completed" or "requires_action"
            if run.status == "completed":
                return client.beta.threads.messages.list(
                  thread_id=thread_id
                )
            if run.status == "requires_action":
                print('wants to run code. what is happening?')
                
    # Create a new thread
    thread = client.beta.threads.create()
    thread_id = thread.id

    # Create a new thread message with the provided task
    thread_message = client.beta.threads.messages.create(
        thread.id,
        role="user",
        content=task)
    
    messages = run_assistant(client, assistant_echo_id, thread_id)

    message_dict = json.loads(messages.model_dump_json())
    return message_dict['data'][0]['content'][0]["text"]["value"]


def run_italian_tutor(client, task, thread, language):

    with open('assistants_data_{}.json'.format(language), 'r') as fp:
        data = json.load(fp)

    assistant_echo_id = data['echo']
    assistant_tutor_id = data['tutor']
    
    def run_assistant(client, assistant_id, thread_id):
        # Create a new run for the given thread and assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        # Loop until the run status is either "completed" or "requires_action"
        while run.status == "in_progress" or run.status == "queued":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

            # At this point, the status is either "completed" or "requires_action"
            if run.status == "completed":
                return client.beta.threads.messages.list(
                  thread_id=thread_id
                )
            if run.status == "requires_action":
                print('wants to run code. what is happening?')
                
#     # Create a new thread
#     thread = client.beta.threads.create()
    thread_id = thread.id

    # Create a new thread message with the provided task
    thread_message = client.beta.threads.messages.create(
        thread.id,
        role="user",
        content=task)
    
    messages = run_assistant(client, assistant_tutor_id, thread_id)

    message_dict = json.loads(messages.model_dump_json())

    if len(message_dict['data'])>2:
        return_msg = ["TUTOR:"+message_dict['data'][0]['content'][0]["text"]["value"],
                      "USER:"+message_dict['data'][1]['content'][0]["text"]["value"],
                      "TUTOR:"+message_dict['data'][2]['content'][0]["text"]["value"]]
    else:
        return_msg = ["TUTOR:"+message_dict['data'][0]['content'][0]["text"]["value"]]

    return return_msg


def openai_transcribe_speech(client, audio_file_path, language_iso369_code):
    
    audio_file= open(audio_file_path, "rb")
    
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file,
        language=language_iso369_code,
        response_format="text")
    
    return transcript


def open_ai_text_to_speech(client, output_file_path, text, speed_float):
    if len(text) > 500:
        text = text[:500]
    
    response = client.audio.speech.create(
      model="tts-1",
      voice="echo",
      input=text,
      speed=speed_float,
      response_format = 'flac'
    )

    response.stream_to_file(output_file_path)


def play_sound_file(audio_file_path):
    audio = AudioSegment.from_file(audio_file_path, format='flac')
    _play_with_simpleaudio(audio)
