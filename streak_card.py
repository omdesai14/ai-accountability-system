"""Generate a shareable streak card as a PNG image."""
from io import BytesIO
from datetime import date

from PIL import Image, ImageDraw, ImageFont


CARD_W, CARD_H = 1080, 1350  # Instagram portrait

BG_TOP = (10, 10, 12)
BG_BOTTOM = (22, 18, 38)
ACCENT_VIOLET = (178, 156, 255)
ACCENT_ROSE = (255, 111, 145)
ACCENT_AMBER = (245, 166, 35)
ACCENT_EMERALD = (74, 222, 128)
INK = (255, 255, 255)
INK_DIM = (174, 176, 182)
INK_FAINT = (104, 107, 115)


_FONT_CANDIDATES_REGULAR = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
_FONT_CANDIDATES_BOLD = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
_FONT_CANDIDATES_ITALIC = [
    "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
    "/Library/Fonts/Georgia Italic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
]


def _load_font(size, weight="regular"):
    paths = {
        "regular": _FONT_CANDIDATES_REGULAR,
        "bold":    _FONT_CANDIDATES_BOLD,
        "italic":  _FONT_CANDIDATES_ITALIC,
    }[weight]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _medal_for_streak(streak: int):
    """Return (emoji-ish symbol, label, accent-color) for the streak tier."""
    if streak >= 100:
        return ("◆", "DIAMOND", (175, 220, 255))
    if streak >= 30:
        return ("●", "GOLD",     ACCENT_AMBER)
    if streak >= 14:
        return ("●", "SILVER",   (200, 205, 215))
    if streak >= 7:
        return ("●", "BRONZE",   (205, 127, 50))
    return ("●", "STARTER", ACCENT_VIOLET)


def _draw_gradient_bg(img):
    """Vertical gradient from BG_TOP to BG_BOTTOM."""
    pixels = img.load()
    for y in range(CARD_H):
        t = y / CARD_H
        r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
        for x in range(CARD_W):
            pixels[x, y] = (r, g, b)


def _draw_radial_glow(img, center, radius, color, alpha=140):
    """Soft glow disc behind the streak number."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    steps = 28
    for i in range(steps, 0, -1):
        a = int(alpha * (i / steps) ** 2)
        r = int(radius * (i / steps))
        draw.ellipse(
            (center[0] - r, center[1] - r, center[0] + r, center[1] + r),
            fill=(color[0], color[1], color[2], a),
        )
    img.alpha_composite(overlay)


def _text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def generate_streak_card_png(username: str, streak: int, goal_title: str) -> bytes:
    """Compose a 1080x1350 streak card PNG and return its bytes."""
    img = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 255))
    _draw_gradient_bg(img)

    medal_glyph, tier_label, tier_color = _medal_for_streak(streak)

    # Soft accent glow behind the number
    _draw_radial_glow(img, (CARD_W // 2, 700), 520, tier_color, alpha=110)

    draw = ImageDraw.Draw(img)

    # ─ Header eyebrow ────────────────────────────
    eyebrow = "ZEROSKIP  ·  DON'T BREAK THE STREAK"
    f_eye = _load_font(26, "bold")
    w, _ = _text_size(draw, eyebrow, f_eye)
    draw.text(((CARD_W - w) // 2, 110), eyebrow, font=f_eye, fill=INK_FAINT)

    # ─ Small medal pill at top ───────────────────
    f_tier = _load_font(28, "bold")
    tier_text = f"{tier_label} STREAK"
    tw, th = _text_size(draw, tier_text, f_tier)
    pill_pad_x, pill_pad_y = 26, 14
    pill_w = tw + pill_pad_x * 2 + 36
    pill_x = (CARD_W - pill_w) // 2
    pill_y = 250
    draw.rounded_rectangle(
        (pill_x, pill_y, pill_x + pill_w, pill_y + th + pill_pad_y * 2),
        radius=40,
        fill=(255, 255, 255, 18),
        outline=tier_color,
        width=2,
    )
    # dot inside the pill
    dot_r = 9
    dot_cx = pill_x + pill_pad_x + dot_r
    dot_cy = pill_y + (th + pill_pad_y * 2) // 2
    draw.ellipse(
        (dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r),
        fill=tier_color,
    )
    draw.text(
        (dot_cx + dot_r + 14, pill_y + pill_pad_y - 2),
        tier_text,
        font=f_tier,
        fill=tier_color,
    )

    # ─ Huge streak number ────────────────────────
    f_num = _load_font(360, "bold")
    num_text = str(streak)
    w, h = _text_size(draw, num_text, f_num)
    num_x = (CARD_W - w) // 2
    num_y = 430
    draw.text((num_x + 4, num_y + 4), num_text, font=f_num, fill=(0, 0, 0))
    draw.text((num_x, num_y), num_text, font=f_num, fill=INK)

    # ─ "DAYS" caption (well below the number) ────
    f_days = _load_font(46, "bold")
    days_label = "DAYS" if streak != 1 else "DAY"
    w, _ = _text_size(draw, days_label, f_days)
    draw.text(((CARD_W - w) // 2, 880), days_label, font=f_days, fill=INK_DIM)

    # ─ Italic tagline ────────────────────────────
    f_italic = _load_font(54, "italic")
    tagline = "I showed up."
    w, _ = _text_size(draw, tagline, f_italic)
    draw.text(((CARD_W - w) // 2, 1010), tagline, font=f_italic, fill=INK)

    # ─ Goal title (truncated if long) ────────────
    f_goal = _load_font(28, "regular")
    goal_text = goal_title.strip()
    if len(goal_text) > 42:
        goal_text = goal_text[:40].rstrip() + "…"
    goal_text = f"on  ·  {goal_text}"
    w, _ = _text_size(draw, goal_text, f_goal)
    draw.text(((CARD_W - w) // 2, 1095), goal_text, font=f_goal, fill=INK_DIM)

    # ─ Footer: username + date ───────────────────
    f_footer = _load_font(24, "bold")
    footer = f"@{username}   ·   {date.today().isoformat()}"
    w, _ = _text_size(draw, footer, f_footer)
    draw.text(((CARD_W - w) // 2, 1215), footer, font=f_footer, fill=INK_FAINT)

    # ─ Decorative top/bottom rules ───────────────
    rule_color = (60, 62, 70, 255)
    draw.rectangle((100, 80, CARD_W - 100, 82), fill=rule_color)
    draw.rectangle((100, CARD_H - 80, CARD_W - 100, CARD_H - 78), fill=rule_color)

    out = BytesIO()
    img.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()
