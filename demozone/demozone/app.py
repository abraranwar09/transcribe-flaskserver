import os
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_uploads import UploadSet, configure_uploads, AUDIO, IMAGES
from werkzeug.utils import secure_filename
import logging
from threading import Thread
from demozone.utils.file_watcher import start_watching
from demozone.utils.blobber import process_image_file, process_audio_file

# Initialize Flask app and Flask-RESTful API
app = Flask(__name__)
api = Api(app)

# Configure the upload sets
audio_files = UploadSet('audio', AUDIO)
image_files = UploadSet('images', IMAGES)

app.config['UPLOADED_AUDIO_DEST'] = 'uploads/audio'
app.config['UPLOADED_IMAGES_DEST'] = 'uploads/images'

configure_uploads(app, (audio_files, image_files))

# Ensure the upload directories exist
os.makedirs(app.config['UPLOADED_AUDIO_DEST'], exist_ok=True)
os.makedirs(app.config['UPLOADED_IMAGES_DEST'], exist_ok=True)

# Define the AudioUpload resource
class AudioUpload(Resource):
    def post(self):
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        session_id = request.form.get('session_id')
        max_speakers = request.form.get('max_speakers', default=2, type=int)
        
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if file and audio_files.file_allowed(file, file.filename):
            filename = audio_files.save(file)
            return jsonify({"message": "File uploaded successfully", "filename": filename})
        else:
            return jsonify({"error": "File type not allowed"})

# Define the ImageUpload resource
class ImageUpload(Resource):
    def post(self):
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        session_id = request.form.get('session_id')
        
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if file and image_files.file_allowed(file, file.filename):
            filename = image_files.save(file)
            return jsonify({"message": "File uploaded successfully", "filename": filename})
        else:
            return jsonify({"error": "File type not allowed"})

# Add resources to the API
api.add_resource(AudioUpload, '/upload/audio')
api.add_resource(ImageUpload, '/upload/image')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to start the file watchers
def start_file_watchers():
    directories_to_watch = [app.config['UPLOADED_IMAGES_DEST'], app.config['UPLOADED_AUDIO_DEST']]
    process_functions = [process_image_file, process_audio_file]
    session_id = "your_session_id"  # Replace with actual session ID logic
    max_speakers = 2  # Default value, can be changed as needed

    start_watching(directories_to_watch, process_functions, session_id, max_speakers)

# Start the file watchers in a separate thread
watcher_thread = Thread(target=start_file_watchers)
watcher_thread.daemon = True
watcher_thread.start()

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)