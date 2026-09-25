import pytest

from pydantic import ValidationError

from app.models import PromptRequest


def test_prompt_request_accepts_valid_input():

    request = PromptRequest(

        story_prompt=(
            "A fox explores a magical forest."
        ),

        character_name="Finn",

        setting="forest",

        tone="funny",

        art_style="comic book"
    )

    assert request.character_name == "Finn"


def test_prompt_request_rejects_short_story():

    with pytest.raises(
        ValidationError
    ):

        PromptRequest(

            story_prompt="fox",

            character_name="Finn",

            setting="forest",

            tone="funny",

            art_style="comic book"
        )