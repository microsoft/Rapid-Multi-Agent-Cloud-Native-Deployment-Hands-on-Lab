from io import BytesIO

from PIL import Image

from backend.app.models import PixelSpec, SocialPost
from backend.app.renderer import render_polaroid


def test_renderer_returns_png() -> None:
    spec = PixelSpec(
        title="Sunny Pause",
        palette="sunset",
        sky="clouds",
        subject="coffee",
        accent="sparkles",
        caption_line="sip the good light",
    )
    post = SocialPost(
        caption="今天的阳光刚刚好，把每一个小小的快乐都收藏进这张拍立得。",
        hashtags=["#今日心情", "#像素生活", "#快乐收藏"],
        visual_hook="阳光下的一杯咖啡",
    )
    image = render_polaroid(spec, post, "😊", "joyful")
    assert image.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(image) > 5_000

    rendered = Image.open(BytesIO(image))
    scene = rendered.crop((52, 52, 588, 500))
    for x, y in ((0, 0), (80, 80), (264, 200), (520, 432)):
        assert len(set(scene.crop((x, y, x + 8, y + 8)).getdata())) == 1
