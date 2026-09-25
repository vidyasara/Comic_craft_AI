from app.services.exporters import save_pdf


def test_save_pdf_creates_file(
    tmp_path,
    monkeypatch
):

    import app.services.exporters as exporters


    monkeypatch.setattr(
        exporters,
        "EXPORTS_DIR",
        tmp_path
    )


    monkeypatch.setattr(
        exporters,
        "STATIC_DIR",
        tmp_path
    )


    result = save_pdf(

        [

            {

                "panel_number": 1,

                "title": "Test",

                "image_path":
                    "/static/panels/missing.png",

                "scene_description":
                    "A test scene.",

                "caption":
                    "Test.",

                "narration":
                    "This is a test.",

                "dialogue": [],

                "image_prompt":
                    "A test image."
            }

        ]

    )


    assert result.startswith(
        "/static/exports/"
    )


    filename = (
        result.rsplit("/", 1)[-1]
    )


    assert (
        tmp_path / filename
    ).exists()