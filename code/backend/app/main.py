import os
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .a2a_client import run_remote_agent
from .models import GenerateRequest, GenerateResponse, PixelSpec, SocialPost
from .renderer import render_polaroid

CONTENT_AGENT_URL = os.getenv("CONTENT_AGENT_URL", "http://localhost:5001")
IMAGE_AGENT_URL = os.getenv("IMAGE_AGENT_URL", "http://localhost:5002")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "generated"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="MoodFrame API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    try:
        post = await run_remote_agent(
            CONTENT_AGENT_URL,
            request.model_dump(),
            SocialPost,
        )
        art = await run_remote_agent(
            IMAGE_AGENT_URL,
            {
                **request.model_dump(),
                **post.model_dump(),
            },
            PixelSpec,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    image_id = uuid.uuid4().hex
    image_path = OUTPUT_DIR / f"{image_id}.png"
    image_path.write_bytes(render_polaroid(art, post, request.emoji, request.mood))
    image_url = f"/api/images/{image_id}.png"
    return GenerateResponse(
        emoji=request.emoji,
        mood=request.mood,
        post=post,
        art=art,
        image_url=image_url,
        download_url=f"/api/downloads/moodframe-{image_id}.png",
    )


@app.get("/api/images/{image_name}")
async def image(image_name: str) -> FileResponse:
    safe_name = Path(image_name).name
    if safe_name != image_name or not safe_name.endswith(".png"):
        raise HTTPException(status_code=400, detail="Invalid image name")
    image_path = OUTPUT_DIR / safe_name
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(
        image_path,
        media_type="image/png",
        content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@app.get("/api/downloads/moodframe-{image_id}.png")
async def download_image(image_id: str) -> FileResponse:
    try:
        safe_id = uuid.UUID(image_id).hex
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid image id") from exc
    if safe_id != image_id:
        raise HTTPException(status_code=400, detail="Invalid image id")

    image_path = OUTPUT_DIR / f"{safe_id}.png"
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(
        image_path,
        media_type="image/png",
        filename=f"moodframe-{safe_id}.png",
        content_disposition_type="attachment",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
