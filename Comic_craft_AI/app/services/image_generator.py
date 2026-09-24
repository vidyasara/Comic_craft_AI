from pathlib import Path
import re
import uuid

from huggingface_hub import InferenceClient

from app.config import get_settings


def _safe_stem(value: str) -> str:

    stem = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "-",
        value
    )

    stem = stem.strip("-").lower()

    return stem[:60] or "panel"


def generate_image(
    image_prompt: str,
    panel_number: int,
    art_style: str
) -> str:

    settings = get_settings()

    if not settings.hf_token:
        raise RuntimeError(
            "HF_TOKEN is not configured. "
            "Please add it to your .env file."
        )

    client = InferenceClient(
        provider="auto",
        api_key=settings.hf_token,
        timeout=180,
    )

    prompt = f"""
{image_prompt}

Visual style:
{art_style}

Comic panel illustration.
Consistent character design.
Expressive character.
Detailed environment.
Cinematic composition.
Clear storytelling.
Beautiful lighting.

Do not include:
text,
speech bubbles,
watermarks,
logos.
"""

    negative_prompt = """
blurry,
low quality,
distorted anatomy,
extra limbs,
extra fingers,
duplicate characters,
deformed face,
text,
watermark,
logo,
speech bubbles
"""

    print(
        f"Generating image for panel {panel_number}...",
        flush=True
    )

    image = client.text_to_image(
        prompt=prompt,
        model=settings.sd_model_id,
        negative_prompt=negative_prompt,
        num_inference_steps=settings.sd_num_inference_steps,
        guidance_scale=settings.sd_guidance_scale,
        width=settings.sd_width,
        height=settings.sd_height,
    )

    filename = (
        f"{panel_number:02d}-"
        f"{_safe_stem(str(uuid.uuid4()))}.png"
    )

    output = (
        Path(__file__).resolve().parents[1]
        / "static"
        / "panels"
        / filename
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    image.save(output)

    print(
        f"Panel {panel_number} saved: {filename}",
        flush=True
    )

    return f"/static/panels/{filename}"