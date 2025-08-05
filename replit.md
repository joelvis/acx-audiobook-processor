# ACX Audiobook Processor

## Overview

The ACX Audiobook Processor is a web-based audio processing tool designed to automatically convert raw audio files to meet Audible's ACX (Audiobook Creation Exchange) submission standards. The application provides a simple upload interface where users can submit MP3 or WAV files and receive processed audiobooks that comply with ACX technical requirements including specific RMS levels, peak normalization, filtering, and format specifications.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology Stack**: HTML5, CSS3, JavaScript, Bootstrap (dark theme)
- **Design Pattern**: Single-page application with minimal UI focused on file upload/download workflow
- **User Interface**: Simple form-based interface with collapsible processing information panel
- **File Handling**: Client-side file validation and drag-and-drop support for audio files
- **Progress Tracking**: Real-time processing status updates with estimated completion times

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Architecture Pattern**: MVC (Model-View-Controller) with separation of concerns
- **Request Handling**: RESTful endpoints for file upload, processing estimation, and health checks
- **File Processing**: Asynchronous audio processing pipeline using utility modules
- **Security**: Secure filename handling, file type validation, and size limits (500MB max)
- **Error Handling**: Comprehensive error catching with user-friendly error messages

### Audio Processing Pipeline
- **Processing Engine**: FFmpeg command-line tool for audio manipulation
- **Processing Steps**: 
  - Noise reduction and high-pass filtering (80Hz)
  - Dynamic range compression (2:1 ratio)
  - Peak normalization (-3dB) and RMS normalization (-20dB)
  - Limiting and silence padding (2 seconds at start/end)
  - Mono conversion and metadata stripping
- **Output Format**: 192kbps CBR MP3 at 44.1kHz sample rate
- **File Management**: Temporary file handling with automatic cleanup

### Data Storage
- **File Storage**: Temporary filesystem storage using system temp directory
- **Session Management**: Flask session handling with secret key configuration
- **No Persistent Database**: Stateless application design with no permanent data storage

### Authentication and Authorization
- **Security Model**: No user authentication required (public tool)
- **Access Control**: Basic file type and size validation
- **Session Security**: Flask secret key for session integrity

## External Dependencies

### Third-Party Libraries
- **Flask**: Python web framework for HTTP request handling and routing
- **Werkzeug**: WSGI utility library for secure filename handling
- **Bootstrap**: Frontend CSS framework for responsive UI components

### System Dependencies
- **FFmpeg**: Command-line audio processing engine for all audio manipulations
- **Python 3.x**: Runtime environment with built-in libraries (os, pathlib, tempfile, subprocess)

### Hosting and Deployment
- **Replit Platform**: Cloud hosting environment with integrated development tools
- **Web Server**: Built-in Flask development server configured for production use
- **Port Configuration**: HTTP server running on port 5000 with external access

### File Format Support
- **Input Formats**: MP3 and WAV audio files
- **Output Format**: MP3 (192kbps CBR, 44.1kHz, mono)
- **Processing Constraints**: 500MB maximum file size limit

### External APIs
- **No External APIs**: Self-contained processing without external service dependencies
- **Local Processing**: All audio processing performed server-side using FFmpeg