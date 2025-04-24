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

## License

[MIT License](LICENSE)
