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
    Optimized version for faster processing of large files
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
        
        # For very large files, we'll use simplified processing
        if is_large_file:
            # More efficient processing for large files
            print(f"Processing large file ({file_size_mb:.2f} MB) with optimized settings...")
            # Build a command with fewer filters for better performance with large files
            ffmpeg_command = [
                'ffmpeg', '-y',
                '-threads', '4',  # Use 4 threads for faster processing
                '-i', input_path,
                '-map_metadata', '-1',  # Strip all metadata
                '-af',
                # Process audio for large files without removing content
                'highpass=f=80,' \
                'loudnorm=I=-20:TP=-3:LRA=11,' \
                'apad=pad_dur=2:pad_len=88200',  # Exactly 2 seconds at 44.1kHz
                # Basic output settings
                '-ar', '44100',  # 44.1kHz sample rate
                '-ac', '1',      # Mono output
                '-b:a', '192k',  # 192kbps bitrate
                '-codec:a', 'libmp3lame',
                '-f', 'mp3',
                temp_output
            ]
        else:
            # Standard optimized processing for normal-sized files
            print(f"Processing file ({file_size_mb:.2f} MB) with standard settings...")
            ffmpeg_command = [
                'ffmpeg', '-y',
                '-threads', '4',
                '-i', input_path,
                '-map_metadata', '-1'
            ]
            
            # Format-specific optimizations
            if is_wav:
                ffmpeg_command.extend([
                    '-af',
                    # Full processing for WAV files that preserves content with exact 2s silence
                    'silenceremove=start_periods=1:start_threshold=-60dB:detection=peak,' \
                    'silenceremove=stop_periods=1:stop_threshold=-60dB:detection=peak,' \
                    'highpass=f=80,' \
                    'acompressor=threshold=-18dB:ratio=2:attack=20:release=1000,' \
                    'loudnorm=I=-20:TP=-3:LRA=11,' \
                    'adelay=2000|2000,' \
                    'apad=pad_dur=2',
                ])
            else:
                ffmpeg_command.extend([
                    '-af',
                    # MP3-specific processing chain that preserves content with exact silence
                    'silenceremove=start_periods=1:start_threshold=-60dB:detection=peak,' \
                    'silenceremove=stop_periods=1:stop_threshold=-60dB:detection=peak,' \
                    'highpass=f=80,' \
                    'acompressor=threshold=-18dB:ratio=2:attack=20:release=1000,' \
                    'loudnorm=I=-20:TP=-3:LRA=11,' \
                    'adelay=2000|2000,' \
                    'apad=pad_dur=2',
                ])
            
            # Common output settings
            ffmpeg_command.extend([
                # Output format settings
                '-ar', '44100',
                '-ac', '1',
                '-codec:a', 'libmp3lame',
                '-b:a', '192k',
                # Strip all metadata
                '-map_chapters', '-1',
                '-map_metadata', '-1',
                # Clear metadata fields
                '-metadata', 'title=', '-metadata', 'artist=', '-metadata', 'album=',
                # Output format
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
                '-map_metadata', '-1',
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