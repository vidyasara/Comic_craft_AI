from app.models import (
    ComicLayoutPanel,
    DialogueLine,
)


def build_comic_layout(
    outline: list[dict],
    story: list[dict],
    image_paths: list[str]
) -> list[dict]:

    outline_by_id = {
        int(item["panel_number"]): item
        for item in outline
    }

    story_by_id = {
        int(item["panel_number"]): item
        for item in story
    }

    if len(image_paths) != len(outline_by_id):
        raise ValueError(
            "Number of images does not match panel count."
        )

    layout = []

    for index, image_path in enumerate(
        image_paths,
        start=1
    ):

        if index not in outline_by_id:
            raise ValueError(
                f"Missing outline for panel {index}."
            )

        if index not in story_by_id:
            raise ValueError(
                f"Missing story for panel {index}."
            )

        outline_panel = outline_by_id[index]
        story_panel = story_by_id[index]

        # -----------------------------------------------------
        # Validate dialogue objects
        # -----------------------------------------------------

        dialogue = [
            DialogueLine.model_validate(line)
            for line in story_panel.get(
                "dialogue",
                []
            )
        ]

        # -----------------------------------------------------
        # Build panel
        # -----------------------------------------------------

        panel = {
            "panel_number": index,

            "title": (
                story_panel["title"]
                or outline_panel["title"]
            ),

            "image_path": image_path,

            "scene_description":
                story_panel["scene_description"],

            "caption":
                story_panel["caption"],

            "narration":
                story_panel["narration"],

            "dialogue":
                dialogue,

            "image_prompt":
                outline_panel["image_prompt"],
        }

        # -----------------------------------------------------
        # Validate complete comic panel
        # -----------------------------------------------------

        validated = ComicLayoutPanel.model_validate(
            panel
        )

        layout.append(
            validated.model_dump()
        )

    return layout