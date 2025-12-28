# Docker Setup Guide for SHARP

This guide covers running SHARP using Docker with the Gradio web interface.

## Prerequisites

- **Docker** 20.10 or later
- **Docker Compose** v2.0 or later
- **NVIDIA GPU** with CUDA support
- **NVIDIA Container Toolkit** ([installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))

### Verify NVIDIA Container Toolkit

```bash
docker run --rm --gpus all nvidia/cuda:12.9.1-base-ubuntu24.04 nvidia-smi
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/apple/ml-sharp.git
cd ml-sharp

# Build and run
docker compose up --build
```

Open http://localhost:7860 in your browser.

## Configuration

### Environment Variables

Configure the application by setting environment variables in `compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `SHARP_AUTH_USERNAME` | *(none)* | Username for web authentication |
| `SHARP_AUTH_PASSWORD` | *(none)* | Password for web authentication |
| `SHARP_MAX_FILE_SIZE_MB` | `50` | Maximum upload file size in MB |
| `SHARP_PORT` | `7860` | Web server port |
| `SHARP_DATA_DIR` | `/app/data` | Data directory inside container |

### Enabling Authentication

Edit `compose.yml` to uncomment and set credentials:

```yaml
environment:
  - SHARP_AUTH_USERNAME=admin
  - SHARP_AUTH_PASSWORD=your-secure-password
```

**Important:** Always enable authentication when exposing the service to a network.

### Resource Limits

The default configuration limits resources to prevent abuse:

```yaml
deploy:
  resources:
    limits:
      cpus: "8"
      memory: 32G
```

Adjust these based on your hardware capabilities.

## Usage

### Web Interface

1. Navigate to http://localhost:7860
2. Upload an image (JPEG, PNG, GIF, BMP, or WebP)
3. Wait for processing (typically under 1 second on GPU)
4. Download the generated RGB and depth videos

### Supported Image Formats

- JPEG/JPG
- PNG
- GIF
- BMP
- WebP

Maximum file size: 50MB (configurable)

### Output

The web interface generates two videos:
- **RGB Video**: Photorealistic 3D view synthesis
- **Depth Video**: Depth map visualization

Output files are saved to the `./data` directory on your host machine.

## Advanced Usage

### Running in Background

```bash
docker compose up -d --build
```

### Viewing Logs

```bash
docker compose logs -f
```

### Stopping the Service

```bash
docker compose down
```

### Rebuilding After Changes

```bash
docker compose up --build --force-recreate
```

### Using a Custom Port

Edit `compose.yml`:

```yaml
ports:
  - "8080:7860"  # Access at localhost:8080
```

Or set the environment variable:

```yaml
environment:
  - SHARP_PORT=8080
ports:
  - "8080:8080"
```

## Production Deployment

### Security Recommendations

1. **Enable Authentication**: Always set `SHARP_AUTH_USERNAME` and `SHARP_AUTH_PASSWORD`

2. **Use a Reverse Proxy**: Deploy behind nginx or Traefik for:
   - SSL/TLS termination
   - Rate limiting
   - Additional security headers

3. **Network Isolation**: Bind to localhost and use a reverse proxy:
   ```yaml
   ports:
     - "127.0.0.1:7860:7860"
   ```

4. **Regular Updates**: Keep the Docker image updated for security patches

### Example nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name sharp.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

## Troubleshooting

### GPU Not Detected

```bash
# Verify NVIDIA Container Toolkit
nvidia-ctk --version

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.9.1-base-ubuntu24.04 nvidia-smi
```

### Out of Memory

Reduce resource limits or process smaller images:

```yaml
environment:
  - SHARP_MAX_FILE_SIZE_MB=20
```

### Build Fails

Ensure you have sufficient disk space (the image requires ~15GB):

```bash
docker system df
docker system prune  # Clean unused resources
```

### Container Won't Start

Check logs for errors:

```bash
docker compose logs sharp
```

### Permission Denied on Data Directory

Ensure the `./data` directory is writable:

```bash
mkdir -p data
chmod 755 data
```

## Development

### Building Manually

```bash
docker build -t sharp:latest .
```

### Running Without Compose

```bash
docker run --gpus all -p 7860:7860 -v $(pwd)/data:/app/data sharp:latest
```

### Accessing Container Shell

```bash
docker compose exec sharp bash
```

## Architecture

The Docker setup includes:

- **Base Image**: `nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04`
- **Python**: 3.13
- **Security**: Runs as non-root user (`sharp`)
- **Web Interface**: Gradio on port 7860
- **Model**: Auto-downloaded on first build (~cached in image)

## License

See the main [README.md](README.md) for license information.
