import subprocess
import os

def process_audio_file(input_path, output_path):
    """
    Process audio file according to ACX standards using FFmpeg
    """
    try:
        # FFmpeg command chain for ACX processing
        ffmpeg_command = [
            'ffmpeg', '-i', input_path,
            # High-pass filter at 80Hz
            '-af', 'highpass=f=80',
            # Compression
            '-af', 'acompressor=threshold=-18dB:ratio=2:attack=20:release=1000',
            # Normalization to -3dB
            '-af', 'volume=volume=0.7079458',  # -3dB = 10^(-3/20) ≈ 0.7079458
            # RMS normalization to -20dB
            '-af', 'loudnorm=I=-20:TP=-3:LRA=11',
            # Limiter
            '-af', 'alimiter=level_in=1:level_out=1:limit=-3:attack=5:release=50',
            # Output format settings
            '-ar', '44100',  # 44.1kHz sample rate
            '-ab', '192k',   # 192kbps bitrate
            '-ac', '2',      # Stereo
            '-codec:a', 'libmp3lame',
            '-q:a', '0',     # Highest quality
            output_path
        ]
        
        # Execute FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error processing audio: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")
