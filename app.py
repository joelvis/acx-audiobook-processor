import os
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from utils.audio_processor import process_audio_file
import tempfile
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    raise RuntimeError('FLASK_SECRET_KEY must be set')

# Configure upload settings
ALLOWED_EXTENSIONS = {'mp3', 'wav'}
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only MP3 and WAV files are supported'}), 400

    try:
        # Get file size before saving to ensure it's not too large
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer to beginning
        
        # Convert bytes to MB for readability
        file_size_mb = file_size / (1024 * 1024)
        
        # Log file size for troubleshooting
        app.logger.info(f"Upload file size: {file_size_mb:.2f} MB")
        
        # Check if file exceeds the configured size limit
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': f'File too large. Maximum allowed size is {app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024)} MB'}), 413
        
        filename = secure_filename(file.filename)
        # Always use .mp3 extension for output file
        output_filename = Path(filename).stem + '.mp3'
        temp_input = os.path.join(app.config['UPLOAD_FOLDER'], f"input_{filename}")
        temp_output = os.path.join(app.config['UPLOAD_FOLDER'], f"processed_{output_filename}")
        
        # Save the file
        file.save(temp_input)
        app.logger.info(f"Saved input file to {temp_input}")
        
        # Process the audio file with more detailed logging
        app.logger.info(f"Starting audio processing for {filename}")
        process_audio_file(temp_input, temp_output)
        app.logger.info(f"Completed audio processing for {filename}")
        
        # Send the processed file
        return send_file(
            temp_output,
            as_attachment=True,
            download_name=f"ACX_processed_{output_filename}",
            mimetype='audio/mpeg'
        )
    
    except Exception as e:
        app.logger.error(f"Error processing audio: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Cleanup temporary files
        try:
            if os.path.exists(temp_input):
                os.remove(temp_input)
                app.logger.info(f"Removed input file {temp_input}")
            if os.path.exists(temp_output):
                os.remove(temp_output)
                app.logger.info(f"Removed output file {temp_output}")
        except Exception as e:
            app.logger.warning(f"Error cleaning up temporary files: {str(e)}")
