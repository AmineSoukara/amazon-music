# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an unofficial Amazon Music API client and downloader written in Python. It provides both a CLI tool (`amz`) and a Python API for downloading music from Amazon Music with metadata, lyrics, and multiple quality options.

## Key Development Commands

### Package Installation
```bash
pip install -e .                    # Install in development mode
pip install amazon-music            # Install from PyPI
```

### Code Quality & Linting
The project uses GitHub Actions for automated code formatting:
- `autopep8` - PEP8 compliance
- `autoflake` - Remove unused imports/variables  
- `isort` - Sort imports
- `black` - Code formatting

To run locally:
```bash
pip install autopep8 autoflake isort black
autopep8 --in-place --recursive --aggressive --aggressive amz/
autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables --ignore-init-module-imports .
isort amz/
black amz/
```

### Testing
The setup.py includes dev dependencies for testing:
```bash
pip install -e ".[dev]"
pytest                              # Run tests (if test files exist)
pytest-cov                          # Coverage testing
mypy amz/                           # Type checking
flake8 amz/                         # Additional linting
```

### CLI Usage
```bash
amz [URL_OR_ID] [OPTIONS]           # Main CLI command
amz --config                        # Interactive configuration
```

## Architecture Overview

### Core Components

**`amz/main.py` - AmDownloader Class**
- Main downloader orchestrator
- Handles batch downloads (albums/playlists)
- Manages parallel downloads with ThreadPoolExecutor
- Stream quality selection and fallback logic
- Progress tracking and signal handling for graceful shutdown

**`amz/api.py` - API Class** 
- REST API client for Amazon Music endpoints
- Handles authentication with access tokens
- Error handling for rate limits, bans, connection issues
- Endpoints: search, tracks, albums, playlists, stream URLs, Widevine keys

**`amz/cli.py`**
- Command-line interface implementation
- URL parsing for Amazon Music links
- Interactive configuration setup
- Rich console output with themes and progress bars

**`amz/converter.py` - AudioConverter**
- Handles audio format conversion and DRM decryption
- Supports multiple output formats (OPUS, FLAC, MP3, etc.)
- Widevine DRM key integration for protected content

**`amz/metadata.py` - MetadataHandler**
- Embeds track metadata (title, artist, album, lyrics, artwork) 
- Uses mutagen library for various audio formats

### Supporting Modules

- `formats.py` - File/folder naming conventions with multiple format options
- `printer.py` - Rich console output, progress bars, and logging
- `utils.py` - ZIP creation and utility functions
- `errors.py` - Custom exception classes for API errors
- `gui.py` - GUI interface components (optional dependency)

### Key Patterns

**Quality Management**: StreamQuality class handles quality preference with fallback (Max → Master → High → Normal → Medium → Low → Free)

**Batch Processing**: Downloads use ThreadPoolExecutor with configurable workers, global progress tracking, and graceful cancellation

**Configuration**: Uses JSON config files in user directories for persistent settings (tokens, paths, quality preferences)

**Error Handling**: Comprehensive error handling for network issues, DRM failures, and API rate limits with user-friendly messages

## Content Types

- **Tracks**: Individual songs with metadata and lyrics
- **Albums**: Complete album downloads with folder organization  
- **Playlists**: Both official and community playlists
- **Quality Options**: From Low (48kbps OPUS) to Max (24-bit/192kHz FLAC)

## Authentication

Requires Amazon Music premium account access tokens obtained through the API service. Tokens are stored securely and can be managed via CLI commands.