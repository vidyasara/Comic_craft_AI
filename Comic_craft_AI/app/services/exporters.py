from pathlib import Path
import re
import uuid

from fpdf import FPDF

from app.config import EXPORTS_DIR, STATIC_DIR


def _find_font(name: str) -> str | None:

    candidates = [

        Path("C:/Windows/Fonts") / name,

        Path("/usr/share/fonts/truetype/dejavu")
        / name,

        Path("/usr/share/fonts/dejavu")
        / name,
    ]

    for candidate in candidates:

        if candidate.exists():
            return str(candidate)

    return None


def _safe_text(value) -> str:

    if value is None:
        return ""

    text = str(value)

    # Replace characters that can cause FPDF line-breaking problems.
    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\u200c", "")
    text = text.replace("\u200d", "")
    text = text.replace("\ufeff", "")

    # Collapse excessive whitespace.
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def _write_text(
    pdf: FPDF,
    text: str,
    line_height: float = 7
):

    text = _safe_text(text)

    if not text:
        return

    # Leave a small amount of horizontal room so FPDF
    # always has usable space for line breaking.
    width = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.multi_cell(
        width,
        line_height,
        text
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

        # -------------------------------------------------
        # PANEL TITLE
        # -------------------------------------------------

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

        # -------------------------------------------------
        # PANEL IMAGE
        # -------------------------------------------------

        relative_path = panel["image_path"]

        relative_path = relative_path.replace(
            "/static/",
            "",
            1
        )

        image_file = (
            STATIC_DIR / relative_path
        )

        if image_file.exists():

            pdf.image(
                str(image_file),
                x=15,
                y=35,
                w=180
            )

            pdf.set_y(140)

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

        # -------------------------------------------------
        # SCENE
        # -------------------------------------------------

        pdf.set_font(
            font_regular,
            "",
            11
        )

        _write_text(
            pdf,
            "Scene: "
            + _safe_text(
                panel.get("scene_description", "")
            )
        )

        # -------------------------------------------------
        # CAPTION
        # -------------------------------------------------

        _write_text(
            pdf,
            "Caption: "
            + _safe_text(
                panel.get("caption", "")
            )
        )

        # -------------------------------------------------
        # NARRATION
        # -------------------------------------------------

        _write_text(
            pdf,
            "Narration: "
            + _safe_text(
                panel.get("narration", "")
            )
        )

        # -------------------------------------------------
        # DIALOGUE
        # -------------------------------------------------

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

                _write_text(
                    pdf,
                    "- " + _safe_text(line)
                )

    # -----------------------------------------------------
    # SAVE PDF
    # -----------------------------------------------------

    filename = (
        f"comic-{uuid.uuid4().hex}.pdf"
    )

    output = EXPORTS_DIR / filename

    pdf.output(str(output))

    return (
        "/static/exports/"
        + filename
    )