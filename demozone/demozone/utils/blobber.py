import os
import time
import logging
import threading
import whisperx
import torch
from datetime import datetime
from azure.storage.blob import BlobClient, ContentSettings
import base64
from .sendtoapi import send_to_api  # Removed send_image_url_to_api

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Azure Blob Storage settings
STORAGE_CONTAINER_SAS_URL = "https://daytranscriber.blob.core.windows.net/screenshotsimages?sp=racwdl&st=2024-08-21T06:15:34Z&se=2024-08-28T14:15:34Z&sv=2022-11-02&sr=c&sig=yLD7F9Ep0WxFMtzuMUHC31U%2BSVTSDuZJ8D6OrW1HFaY%3D"

# WhisperX and Hugging Face settings
HF_TOKEN = "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"
DEVICE = "cpu"
COMPUTE_TYPE = "float32"

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def upload_to_blob_storage(local_file_path):
    try:
        blob_name = os.path.basename(local_file_path)
        if not blob_name.lower().endswith('.png'):
            blob_name += '.png'
        
        logging.info(f"Attempting to upload blob: {blob_name}")
        
        sas_parts = STORAGE_CONTAINER_SAS_URL.split('?')
        blob_url = f"{sas_parts[0]}/{blob_name}?{sas_parts[1]}"
        
        logging.info(f"Constructed blob URL: {blob_url}")
        
        blob_client = BlobClient.from_blob_url(blob_url)

        with open(local_file_path, "rb") as data:
            logging.info(f"Uploading file: {local_file_path}")
            blob_client.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type="image/png"))

        logging.info(f"Image uploaded to Azure Blob Storage: {blob_client.url}")
        return blob_client.url
    except Exception as e:
        logging.error(f"An error occurred while uploading to Blob storage: {str(e)}")
        logging.error(f"Attempted blob URL: {blob_url}")
    return None

def save_urls_to_file(session_folder, image_urls):
    url_file_path = os.path.join(session_folder, "image_urls.txt")
    
    # Ensure the directory exists
    os.makedirs(session_folder, exist_ok=True)
    
    with open(url_file_path, "a") as url_file:
        for url in image_urls:
            url_file.write(f"{url}\n")
    logging.info(f"URLs saved to {url_file_path}")

def transcribe_and_diarize(audio_file, max_speakers):
    logging.info("Starting transcription and diarization with WhisperX...")
    logging.info(f"Audio file path: {audio_file}")

    try:
        model = whisperx.load_model("large-v2", DEVICE, compute_type=COMPUTE_TYPE)
        audio = whisperx.load_audio(audio_file)
        result = model.transcribe(audio, batch_size=1, language="en")
        logging.info("Transcription completed.")

        model_a, metadata = whisperx.load_align_model(language_code="en", device=DEVICE)
        result = whisperx.align(result["segments"], model_a, metadata, audio, DEVICE, return_char_alignments=False)
        logging.info("Alignment completed.")

        diarize_model = whisperx.DiarizationPipeline(use_auth_token=HF_TOKEN, device=DEVICE)
        diarize_segments = diarize_model(audio_file, min_speakers=1, max_speakers=max_speakers)
        result = whisperx.assign_word_speakers(diarize_segments, result)
        logging.info("Diarization completed.")

        return result
    except Exception as e:
        logging.error(f"Error during transcription and diarization: {e}")
        raise

def process_audio_file(filepath, session_id, max_speakers=2, callback=None):
    logging.info(f"Processing audio file: {filepath}")
    try:
        # Check if the file has already been processed
        transcript_filename = f"transcript_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        transcript_path = os.path.join(os.path.dirname(filepath), transcript_filename)
        
        if os.path.exists(transcript_path):
            logging.info(f"Transcript already exists: {transcript_path}")
            return

        # Add logging to verify the file path
        logging.info(f"File path: {filepath}")
        logging.info(f"File extension: {os.path.splitext(filepath)[1]}")

        result = transcribe_and_diarize(filepath, max_speakers)
        
        transcript = "\n".join([segment["text"] for segment in result["segments"]])
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(transcript_path), exist_ok=True)
        
        with open(transcript_path, "w") as transcript_file:
            transcript_file.write(transcript)
        
        logging.info(f"Transcript saved to {transcript_path}")
        
        image_urls_file = os.path.join("processed_images", "image_urls.txt")
        
        if transcript.strip():
            send_to_api(transcript_path, "1723700417755x586654339331260400", image_urls_file)
        else:
            logging.error("Transcript is empty, not sending to API.")
        
        if callback:
            callback(session_id, transcript, [])
    except Exception as e:
        logging.error(f"Error processing audio file: {e}")

def process_image_file(filepath, session_id, callback=None):
    try:
        if not filepath or not os.path.exists(filepath):
            logging.error(f"Invalid filepath: {filepath}")
            return

        base64_image = encode_image_to_base64(filepath)
        image_url = upload_to_blob_storage(filepath)
        if image_url:
            save_urls_to_file("processed_images", [image_url])
            image_urls_file = os.path.join("processed_images", "image_urls.txt")
            send_to_api(image_urls_file, "1723700417755x586654339331260400")
            
            if callback:
                callback(session_id, image_url)
        else:
            logging.error(f"Failed to upload image to blob storage: {filepath}")
    except Exception as e:
        logging.error(f"Error processing image file: {e}", exc_info=True)

def get_image_urls(session_folder):
    url_file_path = os.path.join(session_folder, "image_urls.txt")
    if os.path.exists(url_file_path):
        with open(url_file_path, "r") as url_file:
            return [line.strip() for line in url_file if line.strip()]
    return []

# Example usage (if you want to test the module directly)
if __name__ == "__main__":
    # Test image processing
    test_image_path = "path/to/test/image.png"
    session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    process_image_file(test_image_path, session_id)
    
    # Test audio processing
    test_audio_path = "path/to/test/audio.wav"
    process_audio_file(test_audio_path, session_id)
    
    # Test retrieving URLs
    urls = get_image_urls("processed_images")
    print("Retrieved URLs:")
    for url in urls:
        print(url)