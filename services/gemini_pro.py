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
        http_options=types.HttpOptions(
            timeout=120000
        ),
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
                f"Gemini Pro attempt "
                f"{attempt + 1}/3 failed: {exc}",
                flush=True,
            )

            if attempt < 2:
                time.sleep(
                    3 * (attempt + 1)
                )

    raise RuntimeError(
        "Gemini Pro generation failed "
        f"after 3 attempts: {last_error}"
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

Expand the supplied five-panel outline into a complete
comic story.

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
                {{
                    "speaker": "Character name",
                    "text": "Dialogue spoken by the character",
                    "bubble_position": "top-left",
                    "tail_direction": "bottom-right"
                }}
            ]
        }}
    ]
}}

DIALOGUE RULES:

1. Each dialogue item MUST be a JSON object.

2. Every dialogue object MUST contain:
   - speaker
   - text
   - bubble_position
   - tail_direction

3. "speaker" must contain the actual name or identity
   of the character speaking.

4. "text" must contain ONLY the spoken words.
   Do NOT include the speaker name inside "text".

5. Do NOT use formats such as:
   "Finn: Hello!"
   "Tree: Be careful!"

   Instead use:

   {{
       "speaker": "Finn",
       "text": "Hello!",
       "bubble_position": "top-left",
       "tail_direction": "bottom-right"
   }}

6. The speaker may be ANY character introduced in the story.
   Never assume fixed character names.

7. A panel may contain zero, one, two, or three dialogue
   lines.

8. Keep each dialogue line short enough to fit naturally
   inside a comic speech bubble.

9. "bubble_position" MUST be one of:

   "top-left"
   "top-center"
   "top-right"
   "middle-left"
   "middle-right"
   "bottom-left"
   "bottom-center"
   "bottom-right"

10. "tail_direction" MUST be one of:

   "top-left"
   "top-center"
   "top-right"
   "middle-left"
   "middle-right"
   "bottom-left"
   "bottom-center"
   "bottom-right"

11. Choose the bubble position based on the speaker's
    approximate location in the scene.

12. The bubble should normally be placed in an area that
    does not cover the speaker's face or body.

13. The tail direction should point approximately toward
    the speaker's location.

14. If the speaker is on the left side of the scene,
    prefer a bubble or tail arrangement that points
    toward the left.

15. If the speaker is on the right side of the scene,
    prefer a bubble or tail arrangement that points
    toward the right.

16. If the speaker is near the bottom of the scene,
    the tail should generally point downward.

17. If the speaker is near the top of the scene,
    the tail should generally point upward.

18. When there are multiple characters, position their
    dialogue bubbles so that the bubbles do not overlap
    unnecessarily.

19. When a panel contains multiple speakers, do NOT give
    their dialogue bubbles the same bubble_position.

20. When two speakers are present, distribute their bubbles
    across different areas of the panel.

21. If one speaker is on the left side of the scene and
    another is on the right side, prefer a left-side bubble
    for the left speaker and a right-side bubble for the
    right speaker.

22. Avoid placing two dialogue bubbles directly beside,
    above, or underneath each other when another clear
    position is available.

23. When three speakers are present, distribute their
    bubbles across different regions of the image.

24. Keep each bubble close enough to its speaker that the
    tail direction clearly identifies who is speaking.

25. Never sacrifice dialogue readability just to follow
    the exact character position. If necessary, move the
    bubble farther away while keeping its tail pointing
    toward the speaker.

26. Do not use the same bubble_position for consecutive
    dialogue lines in the same panel unless there is no
    reasonable alternative.
    
STORY RULES:

1. Exactly five panels.
2. Preserve panel numbers.
3. Preserve story continuity.
4. Keep the same protagonist.
5. Keep the same setting.
6. Caption should be short.
7. Narration should be vivid but concise.
8. Do not create a different protagonist.
9. Keep dialogue natural and appropriate to the story.
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
                f"Gemini returned "
                f"{len(panels)} story panels. "
                f"Expected "
                f"{settings.max_panels}."
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
            "Gemini Pro returned invalid story JSON: "
            f"{exc}\n"
            f"Response:\n{story_text}"
        ) from exc