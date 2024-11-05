import subprocess
import os
from pathlib import Path

def validate_audio_file(input_path):
    """
    Validate the input audio file format and properties
    """
    try:
        # Get file info using FFmpeg
        cmd = ['ffmpeg', '-i', input_path]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
        output = result.stderr.lower()
        
        # Check if it's an audio file
        if 'audio:' not in output:
            raise Exception("Not a valid audio file")
            
        # Get file extension
        ext = Path(input_path).suffix.lower()
        if ext not in ['.mp3', '.wav']:
            raise Exception("Unsupported file format. Only MP3 and WAV files are supported")
            
        return True
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error validating audio file: {str(e)}")

def process_audio_file(input_path, output_path):
    """
    Process audio file according to ACX standards using FFmpeg
    """
    try:
        # Validate input file
        validate_audio_file(input_path)
        
        # FFmpeg command chain for ACX processing
        ffmpeg_command = [
            'ffmpeg', '-y',  # Force overwrite output file
            '-i', input_path,
            '-af',
            # Combine all audio filters in one chain
            'silenceremove=start_periods=1:start_duration=0.1:start_threshold=-60dB:detection=peak,'
            'silenceremove=stop_periods=1:stop_duration=0.1:stop_threshold=-60dB:detection=peak,'
            'adelay=2000|2000,'  # Add 2s silence at start
            'apad=pad_dur=2,'    # Add 2s silence at end
            'highpass=f=80,'     # High-pass filter at 80Hz
            'acompressor=threshold=-18dB:ratio=2:attack=20:release=1000,'  # Compression
            'volume=volume=2.1,'  # Increase volume by 2.1 dB
            'loudnorm=I=-20:TP=-3:LRA=11,'  # RMS normalization to -20dB
            'alimiter=level_in=0.9:level_out=0.9:limit=0.7:attack=5:release=50',  # Limiter
            # Output format settings
            '-ar', '44100',      # 44.1kHz sample rate
            '-ac', '1',          # Mono output
            '-codec:a', 'libmp3lame',
            '-b:a', '192k',      # Force 192kbps bitrate
            '-f', 'mp3',         # Force MP3 format
            output_path
        ]
        
        # Execute FFmpeg command
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error processing audio: {e.stderr if hasattr(e, 'stderr') else str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")
