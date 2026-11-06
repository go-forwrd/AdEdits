"""Designed on-screen graphics for ads: CTA buttons, price/badge pills, star
ratings, and a progress bar. Each is a Pillow PNG composited via FFmpeg overlay
at a timed position. Brand-consistent (Inter + #EA6024), placed in safe zones.

EDP `overlays` entries (composited in a final pass over the finished video):
  {"type": "cta",      "text": "PRE-ORDER NOW", "start": 12, "end": 18, "position": "lower"}
  {"type": "badge",    "text": "SAVE $10",      "start": 0,  "end": 18, "position": "top-right"}
  {"type": "stars",    "rating": 4.6, "text": "4.6 from real players", "start": 2, "end": 7, "position": "upper"}
  {"type": "progress", "start": 0, "end": null}
  {"type": "photo",    "path": "still.jpg", "start": 3.2, "end": 4.4, "size_frac": 0.6, "bottom_frac": 0.66}
  {"type": "index",    "num": "01", "text": "Waterproof shell", "sub": "Recycled nylon", "start": 2, "end": 3.4, "left_frac": 0.06, "bottom_frac": 0.76}
  {"type": "review",   "text": "Exactly what I needed...", "name": "J.D.", "start": 2, "end": 5, "top_frac": 0.3}
cta / badge / stars accept an optional "font" (project-relative path) for their text.
"""
from __future__ import annotations

import math
from pathlib import Path

from .captions import _load_font


def _orange(cfg) -> str:
    return cfg.captions.get("highlight", "#EA6024")


def _font_path(cfg):
    f = cfg.captions.get("font")
    if f and f != "auto" and not Path(f).is_absolute():
        f = str(cfg.root / f)
    return f


def _with_shadow(img, *, blur=6, alpha=150, offset=(0, 3)):
    """Return a copy of an RGBA image with a soft drop shadow behind it — reads far more
    premium than a hard black stroke, and lifts white art off any background."""
    from PIL import Image, ImageFilter
    ox, oy = offset
    pad = blur * 3 + max(abs(ox), abs(oy))
    canvas = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    # shadow = the art's own alpha, darkened and blurred
    a = img.split()[-1].point(lambda v: int(v * alpha / 255))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 255), (pad + ox, pad + oy), a)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(img, (pad, pad))
    return canvas


