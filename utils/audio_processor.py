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
        
        # Even more optimized processing chain for faster execution
        # Customize the pipeline based on file type for better performance
        ffmpeg_command = [
            'ffmpeg', '-y',  # Force overwrite output file
            '-threads', '4',  # Use 4 threads for faster processing
            '-i', input_path
        ]
        
        # Add specific optimizations for WAV vs MP3 input
        if is_wav:
            # WAV files need less preprocessing, so we can simplify
            ffmpeg_command.extend([
                '-map_metadata', '-1',  # Strip all metadata
                '-af',
                # Simplified audio filter chain with faster implementations
                'highpass=f=80,' \
                'acompressor=threshold=-18dB:ratio=2:attack=20:release=1000,' \
                'loudnorm=I=-20:TP=-3:LRA=11:print_format=json,' \
                'apad=pad_dur=2',  # Moved padding to end of chain for better performance
            ])
        else:
            # MP3 files need different handling
            ffmpeg_command.extend([
                '-map_metadata', '-1',  # Strip all metadata
                '-af',
                # Simplified audio filter chain
                'highpass=f=80,' \
                'acompressor=threshold=-18dB:ratio=2:attack=20:release=1000,' \
                'loudnorm=I=-20:TP=-3:LRA=11,' \
                'apad=pad_dur=2',
            ])
        
        # Common output settings for both formats
        ffmpeg_command.extend([
            # Output format settings
            '-ar', '44100',      # 44.1kHz sample rate
            '-ac', '1',          # Mono output
            '-codec:a', 'libmp3lame',
            '-qscale:a', '2',    # Use VBR quality mode for faster encoding
            '-b:a', '192k',      # Force 192kbps bitrate
            # Strip all metadata in one command
            '-map_chapters', '-1',
            '-map_metadata', '-1',
            # Clear any remaining metadata fields
            '-metadata', 'title=', '-metadata', 'artist=', '-metadata', 'album=',
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