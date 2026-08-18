from io import BytesIO
from random import Random
import re

from PIL import Image, ImageDraw, ImageFont

from .models import PixelSpec, SocialPost

PALETTES = {
    "sunset": ("#512b58", "#ff7b54", "#ffd56b", "#fff1d0", "#2f1b41"),
    "ocean": ("#16324f", "#2a9dbe", "#83d6de", "#f0fbff", "#102a43"),
    "forest": ("#183a2d", "#3d7a4e", "#8fbd69", "#f4efd3", "#24352a"),
    "candy": ("#8f5da2", "#ff8fab", "#ffc2d1", "#fff0f5", "#513252"),
    "midnight": ("#111936", "#293b76", "#8f9fea", "#f5e9a9", "#0a1025"),
    "mono": ("#292929", "#686868", "#b8b8b8", "#f4f4f4", "#161616"),
}


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    tokens = re.findall(r"[\u3400-\u9fff]|[^\s\u3400-\u9fff]+\s*", text.strip())
    lines: list[str] = []
    current = ""
    for token in tokens:
        candidate = f"{current}{token}"
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current.rstrip())
            current = token.lstrip()
        else:
            current = candidate
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current.rstrip())
    if len(lines) == max_lines and "".join(lines).replace(" ", "") != text.replace(" ", ""):
        suffix = "..."
        while lines[-1] and draw.textlength(f"{lines[-1]}{suffix}", font=font) > max_width:
            lines[-1] = lines[-1][:-1]
        lines[-1] = f"{lines[-1].rstrip()}{suffix}"
    return lines


def _pixel(draw: ImageDraw.ImageDraw, x: int, y: int, color: str, size: int = 12) -> None:
    draw.rectangle((x, y, x + size - 1, y + size - 1), fill=color)


def _draw_sky(draw: ImageDraw.ImageDraw, spec: PixelSpec, colors: tuple[str, ...], rng: Random) -> None:
    if spec.sky == "stars":
        for _ in range(24):
            _pixel(draw, rng.randrange(48, 540, 12), rng.randrange(55, 285, 12), colors[3], 6)
    elif spec.sky == "clouds":
        for x, y in ((100, 105), (350, 145)):
            for dx, dy in ((0, 12), (12, 0), (24, 0), (36, 12), (12, 12), (24, 12)):
                _pixel(draw, x + dx, y + dy, colors[3])
    elif spec.sky == "rain":
        for _ in range(20):
            x = rng.randrange(55, 540, 18)
            y = rng.randrange(70, 280, 24)
            draw.line((x, y, x - 8, y + 16), fill=colors[2], width=5)


def _draw_face(
    draw: ImageDraw.ImageDraw,
    center_x: int,
    center_y: int,
    ink: str,
    cheek: str,
    scale: int = 1,
) -> None:
    eye = 7 * scale
    draw.rectangle((center_x - 25 * scale, center_y - 8 * scale, center_x - 25 * scale + eye, center_y - 8 * scale + eye), fill=ink)
    draw.rectangle((center_x + 18 * scale, center_y - 8 * scale, center_x + 18 * scale + eye, center_y - 8 * scale + eye), fill=ink)
    draw.rectangle((center_x - 39 * scale, center_y + 8 * scale, center_x - 27 * scale, center_y + 14 * scale), fill=cheek)
    draw.rectangle((center_x + 27 * scale, center_y + 8 * scale, center_x + 39 * scale, center_y + 14 * scale), fill=cheek)
    draw.arc(
        (center_x - 17 * scale, center_y, center_x + 17 * scale, center_y + 25 * scale),
        10,
        170,
        fill=ink,
        width=4 * scale,
    )


