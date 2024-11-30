import subprocess
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_audio_file(input_path):
    """
    Validate the input audio file format and properties
    """
    try:
        # Get file info using FFmpeg
        cmd = ['ffmpeg', '-i', input_path]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
        output = result.stderr.lower()
        
        logger.info(f"Validating audio file: {input_path}")
        
        # Check if it's an audio file
        if 'audio:' not in output:
            logger.error(f"Invalid audio file: {input_path}")
            raise Exception("Not a valid audio file")
            
        # Get file extension
        ext = Path(input_path).suffix.lower()
        if ext not in ['.mp3', '.wav']:
            logger.error(f"Unsupported file format: {ext}")
            raise Exception("Unsupported file format. Only MP3 and WAV files are supported")
        
        # Log audio file properties
        logger.info(f"Audio file validation successful: {input_path}")
        logger.info(f"File properties: {output}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error validating audio file: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def process_audio_file(input_path, output_path):
    """
    Process audio file according to ACX standards using FFmpeg
    """
    try:
        # Validate input file
        validate_audio_file(input_path)
        logger.info(f"Starting audio processing: {input_path}")
        
        # Build filter chain in proper order
        filter_chain = [
            'aresample=44100',  # Resample to 44.1kHz first
            'aformat=sample_fmts=fltp',  # Convert to float format for better processing
            'highpass=f=80',  # High-pass filter at 80Hz
            'acompressor=threshold=-18dB:ratio=2:attack=20:release=1000',  # Compression
            'loudnorm=I=-20:TP=-3:LRA=11:measured_I=-32',  # RMS normalization
            'volume=volume=2.1',  # Volume adjustment
            'alimiter=level=1.0:limit=-3dB:attack=5:release=50',  # Final limiter
            'adelay=2000|2000',  # Add 2s silence at start
            'apad=pad_dur=2'     # Add 2s silence at end
        ]
        
        # FFmpeg command with optimized settings
        ffmpeg_command = [
            'ffmpeg', '-y',  # Force overwrite output file
            '-i', input_path,
            '-af', ','.join(filter_chain),
            '-ac', '1',          # Mono output
            '-codec:a', 'libmp3lame',
            '-b:a', '192k',      # Force 192kbps bitrate
            '-f', 'mp3',         # Force MP3 format
            output_path
        ]
        
        logger.info("Executing FFmpeg command with filter chain")
        logger.debug(f"FFmpeg command: {' '.join(ffmpeg_command)}")
        
        # Execute FFmpeg command with full output capture
        process = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        
        if process.returncode != 0:
            error_msg = f"FFmpeg processing failed: {process.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Verify output file
        if not os.path.exists(output_path):
            error_msg = "Output file was not created"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        logger.info(f"Audio processing completed successfully: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg error: {e.stderr if hasattr(e, 'stderr') else str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Processing error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
