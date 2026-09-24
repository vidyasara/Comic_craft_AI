from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import (
    STATIC_DIR,
    get_settings
)

from app.routes import router


settings = get_settings()


app = FastAPI(
    title=settings.app_name,

    description=(
        "AI comic story creator "
        "using Gemini and Stable Diffusion."
    ),

    version="1.0.0"
)


app.state.comics = {}


app.mount(
    "/static",
    StaticFiles(
        directory=str(STATIC_DIR)
    ),
    name="static"
)


app.include_router(router)