import os
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from utils.audio_processor import process_audio_file
import tempfile
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.urandom(24)

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

@app.route('/upload', methods=['POST'])
def upload_file():
    temp_input = None
    temp_output = None
    
    try:
        # Input file validation
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only MP3 and WAV files are supported'}), 400

        # Create secure filenames
        filename = secure_filename(file.filename)
        output_filename = Path(filename).stem + '.mp3'
        temp_input = os.path.join(app.config['UPLOAD_FOLDER'], f"input_{filename}")
        temp_output = os.path.join(app.config['UPLOAD_FOLDER'], f"processed_{output_filename}")
        
        # Save input file
        file.save(temp_input)
        if not os.path.exists(temp_input):
            raise Exception("Failed to save uploaded file")
        
        # Process the audio file
        process_audio_file(temp_input, temp_output)
        
        # Verify output file exists
        if not os.path.exists(temp_output):
            raise Exception("Audio processing failed - output file not created")
            
        # Set download filename
        download_name = f"ACX_processed_{output_filename}"
        
        # Send the processed file with proper headers
        response = send_file(
            temp_output,
            as_attachment=True,
            download_name=download_name,
            mimetype='audio/mpeg'
        )
        
        # Add Content-Disposition header
        response.headers['Content-Disposition'] = f'attachment; filename="{download_name}"'
        response.headers['Content-Type'] = 'audio/mpeg'
        
        return response
    
    except FileNotFoundError as e:
        return jsonify({'error': 'File not found during processing'}), 404
    except PermissionError as e:
        return jsonify({'error': 'Permission denied while accessing files'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Only cleanup after response is sent
        try:
            if temp_input and os.path.exists(temp_input):
                os.remove(temp_input)
            if temp_output and os.path.exists(temp_output):
                os.remove(temp_output)
        except Exception as e:
            app.logger.error(f"Error during cleanup: {str(e)}")
