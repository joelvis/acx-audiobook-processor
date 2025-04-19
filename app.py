import os
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from utils.audio_processor import process_audio_file
import tempfile
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

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
        filename = secure_filename(file.filename)
        # Always use .mp3 extension for output file
        output_filename = Path(filename).stem + '.mp3'
        temp_input = os.path.join(app.config['UPLOAD_FOLDER'], f"input_{filename}")
        temp_output = os.path.join(app.config['UPLOAD_FOLDER'], f"processed_{output_filename}")
        
        file.save(temp_input)
        
        # Process the audio file
        process_audio_file(temp_input, temp_output)
        
        # Send the processed file
        return send_file(
            temp_output,
            as_attachment=True,
            download_name=f"ACX_processed_{output_filename}",
            mimetype='audio/mpeg'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Cleanup temporary files
        if os.path.exists(temp_input):
            os.remove(temp_input)
        if os.path.exists(temp_output):
            os.remove(temp_output)
