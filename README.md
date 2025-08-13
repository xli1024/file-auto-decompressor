# File Auto-Decompressor

A Python service that automatically monitors a directory for new compressed files (.zip, .rar, .7z), decompresses them to a specified output directory, and removes the original compressed files.

## Features

- Real-time monitoring of a directory for new compressed files
- Support for ZIP, RAR, and 7z file formats
- **Smart download completion detection**: Waits for files to finish downloading before attempting decompression
- **Password support**: Automatically tries default passwords for password-protected archives
- Automatic decompression to a specified output directory
- Removal of original compressed files after successful decompression
- Comprehensive error handling and logging
- Docker support for easy deployment

### New Features

#### Download Completion Detection
The system now intelligently waits for files to complete downloading before attempting decompression:
- Skips files with 0 bytes size
- Monitors file size changes every 5 seconds
- Only processes files after size remains stable for 30 seconds
- Prevents decompression failures due to incomplete downloads

#### Password-Protected Archive Support
- Accepts a list of default passwords via command line or environment variables
- Tries passwords sequentially when encountering password-protected archives
- Supports password-protected ZIP, RAR, and 7z files
- Logs successful password usage for audit purposes
- Gracefully handles exhausted password attempts

## Requirements

- Python 3.6+
- Docker (for containerized deployment)

## Installation

### Local Installation

1. Clone the repository:
   ```bash
   git clone <your-repository-url>
   cd file-auto-decompressor
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Install system dependencies:
   - For Ubuntu/Debian:
     ```bash
     sudo apt-get update && sudo apt-get install -y p7zip-full unrar
     ```
   - For macOS:
     ```bash
     brew install p7zip unrar
     ```
   - For Windows:
     Install 7-Zip and WinRAR, and ensure they are in your PATH.

### Docker Installation

1. Clone the repository:
   ```bash
   git clone <your-repository-url>
   cd file-auto-decompressor
   ```

2. Build the Docker image:
   ```bash
   docker build -t file-auto-decompressor .
   ```

## Usage

### Local Usage

Run the script with default settings:
```bash
python main.py
```

Customize the input and output directories:
```bash
python main.py --input-dir /path/to/downloads --output-dir /path/to/output
```

Enable file logging:
```bash
python main.py --log-dir /path/to/logs
```

Set a different log level:
```bash
python main.py --log-level DEBUG
```

Use default passwords for password-protected archives:
```bash
python main.py --default-passwords "password123,admin,123456"
```

Combine multiple options:
```bash
python main.py \
  --input-dir /path/to/downloads \
  --output-dir /path/to/output \
  --default-passwords "password123,admin,secret" \
  --log-level INFO
```

### Docker Usage

Run the container with default settings:
```bash
docker run -d \
  -v /path/to/downloads:/downloads \
  -v /path/to/output:/download_files \
  --restart always \
  --name file-auto-decompressor \
  file-auto-decompressor
```

### Using Docker Compose

1. Edit the docker-compose.yml file to specify your directory paths:
   ```yaml
   volumes:
     - /path/to/downloads:/downloads        # Change this to your downloads directory
     - /path/to/output:/download_files      # Change this to your output directory
   ```

2. (Optional) Create a `.env` file to set default passwords:
   ```bash
   # Copy the example file and edit it
   cp example.env .env
   # Edit .env to set your passwords
   ```

3. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

#### Docker Compose with Passwords

To use default passwords with Docker Compose, you can:

**Option 1: Use environment file (.env)**
```bash
# Create .env file
echo "DEFAULT_PASSWORDS=password123,admin,123456" > .env
docker-compose up -d
```

**Option 2: Set environment variable directly**
```bash
DEFAULT_PASSWORDS="password123,admin,123456" docker-compose up -d
```

**Option 3: Run container manually with passwords**
```bash
docker run -d \
  -v /path/to/downloads:/downloads \
  -v /path/to/output:/download_files \
  -e DEFAULT_PASSWORDS="password123,admin,123456" \
  --restart always \
  --name file-auto-decompressor \
  file-auto-decompressor
```

## Configuration

The application can be configured using command-line arguments:

- `--input-dir`: Directory to monitor for new compressed files (default: /downloads)
- `--output-dir`: Directory where decompressed files will be saved (default: /download_files)
- `--log-dir`: Directory where log files will be stored (default: None, logs to console only)
- `--log-level`: Logging level (default: INFO, options: DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--default-passwords`: Comma-separated list of default passwords to try for password-protected archives (default: empty)

### Environment Variables

When using Docker, you can also configure the application using environment variables:

- `DEFAULT_PASSWORDS`: Same as `--default-passwords` command-line argument

### File Stability Settings

The download completion detection uses these default settings:
- **Stability duration**: 30 seconds (file size must remain unchanged)
- **Check interval**: 5 seconds (how often to check file size)
- **Max retries**: 3 attempts before giving up on unstable files

These settings are currently hardcoded but provide robust detection for most download scenarios.

## License

[MIT License](LICENSE)
