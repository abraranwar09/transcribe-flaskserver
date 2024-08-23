from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_reuploaded import UploadSet, configure_uploads, AUDIO, IMAGES
from werkzeug.utils import secure_filename  # Updated import
import os

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

class AudioUpload(Resource):
    def post(self):
        if 'file' not in request.files:
            return jsonify({"error": "No file part"})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No selected file"})
        
        if file and audio_files.file_allowed(file, file.filename):
            filename = audio_files.save(file)
            return jsonify({"message": "File uploaded successfully", "filename": filename})
        else:
            return jsonify({"error": "File type not allowed"})

class ImageUpload(Resource):
    def post(self):
        if 'file' not in request.files:
            return jsonify({"error": "No file part"})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No selected file"})
        
        if file and image_files.file_allowed(file, file.filename):
            filename = image_files.save(file)
            return jsonify({"message": "File uploaded successfully", "filename": filename})
        else:
            return jsonify({"error": "File type not allowed"})

api.add_resource(AudioUpload, '/upload/audio')
api.add_resource(ImageUpload, '/upload/image')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)