# ACX Audiobook Processor

A web application for processing audiobooks to meet Audible's ACX submission standards. The system handles audio file upload/download and performs automated processing to ensure your audiobooks meet ACX requirements.

## Features

- **Web-based Interface**: Simple upload/download functionality
- **Automatic Audio Processing**:
  - RMS normalization to -20dB
  - Peak normalization to -3dB
  - High-pass filtering at 80Hz
  - Compression (2:1 ratio)
  - Limiting
  - 2-second silence padding
  - Mono output conversion
  - 192kbps CBR MP3 format

## Technical Stack

- Flask (Web Framework)
- FFmpeg (Audio Processing)
- Python 3.x

## Requirements

- Python 3.x
- FFmpeg
- Flask

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/acx-audiobook-processor.git
```

2. Install dependencies:
```bash
pip install flask
```

3. Ensure FFmpeg is installed on your system.

4. Run the application:
```bash
python main.py
```

## Usage

1. Open your web browser and navigate to `http://localhost:5000`
2. Select your audio file (MP3 or WAV format)
3. Click "Process Audio"
4. Wait for processing to complete
5. The processed file will automatically download

## License

MIT License

## Author

Created with ❤️ using Replit
