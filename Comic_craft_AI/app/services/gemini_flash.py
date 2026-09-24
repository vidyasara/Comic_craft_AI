import time

from google import genai
from google.genai import types

from app.config import get_settings
from app.models import PanelOutline, PromptRequest


def _client():
    settings = get_settings()

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Please add it to your .env file."
        )

    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=120000),
    )


def _generate_text(client, model, prompt):
    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            return response.text.strip()

        except Exception as exc:
            last_error = exc

            print(
                f"Gemini attempt {attempt + 1}/3 failed: {exc}",
                flush=True,
            )

            if attempt < 2:
                time.sleep(3 * (attempt + 1))

    raise RuntimeError(
        f"Gemini generation failed after 3 attempts: {last_error}"
    ) from last_error


def generate_outline(
    request: PromptRequest
) -> list[dict]:

    settings = get_settings()
    client = _client()

    # ---------------------------------------------------------
    # STEP 1: Generate the five-panel story
    # ---------------------------------------------------------

    story_prompt = f"""
Create exactly 5 sequential comic panels.

Story:
{request.story_prompt}

Main character:
{request.character_name}

Setting:
{request.setting}

Tone:
{request.tone}

Art style:
{request.art_style}

Return exactly five lines.

Use this format:

Panel 1: short description
Panel 2: short description
Panel 3: short description
Panel 4: short description
Panel 5: short description

Each panel should contain only one short sentence.

Create a clear beginning, middle, and ending.
Keep the character and setting consistent.
"""

    story_text = _generate_text(
        client,
        settings.gemini_flash_model,
        story_prompt,
    )

    # ---------------------------------------------------------
    # STEP 2: Extract panel descriptions
    # ---------------------------------------------------------

    lines = [
        line.strip()
        for line in story_text.splitlines()
        if line.strip()
    ]

    panel_lines = []

    for line in lines:
        cleaned = line.strip()

        if cleaned.lower().startswith("panel "):
            panel_lines.append(cleaned)

        elif cleaned[:1].isdigit() and "." in cleaned[:3]:
            panel_lines.append(cleaned)

    if len(panel_lines) != settings.max_panels:
        raise RuntimeError(
            f"Gemini returned {len(panel_lines)} panels. "
            f"Expected {settings.max_panels}.\n"
            f"Response:\n{story_text}"
        )

    # ---------------------------------------------------------
    # STEP 3: Generate an image prompt for each panel
    # ---------------------------------------------------------

    panels = []

    for index, line in enumerate(panel_lines, start=1):

        if ":" in line:
            description = line.split(":", 1)[1].strip()

        elif "." in line:
            description = line.split(".", 1)[1].strip()

        else:
            description = line.strip()

        image_prompt_request = f"""
Create a detailed image-generation prompt for this comic panel.

Panel description:
{description}

Main character:
{request.character_name}

Setting:
{request.setting}

Art style:
{request.art_style}

The image prompt must describe:
- character appearance
- action
- environment
- lighting
- composition
- camera angle
- comic art style

Do not include dialogue.

Return only the image prompt as plain text.
"""

        image_prompt = _generate_text(
            client,
            settings.gemini_flash_model,
            image_prompt_request,
        )

        panel = PanelOutline(
            panel_number=index,
            title=f"Panel {index}",
            scene_description=description,
            image_prompt=image_prompt,
        )

        panels.append(panel.model_dump())

    return panels