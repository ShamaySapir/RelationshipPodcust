# imports
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import requests 
import re

# Load environment variables from .env file
load_dotenv(override=True)
api_key = os.getenv('AZURE_OPENAI_API_KEY')
endpoint = os.getenv('ENDPOINT')
version = os.getenv('VERSION')
deployment = os.getenv('DEPLOYMENT_4o')
region = os.getenv('AZURE_TTS_REGION')
key = os.getenv('AZURE_TTS_API_KEY')

client = AzureOpenAI(
    azure_endpoint=endpoint, 
    api_key=api_key,
    api_version=version
)

PROMPTS = {
    "translate_system": """You are a helpful assistant that gets text in Hebrew 
    and translates it to English and can do requested changes to the text.""",
    "transalte_client": "Translate the following text to English and according to the text, add the line Week X Day Y",
    "summarize_system": "You are a helpful assistant. For each Week and Day, summarize the key information briefly.",
    "summarize_title": """Please summarize the following content into a single line
    to be used as a podcast episode title,
        in the format: Week X: Day Y – NAME (Z).
        NAME is the episode title you create, X is the Week number, Y is the day number""",
    "summary": f"Please summarize the following content into a single line \
    to be used as a podcast episode summary."
}


# Set the endpoint and headers
endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
headers = {
    "Ocp-Apim-Subscription-Key": key,
    "Content-Type": "application/ssml+xml",
    "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
    "User-Agent": "myTTSApp"
}
   

def generic_response(user_prompt, system_prompt, model=deployment):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
    )
    return response.choices[0].message.content.strip()


def translate_week_episodes(text):
    system_prompt = PROMPTS["translate_system"]
    user_prompt = PROMPTS["transalte_client"]
    user_prompt += "\n\n" + text
    response = generic_response(user_prompt, system_prompt)
    return response


def divide_episodes(text):
    pattern = r'(Week\s+\d+\s+Day\s+\d+)'
    matches = list(re.finditer(pattern, text))

    days = []

    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        title = matches[i].group(1).strip()
        content = text[start:end].strip()

        days.append((title, content))

    return days


def user_prompt_for_title(day_text, z):
    user_prompt = PROMPTS["summarize_title"]
    user_prompt +=  f" and Z is the value {z}\n"
    user_prompt += day_text
    return user_prompt

def user_prompt_for_summary(day_text):
    user_prompt = PROMPTS["summary"]
    user_prompt += day_text
    return user_prompt

def summarize_week_episodes(days, podcast_episode):
    results = []
    # Loop through the days and summarize each one
    for title, day_text in days:
        print(f"Processing {title}...")
        
        try:
            day_title = generic_response(
                user_prompt_for_title(day_text, podcast_episode),
                PROMPTS["summarize_system"]
            )
            summary = generic_response(
                user_prompt_for_summary(day_text),
                PROMPTS["summarize_system"]
            )
        except Exception as e:
            print(f"Error with {title}: {e}")
            day_title = None
            summary = None

        results.append({
            "day": day_title,
            "response": summary
        })
        podcast_episode += 1
        print(f"Received: {day_title}:\n{summary}")
    return results


def create_ssml(text, voice="en-US-JennyNeural"):
    ssml = f"""
    <speak version='1.0' xml:lang='en-US'>
    <voice name='{voice}'>
        {text}
    </voice>
    </speak>
    """
    return ssml

def create_audio_file(ssml, filename, endpoint, headers):
    # Make the POST request
    response = requests.post(endpoint, headers=headers, data=ssml.encode('utf-8'))

    # Save to file
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Audio saved as {filename}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def generate_audio_files(days, voice="en-US-AndrewNeural", output_folder="audio"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    audio_files = []

    for title, day_text in days:
        print(f"Processing {title}...")
        
        try:
            ssml = create_ssml(day_text, voice)
            safe_title = title.replace(" ", "_").replace(":", "_")
            filename = os.path.join(output_folder, f"{safe_title}.mp3")
            create_audio_file(ssml, filename, endpoint, headers)
            audio_files.append(filename)
        except Exception as e:
            print(f"⚠️ Error with {title}: {e}")
    
    return audio_files



  