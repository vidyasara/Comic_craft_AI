from pathlib import Path
import re
import uuid

from fpdf import FPDF

from app.config import EXPORTS_DIR, STATIC_DIR


def _find_font(name: str) -> str | None:

    candidates = [
        Path("C:/Windows/Fonts") / name,
        Path("/usr/share/fonts/truetype/dejavu") / name,
        Path("/usr/share/fonts/dejavu") / name,
    ]

    for candidate in candidates:

        if candidate.exists():
            return str(candidate)

    return None


def _safe_text(value) -> str:

    if value is None:
        return ""

    text = str(value)

    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\u200c", "")
    text = text.replace("\u200d", "")
    text = text.replace("\ufeff", "")

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    return text.strip()


def _write_text(
    pdf: FPDF,
    text: str,
    line_height: float = 7
):

    text = _safe_text(text)

    if not text:
        return

    width = (
        pdf.w
        - pdf.l_margin
        - pdf.r_margin
    )

    pdf.multi_cell(
        width,
        line_height,
        text
    )


def _draw_speech_bubble(
    pdf: FPDF,
    speaker: str,
    dialogue: str,
    bubble_position: str,
    tail_direction: str,
    image_x: float,
    image_y: float,
    image_w: float,
    image_h: float,
):
    """
    Draw a comic-style speech bubble over the panel image.

    Positions and tail directions are generic and are
    supplied by Gemini for each dialogue line.
    """

    speaker = _safe_text(speaker)
    dialogue = _safe_text(dialogue)

    if not dialogue:
        return

    position = (
        bubble_position
        .lower()
        .replace("-", "_")
        .strip()
    )

    tail = (
        tail_direction
        .lower()
        .replace("-", "_")
        .strip()
    )

    # ---------------------------------------------------------
    # Bubble dimensions
    # ---------------------------------------------------------

    bubble_w = min(
        68,
        max(
            42,
            image_w * 0.36
        )
    )

    # Estimate height from dialogue length.
    text_length = len(dialogue)

    if text_length <= 45:
        bubble_h = 25

    elif text_length <= 85:
        bubble_h = 32

    elif text_length <= 130:
        bubble_h = 40

    else:
        bubble_h = 48

    # ---------------------------------------------------------
    # Position the bubble
    # ---------------------------------------------------------

    margin_x = image_w * 0.04
    margin_y = image_h * 0.05

    positions = {

        "top_left": (
            image_x + margin_x,
            image_y + margin_y
        ),

        "top_center": (
            image_x
            + (image_w - bubble_w) / 2,
            image_y + margin_y
        ),

        "top_right": (
            image_x
            + image_w
            - bubble_w
            - margin_x,
            image_y + margin_y
        ),

        "middle_left": (
            image_x + margin_x,
            image_y
            + (image_h - bubble_h) / 2
        ),

        "middle_right": (
            image_x
            + image_w
            - bubble_w
            - margin_x,
            image_y
            + (image_h - bubble_h) / 2
        ),

        "bottom_left": (
            image_x + margin_x,
            image_y
            + image_h
            - bubble_h
            - margin_y
        ),

        "bottom_center": (
            image_x
            + (image_w - bubble_w) / 2,
            image_y
            + image_h
            - bubble_h
            - margin_y
        ),

        "bottom_right": (
            image_x
            + image_w
            - bubble_w
            - margin_x,
            image_y
            + image_h
            - bubble_h
            - margin_y
        ),
    }

    bubble_x, bubble_y = positions.get(
        position,
        positions["top_left"]
    )

    # ---------------------------------------------------------
    # Keep bubble inside image
    # ---------------------------------------------------------

    bubble_x = max(
        image_x + 3,
        min(
            bubble_x,
            image_x + image_w - bubble_w - 3
        )
    )

    bubble_y = max(
        image_y + 3,
        min(
            bubble_y,
            image_y + image_h - bubble_h - 3
        )
    )

    # ---------------------------------------------------------
    # Draw white bubble
    # ---------------------------------------------------------

    pdf.set_fill_color(
        255,
        255,
        255
    )

    pdf.set_draw_color(
        23,
        20,
        33
    )

    pdf.set_line_width(0.8)

    pdf.ellipse(
        bubble_x,
        bubble_y,
        bubble_w,
        bubble_h,
        style="DF"
    )

    # ---------------------------------------------------------
    # Draw speech-bubble tail
    # ---------------------------------------------------------

    center_x = (
        bubble_x
        + bubble_w / 2
    )

    center_y = (
        bubble_y
        + bubble_h / 2
    )

    if tail == "bottom_left":

        start_x = bubble_x + bubble_w * 0.25
        start_y = bubble_y + bubble_h

        end_x = start_x - 5
        end_y = start_y + 9

        pdf.line(
            start_x,
            start_y,
            end_x,
            end_y
        )

        pdf.line(
            end_x,
            end_y,
            start_x + 7,
            start_y + 1
        )

    elif tail == "bottom_center":

        start_x = center_x
        start_y = bubble_y + bubble_h

        end_x = center_x
        end_y = start_y + 10

        pdf.line(
            start_x,
            start_y,
            end_x,
            end_y
        )

    elif tail == "bottom_right":

        start_x = bubble_x + bubble_w * 0.75
        start_y = bubble_y + bubble_h

        end_x = start_x + 5
        end_y = start_y + 9

        pdf.line(
            start_x,
            start_y,
            end_x,
            end_y
        )

        pdf.line(
            end_x,
            end_y,
            start_x - 7,
            start_y + 1
        )

    elif tail == "top_left":

        start_x = bubble_x + bubble_w * 0.25
        start_y = bubble_y

        end_x = start_x - 5
        end_y = start_y - 9

        pdf.line(
            start_x,
            start_y,
            end_x,
            end_y
        )

        pdf.line(
            end_x,
            end_y,
            start_x + 7,
            start_y - 1
        )

    elif tail == "top_center":

        start_x = center_x
        start_y = bubble_y

        end_x = center_x
        end_y = start_y - 10

        pdf.line(
            start_x,
            start_y,
            end_x,
            end_y
        )

    elif tail == "top_right":

        start_x = bubble_x + bubble_w * 0.75
        start_y = bubble_y

        end_x = start_x + 5
        end_y = start_y - 9

        pdf.line(
            start_x,
            start_y,
            end_x,
            end_y
        )

        pdf.line(
            end_x,
            end_y,
            start_x - 7,
            start_y - 1
        )

    elif tail == "middle_left":

        start_x = bubble_x
        start_y = center_y

        end_x = start_x - 10
        end_y = center_y

        pdf.line(
            start_x,
            start_y,
            end_x,
            end_y
        )

    elif tail == "middle_right":

        start_x = bubble_x + bubble_w
        start_y = center_y

        end_x = start_x + 10
        end_y = center_y

        pdf.line(
            start_x,
            start_y,
            end_x,
            end_y
        )

    # ---------------------------------------------------------
    # Bubble text
    # ---------------------------------------------------------

    text_padding_x = 5
    text_padding_y = 4

    text_x = (
        bubble_x
        + text_padding_x
    )

    text_y = (
        bubble_y
        + text_padding_y
    )

    text_w = (
        bubble_w
        - text_padding_x * 2
    )

    # Speaker name
    if speaker:

        pdf.set_font(
            "DejaVu",
            "B",
            7
        )

        pdf.set_text_color(
            90,
            90,
            90
        )

        pdf.set_xy(
            text_x,
            text_y
        )

        pdf.multi_cell(
            text_w,
            3.5,
            speaker,
            align="C"
        )

        text_y += 4

    # Dialogue
    pdf.set_font(
        "DejaVu",
        "B",
        8
    )

    pdf.set_text_color(
        23,
        20,
        33
    )

    pdf.set_xy(
        text_x,
        text_y
    )

    pdf.multi_cell(
        text_w,
        4,
        dialogue,
        align="C"
    )