def _draw_subject(draw: ImageDraw.ImageDraw, subject: str, colors: tuple[str, ...]) -> None:
    dark, mid, light, paper, ink = colors
    if subject in {"sun", "moon"}:
        fill = light if subject == "sun" else paper
        draw.ellipse((226, 105, 370, 249), fill=fill, outline=ink, width=8)
        if subject == "moon":
            draw.ellipse((276, 88, 396, 218), fill=dark)
            _draw_face(draw, 270, 172, ink, mid)
        else:
            _draw_face(draw, 298, 172, ink, mid)
    elif subject == "heart":
        draw.polygon(((298, 292), (218, 205), (218, 155), (258, 125), (298, 160), (338, 125), (378, 155), (378, 205)), fill=ink)
        for row, blocks in enumerate(((1, 2, 4, 5), (0, 1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5), (2, 3, 4), (3,))):
            for block in blocks:
                _pixel(draw, 244 + block * 18, 135 + row * 18, light, 18)
        _draw_face(draw, 298, 190, ink, mid)
    elif subject == "flower":
        draw.line((298, 180, 298, 330), fill=ink, width=12)
        for box in ((250, 130, 298, 178), (298, 130, 346, 178), (274, 105, 322, 153), (274, 155, 322, 203)):
            draw.rectangle(box, fill=light, outline=ink, width=6)
        draw.rectangle((276, 132, 320, 176), fill=paper, outline=ink, width=5)
        _draw_face(draw, 298, 153, ink, mid)
    elif subject == "coffee":
        draw.rectangle((220, 175, 350, 295), fill=paper, outline=ink, width=8)
        draw.rectangle((350, 200, 390, 265), outline=ink, width=16)
        draw.rectangle((350, 208, 382, 257), outline=paper, width=8)
        draw.rectangle((236, 190, 334, 220), fill=ink)
        for x in (260, 305):
            draw.line((x, 165, x + 8, 125), fill=paper, width=7)
        _draw_face(draw, 286, 252, ink, mid)
    elif subject == "cat":
        draw.rectangle((245, 145, 350, 285), fill=mid, outline=ink, width=8)
        draw.polygon(((245, 145), (260, 95), (290, 145)), fill=mid, outline=ink)
        draw.polygon(((305, 145), (340, 95), (350, 145)), fill=mid, outline=ink)
        _draw_face(draw, 298, 202, ink, light)
        draw.line((248, 225, 205, 215), fill=paper, width=4)
        draw.line((248, 238, 202, 242), fill=paper, width=4)
        draw.line((348, 225, 392, 215), fill=paper, width=4)
        draw.line((348, 238, 395, 242), fill=paper, width=4)
    elif subject == "mountain":
        draw.polygon(((65, 335), (230, 120), (370, 335)), fill=mid, outline=ink)
        draw.polygon(((230, 120), (180, 185), (245, 170), (275, 210), (300, 195)), fill=paper)
        draw.polygon(((250, 335), (410, 170), (535, 335)), fill=light, outline=ink)
        _draw_face(draw, 230, 258, ink, light)
    elif subject == "city":
        for x, top, width in ((80, 180, 80), (170, 125, 105), (285, 205, 70), (365, 145, 115), (490, 225, 55)):
            draw.rectangle((x, top, x + width, 340), fill=ink, outline=paper, width=5)
            for wx in range(x + 14, x + width - 8, 24):
                for wy in range(top + 20, 325, 30):
                    _pixel(draw, wx, wy, light, 8)
        _draw_face(draw, 222, 280, paper, mid)
    elif subject == "wave":
        for offset in range(0, 150, 24):
            draw.arc((90 + offset, 150, 310 + offset, 360), 195, 345, fill=paper, width=16)
        _draw_face(draw, 330, 285, ink, light)


def _draw_accents(draw: ImageDraw.ImageDraw, accent: str, colors: tuple[str, ...], rng: Random) -> None:
    if accent == "none":
        return
    for _ in range(10):
        x, y = rng.randrange(70, 515, 12), rng.randrange(75, 315, 12)
        if accent == "sparkles":
            draw.line((x - 7, y, x + 7, y), fill=colors[3], width=3)
            draw.line((x, y - 7, x, y + 7), fill=colors[3], width=3)
        elif accent == "birds":
            draw.arc((x - 12, y, x, y + 10), 190, 350, fill=colors[4], width=3)
            draw.arc((x, y, x + 12, y + 10), 190, 350, fill=colors[4], width=3)
        elif accent == "music":
            draw.text((x, y), "♪", fill=colors[3], font=_font(20))
        elif accent == "leaves":
            draw.ellipse((x, y, x + 12, y + 7), fill=colors[2])
        elif accent == "bubbles":
            draw.ellipse((x, y, x + 12, y + 12), outline=colors[3], width=3)


def _pixelate_scene(image: Image.Image) -> None:
    scene_box = (52, 52, 588, 500)
    scene = image.crop(scene_box)
    low_resolution = scene.resize((67, 56), Image.Resampling.BOX)
    pixel_art = low_resolution.resize((536, 448), Image.Resampling.NEAREST)
    image.paste(pixel_art, scene_box[:2])


def render_polaroid(spec: PixelSpec, post: SocialPost, emoji: str, mood: str) -> bytes:
    colors = PALETTES[spec.palette]
    rng = Random(f"{emoji}:{mood}:{spec.title}")
    image = Image.new("RGB", (640, 980), "#ede8df")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 24, 612, 952), radius=12, fill="#fffdf8")
    draw.rectangle((52, 52, 588, 500), fill=colors[0])
    draw.rectangle((52, 330, 588, 500), fill=colors[1])
    _draw_sky(draw, spec, colors, rng)
    _draw_subject(draw, spec.subject, colors)
    _draw_accents(draw, spec.accent, colors, rng)
    _pixelate_scene(image)

    title_font = _font(34, bold=True)
    caption_font = _font(22)
    hashtag_font = _font(20, bold=True)
    meta_font = _font(18, bold=True)
    draw.text((72, 535), spec.title[:26], fill=colors[4], font=title_font)
    y = 592
    for line in _wrap_text(draw, post.caption, caption_font, 496, 7):
        draw.text((72, y), line, fill="#55504a", font=caption_font)
        y += 34

    y += 8
    hashtag_x = 72
    for hashtag in post.hashtags:
        tag_width = draw.textlength(hashtag, font=hashtag_font)
        if hashtag_x > 72 and hashtag_x + tag_width > 568:
            hashtag_x = 72
            y += 31
        draw.text((hashtag_x, y), hashtag, fill=colors[0], font=hashtag_font)
        hashtag_x += int(tag_width) + 18

    draw.line((72, 890, 568, 890), fill="#ded6cf", width=2)
    draw.text((72, 907), mood.upper(), fill="#8a8179", font=meta_font)
    draw.text((430, 907), "MOODFRAME", fill="#8a8179", font=meta_font)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
