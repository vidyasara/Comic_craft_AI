from app.services.layout_builder import (
    build_comic_layout
)


def test_build_comic_layout_matches_panels():

    outline = [

        {
            "panel_number": 1,
            "title": "Start",
            "scene_description": "A forest",
            "image_prompt": "Fox in forest"
        },

        {
            "panel_number": 2,
            "title": "Clue",
            "scene_description": "A path",
            "image_prompt": "Fox follows path"
        }

    ]


    story = [

        {
            "panel_number": 1,
            "title": "Start",
            "scene_description": "A forest",
            "caption": "Dawn",
            "narration": "Finn enters.",
            "dialogue": [
                "Finn: Hello."
            ]
        },

        {
            "panel_number": 2,
            "title": "Clue",
            "scene_description": "A path",
            "caption": "Rustle",
            "narration": (
                "Finn notices a clue."
            ),
            "dialogue": []
        }

    ]


    result = build_comic_layout(

        outline,

        story,

        [
            "/static/panels/a.png",
            "/static/panels/b.png"
        ]

    )


    assert len(result) == 2

    assert (
        result[0]["image_path"]
        .endswith("a.png")
    )

    assert (
        result[1]["title"]
        == "Clue"
    )