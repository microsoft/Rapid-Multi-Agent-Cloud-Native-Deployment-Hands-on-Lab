from typing import Literal

from pydantic import BaseModel, Field

MoodName = Literal["joyful", "calm", "loved", "dreamy", "energetic", "cozy"]


class GenerateRequest(BaseModel):
    emoji: str = Field(min_length=1, max_length=8)
    mood: MoodName
    language: Literal["en", "zh"] = "en"


class SocialPost(BaseModel):
    caption: str
    hashtags: list[str] = Field(min_length=3, max_length=3)
    visual_hook: str


class PixelSpec(BaseModel):
    title: str
    palette: Literal["sunset", "ocean", "forest", "candy", "midnight", "mono"]
    sky: Literal["clear", "clouds", "stars", "rain"]
    subject: Literal["sun", "moon", "flower", "heart", "coffee", "cat", "mountain", "city", "wave"]
    accent: Literal["sparkles", "birds", "music", "leaves", "bubbles", "none"]
    caption_line: str = Field(max_length=24)


class GenerateResponse(BaseModel):
    emoji: str
    mood: MoodName
    post: SocialPost
    art: PixelSpec
    image_url: str
    download_url: str

