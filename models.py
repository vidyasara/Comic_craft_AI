from pydantic import BaseModel, Field, field_validator


class PromptRequest(BaseModel):
    story_prompt: str = Field(
        ...,
        min_length=5,
        max_length=2000
    )

    character_name: str = Field(
        ...,
        min_length=1,
        max_length=80
    )

    setting: str = Field(
        ...,
        min_length=1,
        max_length=120
    )

    tone: str = Field(
        ...,
        min_length=1,
        max_length=80
    )

    art_style: str = Field(
        ...,
        min_length=1,
        max_length=80
    )

    @field_validator("*")
    @classmethod
    def strip_values(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Value cannot be empty.")

        return value

class CharacterProfile(BaseModel):
    name: str
    species_or_type: str
    appearance: str
    clothing_or_accessories: str
    distinctive_features: str
    identity_description: str        


class PanelOutline(BaseModel):
    panel_number: int = Field(
        ...,
        ge=1,
        le=5
    )

    title: str

    scene_description: str

    image_prompt: str


class DialogueLine(BaseModel):
    speaker: str

    text: str

    bubble_position: str = "top-left"

    tail_direction: str = "bottom-right"


class StoryPanel(BaseModel):
    panel_number: int = Field(
        ...,
        ge=1,
        le=5
    )

    title: str

    scene_description: str

    caption: str

    narration: str

    dialogue: list[DialogueLine] = Field(
        default_factory=list
    )


class ComicLayoutPanel(BaseModel):
    panel_number: int

    title: str

    image_path: str

    scene_description: str

    caption: str

    narration: str

    dialogue: list[DialogueLine] = Field(
        default_factory=list
    )

    image_prompt: str


class ComicResponse(BaseModel):
    comic_id: str

    panels: list[ComicLayoutPanel]

    pdf_url: str