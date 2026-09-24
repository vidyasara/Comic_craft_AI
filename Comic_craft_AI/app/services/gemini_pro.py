import json
import time

from google import genai
from google.genai import types

from app.config import get_settings
from app.models import (
    PanelOutline,
    PromptRequest,
    StoryPanel,
)


def _client():
    settings = get_settings()

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
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
                config=types.GenerateContentConfig(
                    temperature=0.9,
                    response_mime_type="application/json",
                ),
            )

            return response.text.strip()

        except Exception as exc:
            last_error = exc

            print(
                f"Gemini Pro attempt {attempt + 1}/3 failed: {exc}",
                flush=True,
            )

            if attempt < 2:
                time.sleep(3 * (attempt + 1))

    raise RuntimeError(
        f"Gemini Pro generation failed after 3 attempts: {last_error}"
    ) from last_error


def generate_story(
    request: PromptRequest,
    outline: list[dict]
) -> list[dict]:

    settings = get_settings()

    # ---------------------------------------------------------
    # Create ONE client and keep it alive for the whole request
    # ---------------------------------------------------------

    client = _client()

    outline_models = [
        PanelOutline.model_validate(item)
        for item in outline
    ]

    compact_outline = json.dumps(
        [
            item.model_dump()
            for item in outline_models
        ],
        ensure_ascii=False
    )

    prompt = f"""
You are ComicCraft's professional comic writer.

Expand the supplied five-panel outline into a complete comic story.

STORY PROMPT:
{request.story_prompt}

MAIN CHARACTER:
{request.character_name}

SETTING:
{request.setting}

TONE:
{request.tone}

ART STYLE:
{request.art_style}

OUTLINE:

{compact_outline}

Return ONLY valid JSON.

Required format:

{{
    "panels": [
        {{
            "panel_number": 1,
            "title": "Panel title",
            "scene_description": "Scene description",
            "caption": "Short comic caption",
            "narration": "Narration text",
            "dialogue": [
                "Character: dialogue"
            ]
        }}
    ]
}}

Rules:

1. Exactly five panels.
2. Preserve panel numbers.
3. Preserve story continuity.
4. Keep the same protagonist.
5. Keep the same setting.
6. caption should be short.
7. narration should be vivid but concise.
8. dialogue should contain zero to three lines.
9. Do not create a different protagonist.
10. Return JSON only.
"""

    story_text = _generate_text(
        client,
        settings.gemini_pro_model,
        prompt,
    )

    # ---------------------------------------------------------
    # Parse and validate the JSON
    # ---------------------------------------------------------

    try:

        data = json.loads(story_text)

        panels = [
            StoryPanel.model_validate(panel)
            for panel in data["panels"]
        ]

        if len(panels) != settings.max_panels:
            raise ValueError(
                f"Gemini returned {len(panels)} story panels. "
                f"Expected {settings.max_panels}."
            )

        return [
            panel.model_dump()
            for panel in panels
        ]

    except (
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError
    ) as exc:

        raise RuntimeError(
            f"Gemini Pro returned invalid story JSON: {exc}\n"
            f"Response:\n{story_text}"
        ) from exc