import json
import time

from google import genai
from google.genai import types

from app.config import get_settings
from app.models import (
    CharacterProfile,
    PanelOutline,
    PromptRequest,
)


def _client():
    settings = get_settings()

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Please add it to your .env file."
        )

    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(
            timeout=300000
        ),
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
                f"Gemini attempt "
                f"{attempt + 1}/3 failed: {exc}",
                flush=True,
            )

            if attempt < 2:

                time.sleep(
                    3 * (attempt + 1)
                )

    raise RuntimeError(
        "Gemini generation failed "
        f"after 3 attempts: {last_error}"
    ) from last_error

def _generate_character_profile(
    client,
    model,
    request: PromptRequest
) -> CharacterProfile:

    prompt = f"""
Create a permanent visual identity profile for the
main character of a five-panel comic.

Story:
{request.story_prompt}

Character name:
{request.character_name}

Setting:
{request.setting}

Tone:
{request.tone}

Art style:
{request.art_style}

Return ONLY valid JSON using exactly this structure:

{{
    "name": "{request.character_name}",
    "species_or_type": "...",
    "appearance": "...",
    "clothing_or_accessories": "...",
    "distinctive_features": "...",
    "identity_description": "..."
}}

Rules:

1. Determine the character's species or type from
   the story.

2. If the story describes the character as an animal,
   keep that exact animal species.

3. If the story describes the character as a human,
   keep the character human.

4. If the story describes the character as a robot,
   creature, fantasy being, alien, or another type,
   preserve that type.

5. Do not invent a completely different character.

6. Describe stable visual characteristics that can be
   reproduced across all five comic panels.

7. Include recognizable physical characteristics.

8. Include stable clothing or accessories when
   appropriate.

9. Include distinctive features that help an image
   generator recognize the same character.

10. identity_description must be a concise but detailed
    description that can be copied into every image
    generation prompt.

11. The character identity must remain unchanged across
    all five panels.

Return JSON only.
"""

    profile_text = _generate_text(
        client,
        model,
        prompt,
    )

    try:

        data = json.loads(
            profile_text
        )

        profile = CharacterProfile.model_validate(
            data
        )

        return profile

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ) as exc:

        raise RuntimeError(
            "Gemini returned an invalid "
            f"character profile: {exc}\n"
            f"Response:\n{profile_text}"
        ) from exc

def generate_outline(
    request: PromptRequest
) -> list[dict]:

    settings = get_settings()
    client = _client()

    # STEP 1: Generate a simple five-panel story outline.
    outline_prompt = f"""
Create a five-panel comic story outline.

Story idea:
{request.story_prompt}

Main character:
{request.character_name}

Setting:
{request.setting}

Tone:
{request.tone}

Art style:
{request.art_style}

Create exactly five panels.

For each panel provide:
- panel number
- short title
- detailed scene description

The main character must remain consistent throughout
the story.

Return only valid JSON in this format:

[
  {{
    "panel_number": 1,
    "title": "Panel title",
    "scene_description": "Detailed scene description"
  }}
]
"""

    raw_outline = _generate_text(
        client,
        settings.gemini_flash_model,
        outline_prompt,
    )

    try:
        outline_data = json.loads(raw_outline)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Gemini returned invalid outline JSON: {exc}"
        ) from exc

    if not isinstance(outline_data, list):
        raise RuntimeError(
            "Gemini outline response must be a list."
        )

    if len(outline_data) != 5:
        raise RuntimeError(
            "Gemini must generate exactly five panels."
        )

    # STEP 2: Generate a permanent character identity profile.
    character_profile = _generate_character_profile(
    client,
    settings.gemini_flash_model,
    request,
)

    panels = []

    for index, item in enumerate(
        outline_data,
        start=1
    ):

        description = item.get(
            "scene_description",
            ""
        )

        title = item.get(
            "title",
            f"Panel {index}"
        )

        image_prompt_request = f"""
Create a detailed image-generation prompt for this
comic panel.

PERMANENT CHARACTER IDENTITY:

Name:
{character_profile.name}

Species / Type:
{character_profile.species_or_type}

Appearance:
{character_profile.appearance}

Clothing / Accessories:
{character_profile.clothing_or_accessories}

Distinctive Features:
{character_profile.distinctive_features}

Identity Description:
{character_profile.identity_description}

THIS CHARACTER IDENTITY IS LOCKED.

The character named "{character_profile.name}" MUST
remain the same character in every panel.

Do not change the character's species or type.
Do not turn an animal into a human.
Do not turn a human into an animal.
Do not change the character's major appearance.
Do not replace the character with another character.

Panel description:
{description}

Main character:
{request.character_name}

Setting:
{request.setting}

Art style:
{request.art_style}

The image prompt must describe:

- the locked character's appearance
- character position in the composition
- character action
- environment
- important secondary characters
- lighting
- composition
- camera angle
- depth
- comic art style

COMPOSITION RULES:

1. Keep the main character visually recognizable
   and consistent with the story.

2. If the panel description specifies a character
   position, preserve that position.

3. Leave some visually clean negative space for
   speech bubbles.

4. Do not place important facial features directly
   underneath likely speech-bubble areas.

5. Avoid putting all characters directly in the center
   of the image.

6. When multiple characters are present, arrange them
   so their positions are visually distinguishable.

7. Favor clear left/right or foreground/background
   separation between characters.

8. The final artwork should look like a comic panel,
   not like a poster filled with text.

9. Do NOT render dialogue, speech bubbles, captions,
   letters, subtitles, or written words inside the image.

10. The artwork itself must contain no text.

Return only the image prompt as plain text.
"""

        image_prompt = _generate_text(
            client,
            settings.gemini_flash_model,
            image_prompt_request,
        )

        panel = PanelOutline(
            panel_number=index,
            title=title,
            scene_description=description,
            image_prompt=image_prompt,
        )

        panels.append(
            panel.model_dump()
        )

    return panels