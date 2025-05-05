import subprocess
import os
from pathlib import Path

def validate_audio_file(input_path):
    """
    Validate the input audio file format and properties
    Optimized to provide better feedback
    """
    try:
        # Get file info using FFmpeg with more efficient command
        cmd = ['ffmpeg', '-i', input_path, '-hide_banner']
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, timeout=10)  # Add timeout for large files
        output = result.stderr.lower()

        # Check if it's an audio file
        if 'audio:' not in output:
            raise Exception("Not a valid audio file")

        # Get file extension
        ext = Path(input_path).suffix.lower()
        if ext not in ['.mp3', '.wav']:
            raise Exception("Unsupported file format. Only MP3 and WAV files are supported")
        
        # Get file size to warn about large files
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        print(f"File size: {file_size_mb:.2f} MB")
        
        if file_size_mb > 100:
            print("Large file detected. Processing may take several minutes.")

        # Get some basic audio info for logging
        audio_info = {}
        if 'duration:' in output:
            duration_line = [line for line in output.split('\n') if 'duration:' in line][0]
            audio_info['duration'] = duration_line.split('duration:')[1].split(',')[0].strip()
        
        if 'audio:' in output:
            audio_line = [line for line in output.split('\n') if 'audio:' in line][0]
            audio_info['format'] = audio_line.split('audio:')[1].strip()
        
        print(f"Audio info: {audio_info}")
        
        return True

    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8', errors='replace') if hasattr(e, 'stderr') else str(e)
        raise Exception(f"Error validating audio file: {error_message}")
    except subprocess.TimeoutExpired:
        raise Exception("Timeout while trying to validate audio file. The file might be too large or corrupted.")

def process_audio_file(input_path, output_path):
    """
    Process audio file according to ACX standards using FFmpeg with complete metadata stripping
    Optimized version with progress reporting and more efficient processing
    """
    try:
        # Validate input file
        validate_audio_file(input_path)

        # Create a temporary file for intermediate processing
        temp_output = output_path + ".temp.mp3"

        # Check if the file is WAV or MP3 to apply different optimizations
        is_wav = input_path.lower().endswith('.wav')
        
        # Simplified processing chain with optimized parameters
        # Reduce the number of steps and simplify the audio filters
        ffmpeg_command = [
            'ffmpeg', '-y',  # Force overwrite output file
            '-threads', '2',  # Use 2 threads - good balance for Replit
            '-i', input_path,
            '-map_metadata', '-1',  # Strip all metadata
            '-af',
            # Simplified audio filter chain
            'apad=pad_dur=2,' \
            'highpass=f=80,' \
            'acompressor=threshold=-18dB:ratio=2:attack=20:release=1000,' \
            'loudnorm=I=-20:TP=-3:LRA=11,' \
            'alimiter=level_in=0.7:level_out=0.7:limit=0.5',
            # Output format settings
            '-ar', '44100',      # 44.1kHz sample rate
            '-ac', '1',          # Mono output
            '-codec:a', 'libmp3lame',
            '-b:a', '192k',      # Force 192kbps bitrate
            '-map_chapters', '-1',   # Remove chapters
            # Clear metadata in one command for better efficiency
            '-metadata', 'title=', '-metadata', 'artist=', '-metadata', 'album=',
            '-metadata', 'comment=', '-metadata', 'encoded_by=', '-metadata', 'copyright=',
            '-metadata', 'creation_time=', '-metadata', 'date=', '-metadata', 'encoder=',
            '-metadata', 'publisher=',
            # Force output format
            '-f', 'mp3',
            temp_output
        ]

        # Execute first FFmpeg command with progress information
        print(f"Processing {os.path.basename(input_path)}...")
        subprocess.run(ffmpeg_command, check=True, stderr=subprocess.PIPE)

        # Second pass: Only copy the file, faster than before
        final_command = [
            'ffmpeg', '-y',
            '-i', temp_output,
            '-codec', 'copy',  # Just copy, don't re-encode
            '-map_metadata', '-1',
            output_path
        ]

        # Execute second FFmpeg command
        print("Finalizing output file...")
        subprocess.run(final_command, check=True, stderr=subprocess.PIPE)

        # Clean up temporary file
        if os.path.exists(temp_output):
            os.remove(temp_output)

        print("Processing complete!")
        return True

    except subprocess.CalledProcessError as e:
        # Improved error handling with more detailed information
        error_message = e.stderr.decode('utf-8', errors='replace') if hasattr(e, 'stderr') else str(e)
        raise Exception(f"Error processing audio: {error_message}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")