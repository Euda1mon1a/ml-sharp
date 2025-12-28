"""Gradio web interface for SHARP 3D view synthesis."""

import imghdr
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

import gradio as gr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration via environment variables
DATA_DIR = Path(os.getenv("SHARP_DATA_DIR", "/app/data"))
OUTPUT_DIR = DATA_DIR / "output"
ALLOWED_IMAGE_TYPES = {"jpeg", "png", "gif", "bmp", "webp"}
MAX_FILE_SIZE_MB = int(os.getenv("SHARP_MAX_FILE_SIZE_MB", "50"))


def validate_image(image_path: str) -> None:
    """Validate that the uploaded file is a valid image.

    Args:
        image_path: Path to the uploaded image file.

    Raises:
        ValueError: If the file is not a valid image type.
    """
    file_type = imghdr.what(image_path)
    if file_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(
            f"Invalid file type: {file_type}. "
            f"Allowed types: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}"
        )

    # Check file size
    file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File too large: {file_size_mb:.1f}MB. Maximum: {MAX_FILE_SIZE_MB}MB"
        )


def predict(image: str) -> tuple[str | None, str | None]:
    """Process an image through SHARP to generate 3D view synthesis videos.

    Args:
        image: Path to the input image file (provided by Gradio).

    Returns:
        Tuple of (rgb_video_path, depth_video_path) or (None, None) on error.
    """
    if image is None:
        return None, None

    try:
        # Validate the uploaded image
        validate_image(image)
    except ValueError as e:
        logger.warning(f"Image validation failed: {e}")
        raise gr.Error(str(e))

    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_path = DATA_DIR / "input.jpg"

    # Copy input image
    shutil.copy(image, input_path)

    # Run sharp command
    cmd = [
        "sharp",
        "predict",
        "-i",
        str(input_path),
        "-o",
        str(OUTPUT_DIR),
        "--render",
    ]

    # Execute command
    try:
        t = time.time()
        logger.info("Starting SHARP prediction")
        result = subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        elapsed = round(time.time() - t, 3)
        logger.info(f"SHARP prediction completed in {elapsed} seconds")
    except subprocess.TimeoutExpired:
        logger.error("SHARP prediction timed out after 5 minutes")
        raise gr.Error("Processing timed out. Please try a smaller image.")
    except subprocess.CalledProcessError as e:
        # Log detailed error server-side only
        logger.error(f"SHARP command failed with exit code {e.returncode}")
        logger.error(f"stdout: {e.stdout.decode() if e.stdout else 'N/A'}")
        logger.error(f"stderr: {e.stderr.decode() if e.stderr else 'N/A'}")
        # Return generic error to user
        raise gr.Error("Failed to process image. Please try again with a different image.")

    # Find output videos
    rgb_video = OUTPUT_DIR / "input.mp4"
    depth_video = OUTPUT_DIR / "input.depth.mp4"

    rgb_path = str(rgb_video) if rgb_video.exists() else None
    depth_path = str(depth_video) if depth_video.exists() else None

    if rgb_path:
        return rgb_path, depth_path

    logger.warning("No output videos were generated")
    raise gr.Error("No output was generated. Please try a different image.")


def create_demo() -> gr.Interface:
    """Create and configure the Gradio interface.

    Returns:
        Configured Gradio Interface instance.
    """
    return gr.Interface(
        fn=predict,
        inputs=gr.Image(type="filepath", label="Input Image"),
        outputs=[
            gr.Video(label="RGB Video"),
            gr.Video(label="Depth Video"),
        ],
        title="SHARP 3D View Synthesis",
        description=(
            "Upload an image to generate a 3D view synthesis video. "
            "SHARP creates photorealistic novel views from a single photograph."
        ),
        examples=[["data/teaser.jpg"]] if (DATA_DIR.parent / "data" / "teaser.jpg").exists() else None,
        concurrency_limit=2,  # Limit concurrent GPU operations
        flagging_mode="never",  # Disable flagging for security
    )


def get_auth() -> tuple[str, str] | None:
    """Get authentication credentials from environment variables.

    Returns:
        Tuple of (username, password) if configured, None otherwise.
    """
    username = os.getenv("SHARP_AUTH_USERNAME")
    password = os.getenv("SHARP_AUTH_PASSWORD")
    if username and password:
        return (username, password)
    return None


if __name__ == "__main__":
    logger.info(
        "SHARP - Sharp Monocular View Synthesis in Less Than a Second "
        "(https://github.com/apple/ml-sharp)"
    )

    demo = create_demo()

    # Get optional authentication
    auth = get_auth()
    if auth:
        logger.info("Authentication enabled")
    else:
        logger.warning(
            "No authentication configured. Set SHARP_AUTH_USERNAME and "
            "SHARP_AUTH_PASSWORD environment variables to enable authentication."
        )

    # Launch server
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("SHARP_PORT", "7860")),
        auth=auth,
        show_error=True,
    )
