# File Auto-Decompressor

A Python service that automatically monitors a directory for new compressed files (.zip, .rar, .7z), decompresses them to a specified output directory, and removes the original compressed files.

## Features

- Real-time monitoring of a directory for new compressed files
- Support for ZIP, RAR, and 7z file formats
- Automatic decompression to a specified output directory
- Removal of original compressed files after successful decompression
- Comprehensive error handling and logging
- Docker support for easy deployment

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

### Docker Usage

Run the container with default settings:
```bash
docker run -d \
  -v /path/to/downloads:/downloads \
  -v /path/to/output:/download_files \
  -v /path/to/logs:/logs \
  --restart always \
  --name file-auto-decompressor \
  file-auto-decompressor
```

### Using Docker Compose

1. Create a `.env` file with your directory paths:
   ```
   DOWNLOADS_DIR=/path/to/downloads
   OUTPUT_DIR=/path/to/output
   LOGS_DIR=/path/to/logs
   ```

2. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Configuration

The application can be configured using command-line arguments:

- `--input-dir`: Directory to monitor for new compressed files (default: /downloads)
- `--output-dir`: Directory where decompressed files will be saved (default: /download_files)
- `--log-dir`: Directory where log files will be stored (default: None, logs to console only)
- `--log-level`: Logging level (default: INFO, options: DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Docker Hub

To push the image to Docker Hub:

1. Create a Docker Hub account if you don't have one.

2. Log in to Docker Hub:
   ```bash
   docker login
   ```

3. Tag your image:
   ```bash
   docker tag file-auto-decompressor <your-dockerhub-username>/file-auto-decompressor:latest
   ```

4. Push the image:
   ```bash
   docker push <your-dockerhub-username>/file-auto-decompressor:latest
   ```

## License

[MIT License](LICENSE)