def save_pdf(
    layout: list[dict],
    title: str = "ComicCraft Comic"
) -> str:

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4"
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15
    )

    regular_font = _find_font(
        "DejaVuSans.ttf"
    )

    bold_font = _find_font(
        "DejaVuSans-Bold.ttf"
    )

    if regular_font and bold_font:

        pdf.add_font(
            "DejaVu",
            "",
            regular_font
        )

        pdf.add_font(
            "DejaVu",
            "B",
            bold_font
        )

        font_regular = "DejaVu"
        font_bold = "DejaVu"

    else:

        font_regular = "Helvetica"
        font_bold = "Helvetica"

    for panel in layout:

        pdf.add_page()

        # -----------------------------------------------------
        # Panel title
        # -----------------------------------------------------

        pdf.set_font(
            font_bold,
            "B",
            18
        )

        panel_title = (
            f"Panel "
            f"{panel['panel_number']}: "
            f"{_safe_text(panel['title'])}"
        )

        _write_text(
            pdf,
            panel_title,
            10
        )

        pdf.ln(2)

        # -----------------------------------------------------
        # Panel image
        # -----------------------------------------------------

        relative_path = panel["image_path"]

        relative_path = relative_path.replace(
            "/static/",
            "",
            1
        )

        image_file = (
            STATIC_DIR
            / relative_path
        )

        image_x = 15
        image_y = 35
        image_w = 180
        image_h = 180

        if image_file.exists():

            pdf.image(
                str(image_file),
                x=image_x,
                y=image_y,
                w=image_w,
                h=image_h
            )

            # -------------------------------------------------
            # Draw dialogue bubbles over image
            # -------------------------------------------------

            dialogue_lines = panel.get(
                "dialogue",
                []
            )

            for line in dialogue_lines:

                if isinstance(line, dict):

                    speaker = line.get(
                        "speaker",
                        ""
                    )

                    dialogue = line.get(
                        "text",
                        ""
                    )

                    bubble_position = line.get(
                        "bubble_position",
                        "top-left"
                    )

                    tail_direction = line.get(
                        "tail_direction",
                        "bottom-right"
                    )

                else:

                    speaker = ""

                    dialogue = str(line)

                    bubble_position = "top-left"

                    tail_direction = "bottom-right"

                _draw_speech_bubble(
                    pdf=pdf,
                    speaker=speaker,
                    dialogue=dialogue,
                    bubble_position=bubble_position,
                    tail_direction=tail_direction,
                    image_x=image_x,
                    image_y=image_y,
                    image_w=image_w,
                    image_h=image_h,
                )

            pdf.set_y(
                image_y + image_h + 7
            )

        else:

            pdf.set_y(40)

            pdf.set_font(
                font_regular,
                "",
                11
            )

            _write_text(
                pdf,
                "[Panel image unavailable]"
            )

        # -----------------------------------------------------
        # Panel information
        # -----------------------------------------------------

        pdf.set_font(
            font_regular,
            "",
            11
        )

        _write_text(
            pdf,
            "Scene: "
            + _safe_text(
                panel.get(
                    "scene_description",
                    ""
                )
            )
        )

        _write_text(
            pdf,
            "Caption: "
            + _safe_text(
                panel.get(
                    "caption",
                    ""
                )
            )
        )

        _write_text(
            pdf,
            "Narration: "
            + _safe_text(
                panel.get(
                    "narration",
                    ""
                )
            )
        )

        # -----------------------------------------------------
        # Dialogue reference below the image
        # -----------------------------------------------------

        if panel.get("dialogue"):

            pdf.set_font(
                font_bold,
                "B",
                11
            )

            _write_text(
                pdf,
                "Dialogue:"
            )

            pdf.set_font(
                font_regular,
                "",
                11
            )

            for line in panel["dialogue"]:

                if isinstance(line, dict):

                    speaker = _safe_text(
                        line.get(
                            "speaker",
                            ""
                        )
                    )

                    text = _safe_text(
                        line.get(
                            "text",
                            ""
                        )
                    )

                    if speaker and text:

                        dialogue_text = (
                            f"{speaker}: {text}"
                        )

                    elif text:

                        dialogue_text = text

                    else:

                        dialogue_text = speaker

                else:

                    dialogue_text = _safe_text(
                        line
                    )

                _write_text(
                    pdf,
                    "- " + dialogue_text
                )

    filename = (
        f"comic-{uuid.uuid4().hex}.pdf"
    )

    output = (
        EXPORTS_DIR
        / filename
    )

    pdf.output(
        str(output)
    )

    return (
        "/static/exports/"
        + filename
    )