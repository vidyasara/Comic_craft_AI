from pathlib import Path
import uuid

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request
)

from fastapi.responses import (
    FileResponse,
    HTMLResponse
)

from fastapi.templating import Jinja2Templates

from app.config import (
    EXPORTS_DIR,
    TEMPLATES_DIR
)

from app.models import (
    ComicResponse,
    PromptRequest
)

from app.services.exporters import save_pdf

from app.services.gemini_flash import (
    generate_outline
)

from app.services.gemini_pro import (
    generate_story
)

from app.services.image_generator import (
    generate_image
)

from app.services.layout_builder import (
    build_comic_layout
)


router = APIRouter()

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


def _generate(
    request_data: PromptRequest
):

    outline = generate_outline(
        request_data
    )

    story = generate_story(
        request_data,
        outline
    )

    image_paths = []

    for panel in outline:

        image_path = generate_image(
            image_prompt=panel["image_prompt"],
            panel_number=panel["panel_number"],
            art_style=request_data.art_style
        )

        image_paths.append(
            image_path
        )

    layout = build_comic_layout(
        outline,
        story,
        image_paths
    )

    pdf_url = save_pdf(
        layout,
        title=(
            f"{request_data.character_name}'s Comic"
        )
    )

    comic_id = uuid.uuid4().hex

    return (
        comic_id,
        layout,
        pdf_url
    )


@router.get(
    "/",
    response_class=HTMLResponse
)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@router.post(
    "/generate",
    response_class=HTMLResponse
)
async def generate_form(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...)
):

    payload = PromptRequest(
        story_prompt=story_prompt,
        character_name=character_name,
        setting=setting,
        tone=tone,
        art_style=art_style
    )

    try:

        comic_id, layout, pdf_url = (
            _generate(payload)
        )

        request.app.state.comics[
            comic_id
        ] = {
            "layout": layout,
            "pdf_url": pdf_url,
            "title": (
                f"{character_name}'s Comic"
            )
        }

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "comic_id": comic_id,
                "pdf_url": pdf_url
            }
        )

    except Exception as exc:

        print("===== GENERATE ERROR =====", flush=True)
        import traceback
        traceback.print_exc()
        print("==========================", flush=True)

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc)
            },
            status_code=500
        )


@router.post(
    "/generate-comic/json",
    response_model=ComicResponse
)
async def generate_json(
    payload: PromptRequest,
    request: Request
):

    try:

        comic_id, layout, pdf_url = (
            _generate(payload)
        )

        request.app.state.comics[
            comic_id
        ] = {
            "layout": layout,
            "pdf_url": pdf_url,
            "title": (
                f"{payload.character_name}'s Comic"
            )
        }
        return ComicResponse(
            comic_id=comic_id,
            panels=layout,
            pdf_url=pdf_url
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


@router.get(
    "/comic/{comic_id}",
    response_class=HTMLResponse
)
async def comic_preview(
    request: Request,
    comic_id: str
):

    comic = request.app.state.comics.get(
        comic_id
    )

    if not comic:

        raise HTTPException(
            status_code=404,
            detail="Comic not found."
        )

    return templates.TemplateResponse(
        request=request,
        name="comic_preview.html",
        context={
            "layout": comic["layout"],
            "comic_id": comic_id,
            "pdf_url": comic["pdf_url"]
        }
    )


@router.get(
    "/export/{comic_id}"
)
async def export_pdf(
    comic_id: str,
    request: Request
):

    comic = request.app.state.comics.get(
        comic_id
    )

    if not comic:

        raise HTTPException(
            status_code=404,
            detail="Comic not found."
        )

    filename = Path(
        comic["pdf_url"]
    ).name

    safe_path = (
        EXPORTS_DIR / filename
    )

    if not safe_path.exists():

        raise HTTPException(
            status_code=404,
            detail="PDF file not found."
        )

    return FileResponse(
        safe_path,
        media_type="application/pdf",
        filename=filename
    )


@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html"
    )


@router.post(
    "/test-image"
)
async def test_image(
    prompt: str = Form(...),
    art_style: str = Form("comic book")
):

    try:

        path = generate_image(
            prompt,
            1,
            art_style
        )

        return {
            "image_path": path
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc