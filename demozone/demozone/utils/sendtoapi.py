import requests
import base64
import os
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def file_to_base64(file_path):
    with open(file_path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

def get_image_urls(image_urls_file):
    if os.path.exists(image_urls_file):
        with open(image_urls_file, 'r') as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    return []

def send_to_api(transcript_path, bot_id, image_urls_file):
    url = "https://api.ohanapay.app/api/1.1/wf/add_from_transcriber"
    
    transcript_base64 = file_to_base64(transcript_path) if transcript_path else ""
    image_urls = get_image_urls(image_urls_file)
    
    data = {
        'bot_id': bot_id,  # Ensure the key is 'bot_id'
        'transcription_file': transcript_base64,
        'image_urls': image_urls
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        logging.info("Data sent to API successfully")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending data to API: {e}")
        if hasattr(e, 'response'):
            logging.error(f"Response content: {e.response.text}")

def send_image_url_to_api(image_url, bot_id):
    url = "https://api.ohanapay.app/api/1.1/wf/add_from_transcriber"
    
    data = {
        'bot_id': bot_id,  # Ensure the key is 'bot_id'
        'transcription_file': "",
        'image_urls': [image_url]
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        logging.info("Image URL sent to API successfully")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending image URL to API: {e}")
        if hasattr(e, 'response'):
            logging.error(f"Response content: {e.response.text}")

if __name__ == "__main__":
    logging.warning("This script is not meant to be run directly. It should be imported and used by blobber.py")