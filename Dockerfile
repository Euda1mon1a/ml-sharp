FROM nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04

# Install Python 3.13
RUN apt-get update && apt-get install -y wget software-properties-common build-essential && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y python3.13 python3.13-venv python3.13-dev ninja-build && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash sharp

# Install Sharp and dependencies
RUN mkdir /app && chown sharp:sharp /app
COPY --chown=sharp:sharp pyproject.toml requirements.txt requirements.in /app/
COPY --chown=sharp:sharp src/ /app/src/
WORKDIR /app

# Create virtual environment and install dependencies
RUN python3.13 -m venv .venv && chown -R sharp:sharp .venv
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.7;8.9;9.0+PTX"
ENV FORCE_CUDA="1"
RUN .venv/bin/pip install ninja
RUN .venv/bin/pip install -r requirements.txt
RUN .venv/bin/pip install gradio
RUN ln -s /app/.venv/bin/sharp /usr/local/bin/sharp

# Test run to download model and check if it works
RUN wget https://apple.github.io/ml-sharp/thumbnails/Unsplash_-5wkyNA2BPc_0000-0001.jpg -O /tmp/test.jpg
RUN sharp predict -i /tmp/test.jpg -o /tmp/test
RUN rm /tmp/test.jpg /tmp/test -rf

# Copy other files and set ownership
COPY --chown=sharp:sharp . /app

# Create data directory with proper permissions
RUN mkdir -p /app/data && chown -R sharp:sharp /app/data

# Switch to non-root user
USER sharp

# Expose port
EXPOSE 7860

# Start Gradio web server
CMD [".venv/bin/python3.13", "-u", "/app/gradio_web.py"]