def _star(draw, cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def _cta(text, fw, cfg, font_p):
    from PIL import Image, ImageDraw
    size = int(fw * 0.052)
    font = _load_font(font_p, size, "ExtraBold")
    pad_x, pad_y = int(size * 1.1), int(size * 0.6)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    txt = text.upper()
    bb = tmp.textbbox((0, 0), txt, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w, h = tw + 2 * pad_x, th + 2 * pad_y
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=_orange(cfg))
    d.text((pad_x - bb[0], pad_y - bb[1]), txt, font=font, fill="#FFFFFF")
    return img


def _badge(text, fw, cfg, font_p):
    from PIL import Image, ImageDraw
    size = int(fw * 0.040)
    font = _load_font(font_p, size, "Bold")
    pad_x, pad_y = int(size * 0.7), int(size * 0.45)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    txt = text.upper()
    bb = tmp.textbbox((0, 0), txt, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w, h = tw + 2 * pad_x, th + 2 * pad_y
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill="#111111")
    d.text((pad_x - bb[0], pad_y - bb[1]), txt, font=font, fill=_orange(cfg))
    return img


def _stars(rating, text, fw, cfg, font_p, *, stroke=True):
    from PIL import Image, ImageDraw
    sr = int(fw * 0.020)              # star radius
    gap = int(sr * 0.5)
    n = 5
    stars_w = n * (2 * sr) + (n - 1) * gap
    size = int(fw * 0.034)
    font = _load_font(font_p, size, "Bold") if text else None
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = (tmp.textbbox((0, 0), text.upper(), font=font)[2] if text else 0)
    pad = int(sr * 0.8)
    w = stars_w + (int(sr * 0.8) + tw if text else 0) + 2 * pad
    h = 2 * sr + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = pad + sr
    for _ in range(n):
        _star(d, cx, h / 2, sr, _orange(cfg))
        cx += 2 * sr + gap
    if text:
        bb = tmp.textbbox((0, 0), text.upper(), font=font)
        d.text((stars_w + pad + int(sr * 0.8), (h - (bb[3] - bb[1])) / 2 - bb[1]),
               text.upper(), font=font, fill="#FFFFFF",
               stroke_width=max(1, size // 12) if stroke else 0, stroke_fill="#000000")
    # a keyline swamps thin body faces; give them the soft drop shadow instead
    return img if stroke else _with_shadow(img, blur=max(2, size // 8), alpha=170, offset=(0, 2))


def _callout(text, fw, cfg, font_p, *, size_frac=0.055, max_width_frac=0.86,
             emphasis_style="color", upper=True, weight="Black"):
    """Big bold ad callout headline: all-caps Inter Black, white with one optional
    orange 'hot' word (mark it *like_this*), heavy black stroke for legibility over
    footage, word-wrapped and centered. Returns a tight PNG (positioned by caller).

    ``size_frac``/``max_width_frac`` are fractions of frame width. Sound-off placements
    (Meta) want a bigger, tighter-wrapping headline than the 0.055 default."""
    from PIL import Image, ImageDraw
    size = int(fw * size_frac)
    font = _load_font(font_p, size, weight)
    orange = _orange(cfg)
    toks = []
    for w in (text.upper() if upper else text).split():
        # A word is the orange "hot" word if it carries emphasis asterisks. Detect by
        # presence of '*' (not exact *WORD* bracketing) so punctuation glued to the marker
        # — "*DID*." , "(*NEW*)" — still resolves, and strip every '*' from what we draw.
        hot = "*" in w
        toks.append((w.replace("*", ""), hot))
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    space = tmp.textlength(" ", font=font)
    maxw = int(fw * max_width_frac)
    lines, cur, curw = [], [], 0.0
    for word, hot in toks:
        ww = tmp.textlength(word, font=font)
        add = ww + (space if cur else 0)
        if cur and curw + add > maxw:
            lines.append(cur)
            cur, curw = [(word, hot, ww)], ww
        else:
            cur.append((word, hot, ww))
            curw += add
    if cur:
        lines.append(cur)
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * 1.05)
    line_ws = [sum(w for _, _, w in ln) + space * (len(ln) - 1) for ln in lines]
    # Premium treatment: a hairline stroke for edge definition plus a soft drop shadow,
    # instead of the chunky black outline that reads as loud novelty-merch. The shadow is
    # added after the text is drawn, so legibility holds over busy footage without the
    # heavy keyline.
    stroke = max(1, size // 34)
    pad = int(size * 0.5)
    blockw = int(max(line_ws)) if line_ws else 1
    blockh = lh * len(lines)
    img = Image.new("RGBA", (blockw + 2 * pad, blockh + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # "chip": the emphasis word sits in a rounded orange pill with white text. This reads on
    # ANY background — essential for a color-block set where a beat's background is itself the
    # brand orange (plain orange text would vanish). "color" keeps the classic orange word.
    chip = emphasis_style == "chip"
    cpx, cpy = int(size * 0.20), int(size * 0.08)   # chip inner padding
    y = pad
    for ln, lw in zip(lines, line_ws):
        x = pad + (blockw - lw) / 2
        for word, hot, ww in ln:
            if hot and chip:
                asc_h = font.getmetrics()[0]
                x0, y0 = x - cpx, y + int(size * 0.02)
                x1, y1 = x + ww + cpx, y + asc_h + cpy
                d.rounded_rectangle([x0, y0, x1, y1], radius=int(size * 0.16), fill=orange)
                d.text((x, y), word, font=font, fill="#FFFFFF",
                       stroke_width=stroke, stroke_fill=orange)
            elif hot and emphasis_style == "strike":
                # "strike": the emphasis word stays white, crossed out with a thick orange bar
                # (a "skip this" list).
                d.text((x, y), word, font=font, fill="#FFFFFF", stroke_width=stroke, stroke_fill="#FFFFFF")
                asc_h = font.getmetrics()[0]
                bar = max(4, size // 9)
                my = y + int(asc_h * 0.58)
                d.rounded_rectangle([x - size * 0.08, my - bar // 2, x + ww + size * 0.08, my + bar // 2],
                                    radius=bar // 2, fill=orange)
            else:
                d.text((x, y), word, font=font, fill=(orange if hot else "#FFFFFF"),
                       stroke_width=stroke, stroke_fill=(orange if hot else "#FFFFFF"))
            x += ww + space
        y += lh
    return _with_shadow(img, blur=max(3, size // 12), alpha=135,
                        offset=(0, max(2, size // 22)))


def _body_font_path(ov, cfg, font_p):
    p = ov.get("font")
    if p and not Path(p).is_absolute():
        p = str(cfg.root / p)
    return p or font_p


def _checklist(ov, fw, cfg, font_p):
    """Spec checklist card: Inter Black title, DM Sans rows, the first ``checked`` rows
    with a filled orange box + white tick. Dark translucent card with a soft shadow."""
    from PIL import Image, ImageDraw
    w = int(fw * float(ov.get("width_frac", 0.84)))
    size = int(fw * float(ov.get("size_frac", 0.045)))
    title_f = _load_font(font_p, int(size * 1.15), "Black")
    row_f = _load_font(_body_font_path(ov, cfg, font_p), size, "Regular")
    items, checked = ov["items"], int(ov.get("checked", 0))
    pad, row_h, box = int(size * 0.9), int(size * 1.75), int(size * 1.05)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tb = tmp.textbbox((0, 0), ov.get("title", "").upper(), font=title_f)
    title_h = tb[3] - tb[1]
    h = pad + title_h + int(size * 0.9) + row_h * len(items) + pad - int(size * 0.5)
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(size * 0.6), fill=(17, 17, 17, 214))
    d.text((pad - tb[0], pad - tb[1]), ov.get("title", "").upper(), font=title_f, fill="#FFFFFF")
    y = pad + title_h + int(size * 0.9)
    orange = _orange(cfg)
    for k, item in enumerate(items):
        by = y + (row_h - box) // 2 - int(size * 0.25)
        on = k < checked
        d.rounded_rectangle([pad, by, pad + box, by + box], radius=max(3, box // 5),
                            fill=orange if on else None, outline=orange if on else "#FFFFFF",
                            width=max(2, box // 12))
        if on:
            lw = max(3, box // 7)
            d.line([(pad + box * 0.22, by + box * 0.52), (pad + box * 0.43, by + box * 0.73),
                    (pad + box * 0.80, by + box * 0.28)], fill="#FFFFFF", width=lw, joint="curve")
        rb = tmp.textbbox((0, 0), item, font=row_f)
        d.text((pad + box + int(size * 0.7) - rb[0], by + (box - (rb[3] - rb[1])) // 2 - rb[1]), item,
               font=row_f, fill="#FFFFFF" if on else (255, 255, 255, 170))
        y += row_h
    return _with_shadow(card, blur=max(6, size // 4), alpha=120, offset=(0, 4))


def _textbox(ov, fw, cfg, font_p):
    """Native short-form text style: each line in its own white rounded box, black text,
    centred and stacked (``lines``: list of str)."""
    from PIL import Image, ImageDraw
    size = int(fw * float(ov.get("size_frac", 0.052)))
    f = _load_font(_body_font_path(ov, cfg, font_p), size, ov.get("weight", "Regular"))
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    asc, desc = f.getmetrics()
    px, py = int(size * 0.45), int(size * 0.28)
    rows = [(ln, tmp.textlength(ln, font=f)) for ln in ov["lines"]]
    lh = asc + desc + 2 * py
    gap = int(size * float(ov.get("gap_frac", 0)))   # space between boxes, as a fraction of text size
    step = lh + gap
    w = int(max(r[1] for r in rows)) + 2 * px
    img = Image.new("RGBA", (w, step * len(rows) - gap), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # "accent_from": lines from this index on are drawn as the answer, a brand-orange box with
    # white text, so a worry/question (white box) reads apart from its answer.
    acc = ov.get("accent_from")
    for k, (ln, tw) in enumerate(rows):
        x0 = int((w - tw) / 2) - px
        is_acc = acc is not None and k >= int(acc)
        bg = _orange(cfg) if is_acc else ov.get("bg", "#FFFFFF")
        fg = "#FFFFFF" if is_acc else ov.get("color", "#000000")
        d.rounded_rectangle([x0, k * step, x0 + int(tw) + 2 * px, k * step + lh - 1],
                            radius=int(size * 0.3), fill=bg)
        d.text((x0 + px, k * step + py), ln, font=f, fill=fg)
    return img


def _review_card(ov, fw, cfg, font_p):
    """Customer review card: white rounded card, five orange stars, the quote in the body face
    (wrapped, in curly quotes) and the reviewer's name underneath. Keys: text, name, rating (5),
    width_frac (0.82), size_frac (0.046), font. Quotes are real customer words: pass them verbatim."""
    from PIL import Image, ImageDraw
    size = int(fw * float(ov.get("size_frac", 0.046)))
    body = _load_font(_body_font_path(ov, cfg, font_p), size, "Regular")
    name_f = _load_font(_body_font_path(ov, cfg, font_p), int(size * 0.74), "Regular")
    pad = int(size * 0.85)
    w = int(fw * float(ov.get("width_frac", 0.82)))
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    words, lines, cur = f"\u201c{ov['text']}\u201d".split(), [], ""
    for wd in words:
        trial = f"{cur} {wd}".strip()
        if cur and tmp.textlength(trial, font=body) > w - 2 * pad:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    if cur:
        lines.append(cur)
    asc, desc = body.getmetrics()
    lh = int((asc + desc) * 1.18)
    sr = int(size * 0.42)
    star_h = 2 * sr
    name = ov.get("name")
    name_h = int(size * 0.74 * 1.3) if name else 0
    h = pad + star_h + int(size * 0.55) + lh * len(lines) + (int(size * 0.4) + name_h if name else 0) + pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(size * 0.6), fill=ov.get("bg", "#FFFFFF"))
    cx = pad + sr
    for _ in range(int(ov.get("rating", 5))):
        _star(d, cx, pad + sr, sr, _orange(cfg))
        cx += 2 * sr + int(sr * 0.45)
    y = pad + star_h + int(size * 0.55)
    for ln in lines:
        d.text((pad, y), ln, font=body, fill=ov.get("color", "#111111"))
        y += lh
    if name:
        d.text((pad, y + int(size * 0.4)), f"\u2014 {name}", font=name_f, fill="#5A5A5A")
    if ov.get("rotate"):
        img = img.rotate(float(ov["rotate"]), resample=Image.BICUBIC, expand=True)
    return _with_shadow(img, blur=max(4, size // 6), alpha=120, offset=(0, max(2, size // 14)))


def _chat(ov, fw, cfg, font_p):
    """Text-message thread: ``messages`` is a list of (side, text), side "l" (them: light grey
    bubble, dark text) or "r" (you: brand-orange bubble, white text). Bubbles wrap at 70% of
    the thread width and stack with a small gap; the newest is at the bottom. Optional
    ``header`` (contact name) above the thread in small grey type."""
    from PIL import Image, ImageDraw
    size = int(fw * float(ov.get("size_frac", 0.046)))
    f = _load_font(_body_font_path(ov, cfg, font_p), size, "Regular")
    w = int(fw * float(ov.get("width_frac", 0.86)))
    maxw = int(w * 0.72)
    px, py = int(size * 0.6), int(size * 0.38)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 1.08)
    bubbles = []
    for side, text in ov["messages"]:
        words, lines, cur = text.split(), [], ""
        for wd in words:
            trial = f"{cur} {wd}".strip()
            if cur and tmp.textlength(trial, font=f) > maxw - 2 * px:
                lines.append(cur)
                cur = wd
            else:
                cur = trial
        lines.append(cur)
        bw = int(max(tmp.textlength(ln, font=f) for ln in lines)) + 2 * px
        bh = lh * len(lines) + 2 * py - (lh - asc - desc)
        bubbles.append((side, lines, bw, bh))
    gap = int(size * 0.32)
    head = ov.get("header")
    hf = _load_font(_body_font_path(ov, cfg, font_p), int(size * 0.8), "Regular") if head else None
    head_h = int(size * 0.8 * 1.6) if head else 0
    h = head_h + sum(b[3] for b in bubbles) + gap * (len(bubbles) - 1)
    img = Image.new("RGBA", (w, max(1, h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if head:
        tw = tmp.textlength(head, font=hf)
        d.text(((w - tw) / 2, 0), head, font=hf, fill="#FFFFFF")
    y = head_h
    for side, lines, bw, bh in bubbles:
        right = side == "r"
        x0 = w - bw if right else 0
        bg = _orange(cfg) if right else "#ECECEE"
        fg = "#FFFFFF" if right else "#111111"
        d.rounded_rectangle([x0, y, x0 + bw - 1, y + bh - 1], radius=int(size * 0.75), fill=bg)
        ty = y + py
        for ln in lines:
            d.text((x0 + px, ty), ln, font=f, fill=fg)
            ty += lh
        y += bh + gap
    return _with_shadow(img, blur=max(4, size // 6), alpha=110, offset=(0, max(2, size // 14)))


def _calendar(ov, fw, cfg, font_p):
    """Tear-off calendar tile: white rounded page with a brand-orange band carrying the month
    ("DEC") and a big black day ("25"), then a white Inter Black headline (one *hot* orange
    word allowed) and an optional DM Sans subline, centred under the tile."""
    from PIL import Image, ImageDraw
    size = int(fw * float(ov.get("size_frac", 0.07)))
    tile = int(size * 3.0)
    band = int(tile * 0.30)
    mon_f = _load_font(font_p, int(band * 0.62), "Black")
    day_f = _load_font(font_p, int(tile * 0.52), "Black")
    t = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    rad = int(tile * 0.12)
    d.rounded_rectangle([0, 0, tile - 1, tile - 1], radius=rad, fill="#FFFFFF")
    d.rounded_rectangle([0, 0, tile - 1, band + rad], radius=rad, fill=_orange(cfg))
    d.rectangle([0, band, tile - 1, band + rad], fill="#FFFFFF")
    for txt, f, y0, y1, col in ((ov["month"].upper(), mon_f, 0, band, "#FFFFFF"),
                                (str(ov["day"]), day_f, band, tile, "#111111")):
        bb = d.textbbox((0, 0), txt, font=f)
        d.text(((tile - (bb[2] - bb[0])) / 2 - bb[0], y0 + (y1 - y0 - (bb[3] - bb[1])) / 2 - bb[1]), txt,
               font=f, fill=col)
    parts = [_with_shadow(t, blur=max(4, size // 6), alpha=130, offset=(0, 4))]
    if ov.get("text"):
        parts.append(_callout(ov["text"], fw, cfg, font_p, size_frac=float(ov.get("text_frac", 0.075)),
                              max_width_frac=0.86))
    if ov.get("sub"):
        parts.append(_callout(ov["sub"], fw, cfg, _body_font_path(ov, cfg, font_p),
                              size_frac=float(ov.get("sub_frac", 0.04)), max_width_frac=0.84,
                              upper=False, weight="Regular"))
    gap = int(size * 0.15)
    w = max(p.width for p in parts)
    h = sum(p.height for p in parts) + gap * (len(parts) - 1)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for p in parts:
        img.alpha_composite(p, ((w - p.width) // 2, y))
        y += p.height + gap
    return img


def _index_label(ov, fw, cfg, font_p):
    """Left-aligned "parts index" label: a big orange number ("01"), a white Inter Black
    name under it, an optional DM Sans subline, all on a soft shadow (no keyline)."""
    from PIL import Image, ImageDraw
    size = int(fw * float(ov.get("size_frac", 0.07)))
    num_f = _load_font(font_p, int(size * 1.5), "Black")
    name_f = _load_font(font_p, size, "Black")
    sub_p = ov.get("font")
    if sub_p and not Path(sub_p).is_absolute():
        sub_p = str(cfg.root / sub_p)
    sub_f = _load_font(sub_p or font_p, int(size * 0.56), "Regular") if ov.get("sub") else None
    rows = [(str(ov.get("num", "")), num_f, _orange(cfg)), (ov["text"].upper(), name_f, "#FFFFFF")]
    if sub_f:
        rows.append((ov["sub"], sub_f, "#FFFFFF"))
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    boxes = [tmp.textbbox((0, 0), t, font=f) if t else (0, 0, 0, 0) for t, f, _ in rows]
    gaps = [0, int(size * 0.22), int(size * 0.38)]
    w = max(b[2] - b[0] for b in boxes) + 4
    h = sum(b[3] - b[1] for b in boxes) + sum(gaps[1:len(rows)])
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 0
    for k, ((t, f, col), b) in enumerate(zip(rows, boxes)):
        y += gaps[k] if k else 0
        if t:
            d.text((-b[0], y - b[1]), t, font=f, fill=col)
        y += b[3] - b[1]
    return _with_shadow(img, blur=max(4, size // 6), alpha=190, offset=(0, 3))


def feature_callout(text, frame_size, cfg, *, position="lower-left", subtext=None):
    """Premium landing-page feature label: clean white chip + dark text + the brand
    accent color. Returns a full-frame RGBA PNG (overlay at 0:0)."""
    from PIL import Image, ImageDraw
    fw, fh = frame_size
    font_p = _font_path(cfg)
    size = max(22, int(fh * 0.040))
    font = _load_font(font_p, size, "Bold")
    sub_font = _load_font(font_p, int(size * 0.62), "Medium") if subtext else None
    txt = text.upper()

    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = tmp.textbbox((0, 0), txt, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    sw = sh = 0
    if subtext:
        sbb = tmp.textbbox((0, 0), subtext, font=sub_font)
        sw, sh = sbb[2] - sbb[0], sbb[3] - sbb[1]

    pad = int(size * 0.62)
    bar_w = max(4, int(size * 0.16))
    gap = int(size * 0.5)
    text_w = max(tw, sw)
    text_h = th + (int(size * 0.35) + sh if subtext else 0)
    chip_w = bar_w + gap + text_w + 2 * pad
    chip_h = text_h + 2 * pad

    img = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = int(min(fw, fh) * 0.055)
    if position == "lower-center":
        x, y = (fw - chip_w) // 2, fh - chip_h - m
    elif position == "lower-right":
        x, y = fw - chip_w - m, fh - chip_h - m
    else:  # lower-left
        x, y = m, fh - chip_h - m

    r = int(chip_h * 0.22)
    d.rounded_rectangle([x + 3, y + 6, x + chip_w + 3, y + chip_h + 6], radius=r, fill=(0, 0, 0, 45))  # shadow
    d.rounded_rectangle([x, y, x + chip_w, y + chip_h], radius=r, fill=(255, 255, 255, 236))           # chip
    d.rounded_rectangle([x + pad, y + pad, x + pad + bar_w, y + chip_h - pad], radius=bar_w // 2, fill=_orange(cfg))
    tx = x + pad + bar_w + gap
    d.text((tx - bb[0], y + pad - bb[1]), txt, font=font, fill="#1A1A1A")
    if subtext:
        d.text((tx, y + pad + th + int(size * 0.35)), subtext, font=sub_font, fill="#6B6B6B")
    return img


def _pos_xy(position, gw, gh, fw, fh):
    m = int(fw * 0.06)
    return {
        "top-right": (fw - gw - m, int(fh * 0.14)),
        "top-left": (m, int(fh * 0.14)),
        "upper": ((fw - gw) // 2, int(fh * 0.15)),
        # "safe_upper" clears the top ~15% that a 4:5 / 1:1 recrop of a 9:16 frame trims,
        # so a hook badge survives Meta auto-cropping the multi-use master.
        "safe_upper": ((fw - gw) // 2, int(fh * 0.20)),
        "center": ((fw - gw) // 2, (fh - gh) // 2),
        # "lower" sits at 76% — under a Reels *ad*'s bottom UI (which eats the bottom 35%).
        # "safe_lower" is the same look, bottomed out at 62% so it clears that UI.
        "safe_lower": ((fw - gw) // 2, int(fh * 0.62) - gh),
        "lower": ((fw - gw) // 2, int(fh * 0.76) - gh),
    }.get(position, ((fw - gw) // 2, int(fh * 0.76) - gh))


def build_overlay_specs(overlays, frame_size, total_dur, cfg, tmpdir):
    """Render each overlay graphic and return ffmpeg overlay specs."""
    fw, fh = frame_size
    font_p = _font_path(cfg)
    tmpdir = Path(tmpdir)
    specs = []
    for i, ov in enumerate(overlays):
        typ = ov.get("type")
        if typ == "progress":
            from PIL import Image
            barh = max(5, int(fh * 0.006))
            img = Image.new("RGBA", (fw, barh), (0, 0, 0, 0))
            from PIL import ImageDraw
            ImageDraw.Draw(img).rectangle([0, 0, fw, barh], fill=ov.get("color", _orange(cfg)))
            png = tmpdir / f"ov_{i}_progress.png"
            img.save(png)
            # slide a full-width bar in from the left so it appears to fill L→R
            specs.append({"png": png, "x": f"(t/{total_dur:.3f}-1)*{fw}", "y": str(int(fh * 0.018)),
                          "enable": None})
            continue
        if typ == "logo":
            # Composite a real brand PNG (the script wordmark, emblem, etc.) rather than
            # rendering a text pill. width_frac sizes it to the frame; an optional soft
            # shadow lifts a white logo off busy footage.
            from PIL import Image
            logo = Image.open(ov["path"]).convert("RGBA")
            tw_ = max(1, int(fw * float(ov.get("width_frac", 0.5))))
            logo = logo.resize((tw_, max(1, int(logo.height * tw_ / logo.width))), Image.LANCZOS)
            if ov.get("shadow", True):
                logo = _with_shadow(logo, blur=max(2, tw_ // 90), alpha=150,
                                    offset=(0, max(1, tw_ // 220)))
            png = tmpdir / f"ov_{i}_logo.png"
            logo.save(png)
            gw, gh = logo.size
            x, y = _pos_xy(ov.get("position", "center"), gw, gh, fw, fh)
            specs.append({"png": png, "x": str(int(x)), "y": str(int(y)),
                          **_timing(ov)})
            continue
        if typ == "photo":
            # A still frame "popped" over the talking footage: square cover-crop of `path`
            # (crop_x / crop_y pick the centre, 0-1), white border, rounded corners, soft shadow.
            # Centred; bottom edge at bottom_frac of frame height so it sits above the captions.
            from PIL import Image, ImageDraw
            src = Image.open(ov["path"]).convert("RGB")
            side = min(src.size)
            cx = float(ov.get("crop_x", 0.5)) * src.width
            cy = float(ov.get("crop_y", 0.5)) * src.height
            x0 = int(min(max(cx - side / 2, 0), src.width - side))
            y0 = int(min(max(cy - side / 2, 0), src.height - side))
            sq = int(fw * float(ov.get("size_frac", 0.6)))
            bd = max(4, int(sq * float(ov.get("border_frac", 0.018))))
            rad = int(sq * 0.04)
            photo = src.crop((x0, y0, x0 + side, y0 + side)).resize((sq - 2 * bd,) * 2, Image.LANCZOS)
            card = Image.new("RGBA", (sq, sq), (0, 0, 0, 0))
            m = Image.new("L", (sq, sq), 0)
            ImageDraw.Draw(m).rounded_rectangle([0, 0, sq - 1, sq - 1], radius=rad, fill=255)
            card.paste((255, 255, 255, 255), (0, 0), m)
            pm = Image.new("L", photo.size, 0)
            ImageDraw.Draw(pm).rounded_rectangle([0, 0, photo.width - 1, photo.height - 1],
                                                 radius=max(1, rad - bd), fill=255)
            card.paste(photo, (bd, bd), pm)
            if ov.get("label"):
                # spec chip straddling the photo's top edge
                lsize = int(fw * float(ov.get("label_size", 0.042)))
                lfont = _load_font(font_p, lsize, "Black")
                ltxt = ov["label"].replace("*", "").upper()
                bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), ltxt, font=lfont)
                px, py = int(lsize * 0.55), int(lsize * 0.32)
                chip = Image.new("RGBA", (bb[2] - bb[0] + 2 * px, bb[3] - bb[1] + 2 * py), (0, 0, 0, 0))
                cd = ImageDraw.Draw(chip)
                cd.rounded_rectangle([0, 0, chip.width - 1, chip.height - 1], radius=chip.height // 2,
                                     fill=_orange(cfg))
                cd.text((px - bb[0], py - bb[1]), ltxt, font=lfont, fill="#FFFFFF")
                top = chip.height // 2
                tall = Image.new("RGBA", (max(sq, chip.width), sq + top), (0, 0, 0, 0))
                tall.alpha_composite(card, ((tall.width - sq) // 2, top))
                tall.alpha_composite(chip, ((tall.width - chip.width) // 2, 0))
                card = tall
            if ov.get("rotate"):
                card = card.rotate(float(ov["rotate"]), resample=Image.BICUBIC, expand=True)
            card = _with_shadow(card, blur=max(4, sq // 60), alpha=140, offset=(0, max(2, sq // 120)))
            png = tmpdir / f"ov_{i}_photo.png"
            card.save(png)
            gw, gh = card.size
            x = (fw - gw) // 2 + int(fw * float(ov.get("offset_x", 0.0)))
            y = int(fh * float(ov.get("bottom_frac", 0.66))) - gh
            specs.append({"png": png, "x": str(x), "y": str(y), **_timing(ov)})
            continue
        if typ in ("checklist", "textbox"):
            img = (_checklist if typ == "checklist" else _textbox)(ov, fw, cfg, font_p)
            png = tmpdir / f"ov_{i}_{typ}.png"
            img.save(png)
            x = (fw - img.width) // 2
            y = int(fh * float(ov.get("top_frac", 0.12)))
            specs.append({"png": png, "x": str(x), "y": str(y), **_timing(ov)})
            continue
        if typ == "review":
            img = _review_card(ov, fw, cfg, font_p)
            png = tmpdir / f"ov_{i}_review.png"
            img.save(png)
            x = (fw - img.width) // 2 + int(fw * float(ov.get("offset_x", 0.0)))
            if ov.get("bottom_frac") is not None:
                y = int(fh * float(ov["bottom_frac"])) - img.height
            elif ov.get("top_frac") is not None:
                y = int(fh * float(ov["top_frac"]))
            else:
                y = (fh - img.height) // 2
            specs.append({"png": png, "x": str(x), "y": str(y), **_timing(ov)})
            continue
        if typ == "calendar":
            img = _calendar(ov, fw, cfg, font_p)
            png = tmpdir / f"ov_{i}_calendar.png"
            img.save(png)
            x = (fw - img.width) // 2
            y = int(fh * float(ov.get("top_frac", 0.14)))
            specs.append({"png": png, "x": str(x), "y": str(y), **_timing(ov)})
            continue
        if typ == "chat":
            img = _chat(ov, fw, cfg, font_p)
            png = tmpdir / f"ov_{i}_chat.png"
            img.save(png)
            x = (fw - img.width) // 2
            if ov.get("bottom_frac") is not None:
                y = int(fh * float(ov["bottom_frac"])) - img.height
            else:
                y = int(fh * float(ov.get("top_frac", 0.12)))
            specs.append({"png": png, "x": str(x), "y": str(y), **_timing(ov)})
            continue
        if typ == "index":
            img = _index_label(ov, fw, cfg, font_p)
            png = tmpdir / f"ov_{i}_index.png"
            img.save(png)
            x = int(fw * float(ov.get("left_frac", 0.06)))
            y = int(fh * float(ov.get("bottom_frac", 0.76))) - img.height
            specs.append({"png": png, "x": str(x), "y": str(y), **_timing(ov)})
            continue
        # Optional per-overlay "font" (path, relative to the project root) for small/body text,
        # e.g. a brand body face for the CTA, badge and star line while callouts stay Inter.
        body_p = ov.get("font")
        if body_p and not Path(body_p).is_absolute():
            body_p = str(cfg.root / body_p)
        body_p = body_p or font_p
        if typ == "cta":
            img = _cta(ov["text"], fw, cfg, body_p)
        elif typ == "badge":
            img = _badge(ov["text"], fw, cfg, body_p)
        elif typ == "stars":
            img = _stars(ov.get("rating", 5), ov.get("text", ""), fw, cfg, body_p,
                         stroke=not ov.get("font"))
        elif typ == "callout":
            img = _callout(ov["text"], fw, cfg, body_p,
                           size_frac=float(ov.get("size_frac", 0.055)),
                           max_width_frac=float(ov.get("max_width_frac", 0.86)),
                           emphasis_style=ov.get("emphasis_style", "color"),
                           upper=ov.get("upper", True),
                           weight=ov.get("weight", "Black"))
        else:
            continue
        gw, gh = img.size
        png = tmpdir / f"ov_{i}_{typ}.png"
        img.save(png)
        x, y = _pos_xy(ov.get("position", "lower"), gw, gh, fw, fh)
        # Optional anchors, so a line can stay put while another builds beneath it:
        # "top_frac" pins the graphic's top edge, "bottom_frac" its bottom edge (fractions of height).
        if ov.get("top_frac") is not None:
            y = fh * float(ov["top_frac"])
        elif ov.get("bottom_frac") is not None:
            y = fh * float(ov["bottom_frac"]) - gh
        specs.append({"png": png, "x": str(int(x)), "y": str(int(y)), **_timing(ov)})
    return specs


def _timing(ov):
    """Resolve an overlay's on-screen window into an ffmpeg ``enable`` gate plus optional
    alpha-fade timing. ``fade`` (seconds) makes the overlay ease in and out instead of hard
    cutting — the difference between a DR pop and a premium reveal."""
    s, e = ov.get("start"), ov.get("end")
    enable = None
    if s is not None or e is not None:
        s0 = 0 if s is None else s
        enable = f"between(t,{s0},{e})" if e is not None else f"gte(t,{s0})"
    return {"enable": enable, "start": s, "end": e, "fade": float(ov.get("fade", 0.0))}
