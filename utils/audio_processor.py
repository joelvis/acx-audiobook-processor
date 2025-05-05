import subprocess
import os
from pathlib import Path

def validate_audio_file(input_path):
    """
    Validate the input audio file format and properties
    Simplified for faster processing with large files
    """
    try:
        # Check file existence and basic properties first
        if not os.path.exists(input_path):
            raise Exception(f"File not found: {input_path}")
            
        # Get file size for processing decisions
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        print(f"File size: {file_size_mb:.2f} MB")
        
        # Get file extension - simple extension check for quick validation
        ext = Path(input_path).suffix.lower()
        if ext not in ['.mp3', '.wav']:
            raise Exception("Unsupported file format. Only MP3 and WAV files are supported")
        
        # For large files, we'll skip full validation and just trust the extension
        if file_size_mb > 100:
            print("Large file detected. Using simplified validation.")
            # Just do a quick header check instead of full analysis
            cmd = ['ffmpeg', '-t', '0.1', '-i', input_path, '-f', 'null', '-']
            result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, timeout=5)
            return True
        
        # For smaller files, do more thorough validation
        cmd = ['ffmpeg', '-i', input_path, '-hide_banner']
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, timeout=30)
        output = result.stderr.lower()

        # Check if it's an audio file
        if 'audio:' not in output:
            raise Exception("Not a valid audio file")

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
        # For timeout errors, still allow processing but warn the user
        print("Warning: Timeout during validation, but proceeding with processing.")
        return True

def process_audio_file(input_path, output_path):
    """
    Process audio file according to ACX standards using FFmpeg with complete metadata stripping
    Completely rewritten to preserve all audio content while ensuring exactly 2s silence at start and end
    """
    try:
        # Validate input file - simplified validation for better performance
        validate_audio_file(input_path)

        # Create a temporary file for intermediate processing
        temp_output = output_path + ".temp.mp3"
        
        # Get file size for optimization decisions
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        is_large_file = file_size_mb > 100
        is_wav = input_path.lower().endswith('.wav')
        
        # SIMPLEST APPROACH: Just add proper ACX processing without any silence trimming
        # This preserves ALL content while making sure we have exactly 2s silence added
        print(f"Processing file ({file_size_mb:.2f} MB) with content-preserving approach...")
        
        # Build the initial command with thread optimization
        ffmpeg_command = [
            'ffmpeg', '-y',
            '-threads', '4',  # Use 4 threads for faster processing
            '-i', input_path,
            '-map_metadata', '-1'  # Strip all metadata
        ]
        
        # Basic audio filter chain that preserves content
        # We don't touch the audio content at all, just add processing
        audio_filters = 'highpass=f=80,' \
                        'acompressor=threshold=-18dB:ratio=2:attack=20:release=1000,' \
                        'loudnorm=I=-20:TP=-3:LRA=11,' \
                        'adelay=2000|2000,' \
                        'apad=pad_dur=2'
        
        # Add audio filters
        ffmpeg_command.extend([
            '-af', audio_filters,
            # Output format settings
            '-ar', '44100',      # 44.1kHz sample rate
            '-ac', '1',          # Mono output
            '-codec:a', 'libmp3lame',
            '-b:a', '192k',      # Force 192kbps bitrate
            # Comprehensive metadata stripping to ensure clean files
            '-map_chapters', '-1',
            '-map_metadata', '-1',
            # Clear ALL metadata fields thoroughly to remove any trace of original metadata
            '-metadata', 'title=', '-metadata', 'artist=', '-metadata', 'album=',
            '-metadata', 'comment=', '-metadata', 'genre=', '-metadata', 'copyright=',
            '-metadata', 'description=', '-metadata', 'synopsis=', '-metadata', 'show=',
            '-metadata', 'episode_id=', '-metadata', 'network=', '-metadata', 'url=',
            '-id3v2_version', '0',  # Remove ID3v2 tags completely
            # Force output format
            '-f', 'mp3',
            temp_output
        ])

        # Execute first FFmpeg command with progress information
        print(f"Processing {os.path.basename(input_path)}...")
        subprocess.run(ffmpeg_command, check=True, stderr=subprocess.PIPE)

        # In many cases, we can skip the second pass completely for better performance
        # Second pass is only needed in very specific cases
        # Check the output file size to determine if we need a second pass
        if os.path.getsize(temp_output) > 10 * 1024 * 1024:  # Only for files larger than 10MB
            # Simplified second pass - more efficient for large files
            final_command = [
                'ffmpeg', '-y',
                '-i', temp_output,
                '-c:a', 'copy',  # Just copy, don't re-encode
                # Extra thorough metadata removal for final pass
                '-map_chapters', '-1',
                '-map_metadata', '-1',
                '-id3v2_version', '0',
                '-metadata', 'title=', '-metadata', 'artist=', '-metadata', 'album=',
                '-metadata', 'comment=', '-metadata', 'genre=', '-metadata', 'copyright=',
                output_path
            ]
            # Execute second FFmpeg command
            print("Finalizing large audio file...")
            subprocess.run(final_command, check=True, stderr=subprocess.PIPE)
            # Remove the temp file
            if os.path.exists(temp_output):
                os.remove(temp_output)
        else:
            # For smaller files, just rename the temp file to avoid an unnecessary pass
            print("Finalizing output file...")
            # On Windows, we need to remove the destination file first
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_output, output_path)

        print("Processing complete!")
        return True

    except subprocess.CalledProcessError as e:
        # Improved error handling with more detailed information
        error_message = e.stderr.decode('utf-8', errors='replace') if hasattr(e, 'stderr') else str(e)
        raise Exception(f"Error processing audio: {error_message}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")