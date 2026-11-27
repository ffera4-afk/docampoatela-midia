"""Gera quadros 1080x1920 na identidade @docampoatela.cwb com recortes do relatório."""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
BG = (7, 19, 31)          # #07131F azul-marinho dos logos
CYAN = (43, 196, 207)     # #2BC4CF teal do logo FM (positivo)
AMBER = (242, 84, 27)     # #F2541B laranja do escudo (alerta)
WHITE = (255, 255, 255)
GRAY = (143, 163, 181)    # #8FA3B5
BADGE = "/home/claude/brand/logo_docampoatela_badge.png"
FM = "/home/claude/brand/logo_fabio_moraes_dark.png"
ANTON = "/usr/share/fonts/truetype/google-fonts/ofl/anton/Anton-Regular.ttf"
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
PAGE_SCALE = 2479 / 924  # coords medidas na página exibida (924 px) -> render 300 dpi


def font(name, size):
    return ImageFont.truetype(ANTON if name == "anton" else INTER.format(name), size)


def background():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    # brilho radial suave no topo
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-300, -500, W + 300, 700), fill=(10, 45, 65, 200))
    gd.ellipse((W - 500, H - 700, W + 400, H + 300), fill=(242, 84, 27, 28))
    glow = glow.filter(ImageFilter.GaussianBlur(180))
    img.paste(glow, (0, 0), glow)
    # linhas de campo discretas
    line = (255, 255, 255, 14)
    d.line((0, H // 2, W, H // 2), fill=line, width=3)
    d.ellipse((W // 2 - 260, H // 2 - 260, W // 2 + 260, H // 2 + 260), outline=line, width=3)
    d.rectangle((W // 2 - 330, H - 420, W // 2 + 330, H + 10), outline=line, width=3)
    return img


def crop(page, box):
    x0, y0, x1, y1 = (int(v * PAGE_SCALE) for v in box)
    return Image.open(page).convert("RGB").crop((x0, y0, x1, y1))


def rounded(im, radius):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *im.size), radius, fill=255)
    out = Image.new("RGBA", im.size)
    out.paste(im, (0, 0), mask)
    return out


def place_card(base, im, x, y, width, color, radius=26, border=5):
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    # brilho colorido atrás do cartão
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(
        (x - 10, y - 10, x + im.width + 10, y + im.height + 10), radius + 10, fill=(*color, 110))
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    base.paste(glow, (0, 0), glow)
    card = rounded(im, radius)
    base.paste(card, (x, y), card)
    ImageDraw.Draw(base).rounded_rectangle(
        (x - border // 2, y - border // 2, x + im.width + border // 2, y + im.height + border // 2),
        radius, outline=color, width=border)
    return (x, y, x + im.width, y + im.height)


def logo(path, size):
    im = Image.open(path).convert("RGBA")
    im.thumbnail((size, size), Image.LANCZOS)
    return im


def header(base, tag, subtitle):
    d = ImageDraw.Draw(base)
    b = logo(BADGE, 110)
    base.alpha_composite(b, (60, 110))
    x = 190
    f = font("anton", 46)
    tw = d.textlength(tag, font=f)
    d.rounded_rectangle((x, 130, x + tw + 44, 200), 14, fill=AMBER)
    d.text((x + 22, 134), tag, font=f, fill=WHITE)
    d.text((x + tw + 70, 146), subtitle, font=font("SemiBold", 32), fill=GRAY)


def headline(base, lines, y, size=118):
    """lines: lista de listas de (texto, cor)."""
    d = ImageDraw.Draw(base)
    f = font("anton", size)
    for parts in lines:
        x = 70
        for text, color in parts:
            d.text((x, y), text, font=f, fill=color)
            x += d.textlength(text, font=f)
        y += int(size * 1.12)
    return y


def footer(base, source):
    d = ImageDraw.Draw(base)
    d.text((70, 1640), source, font=font("Medium", 26), fill=GRAY)
    handle = "@docampoatela.cwb"
    f = font("Bold", 34)
    d.text((W - 70 - d.textlength(handle, font=f), 1690), handle, font=f, fill=WHITE)


def centered(d, text, y, f, color):
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=color)


def open_card(path, series, subject):
    """Abertura com o bordão."""
    img = background().convert("RGBA")
    d = ImageDraw.Draw(img)
    b = logo(BADGE, 560)
    img.alpha_composite(b, ((W - b.width) // 2, 330))
    f = font("anton", 112)
    centered(d, "VAMOS DIRETO", 960, f, WHITE)
    centered(d, "DO CAMPO À TELA.", 1085, f, CYAN)
    fs = font("anton", 46)
    label = f"{series}  ·  {subject}"
    tw = d.textlength(label, font=fs)
    d.rounded_rectangle(((W - tw) / 2 - 34, 1268, (W + tw) / 2 + 34, 1346), 16, fill=AMBER)
    centered(d, label, 1272, fs, WHITE)
    img.convert("RGB").save(path, quality=95)


def end_card(path, kicker, cta):
    img = background().convert("RGBA")
    d = ImageDraw.Draw(img)
    b = logo(BADGE, 640)
    img.alpha_composite(b, ((W - b.width) // 2, 300))
    f = font("anton", 96)
    for i, (text, color) in enumerate(kicker):
        tw = d.textlength(text, font=f)
        d.text(((W - tw) / 2, 1010 + i * 108), text, font=f, fill=color)
    fc = font("Bold", 40)
    tw = d.textlength(cta, font=fc)
    d.rounded_rectangle(((W - tw) / 2 - 36, 1270, (W + tw) / 2 + 36, 1350), 40, fill=AMBER)
    d.text(((W - tw) / 2, 1286), cta, font=fc, fill=WHITE)
    centered(d, "@docampoatela.cwb", 1372, font("Bold", 40), WHITE)
    fl = font("SemiBold", 26)
    label = "ANÁLISE TÉCNICA"
    d.text(((W - d.textlength(label, font=fl)) / 2, 1480), label, font=fl, fill=GRAY)
    fm = logo(FM, 240)
    img.alpha_composite(fm, ((W - fm.width) // 2, 1525))
    img.convert("RGB").save(path, quality=95)


def connector(base, a, b, color):
    d = ImageDraw.Draw(base)
    d.line((*a, *b), fill=color, width=5)
    for p in (a, b):
        d.ellipse((p[0] - 10, p[1] - 10, p[0] + 10, p[1] + 10), fill=color)


def highlight(base, card_box, crop_box, region, color, width=6):
    """Desenha retângulo sobre `region` (coords de página) dentro do cartão posicionado."""
    cx0, cy0, cx1, cy1 = card_box
    bx0, by0, bx1, by1 = crop_box
    sx = (cx1 - cx0) / (bx1 - bx0)
    sy = (cy1 - cy0) / (by1 - by0)
    rx0, ry0, rx1, ry1 = region
    r = (cx0 + (rx0 - bx0) * sx, cy0 + (ry0 - by0) * sy, cx0 + (rx1 - bx0) * sx, cy0 + (ry1 - by0) * sy)
    ImageDraw.Draw(base).rounded_rectangle((r[0] - 8, r[1] - 8, r[2] + 8, r[3] + 8), 12, outline=color, width=width)
    return r


def card_frame(path, tag, subject, lines, page, row_box, color, source,
               hl_boxes=(), zoom_box=None, zoom_w=760, card_w=980, card_y=760):
    img = background().convert("RGBA")
    header(img, tag, subject)
    headline(img, lines, 250)
    card = place_card(img, crop(page, row_box), (W - card_w) // 2, card_y, card_w, color)
    rs = [highlight(img, card, row_box, hb, color) for hb in hl_boxes]
    if zoom_box:
        zoom = crop(page, zoom_box)
        zh = int(zoom.height * zoom_w / zoom.width)
        zx, zy = (W - zoom_w) // 2, card[3] + 130
        if rs:
            r = rs[0]
            connector(img, ((r[0] + r[2]) / 2, r[3] + 10), (zx + zoom_w / 2, zy - 6), color)
        place_card(img, zoom, zx, zy, zoom_w, color, radius=30, border=6)
        ImageDraw.Draw(img).text((zx, zy - 62), "NO RELATÓRIO", font=font("Bold", 28), fill=color)
    footer(img, source)
    img.convert("RGB").save(path, quality=95)


def photo_frame(path, tag, subject, lines, photo, source, color=CYAN):
    img = background().convert("RGBA")
    header(img, tag, subject)
    y = headline(img, lines, 250)
    ph = Image.open(photo).convert("RGB")
    place_card(img, ph, 50, y + 60, 980, color)
    footer(img, source)
    img.convert("RGB").save(path, quality=95)


def text_frame(path, lines, size=150, tag=None, subject=None, color_bar=None):
    img = background().convert("RGBA")
    if tag:
        header(img, tag, subject)
    total = len(lines) * int(size * 1.12)
    headline(img, lines, (H - total) // 2 - 80, size)
    if color_bar:
        ImageDraw.Draw(img).rectangle((70, (H - total) // 2 - 130, 250, (H - total) // 2 - 112), fill=color_bar)
    footer(img, "")
    img.convert("RGB").save(path, quality=95)


def bars_frame(path, tag, subject, lines, bars, source, note=None):
    """bars: lista de (rótulo, valor_atleta, valor_elite, cor)."""
    img = background().convert("RGBA")
    header(img, tag, subject)
    y = headline(img, lines, 250) + 80
    d = ImageDraw.Draw(img)
    for label, atl, eli, color in bars:
        d.text((70, y), label, font=font("Bold", 40), fill=WHITE)
        y += 70
        for name, val, c in (("ATLETA", atl, color), ("ELITE SÉRIE A", eli, GRAY)):
            d.text((70, y + 4), name, font=font("SemiBold", 28), fill=GRAY)
            x0, x1 = 330, 860
            d.rounded_rectangle((x0, y, x1, y + 44), 22, fill=(30, 45, 60))
            d.rounded_rectangle((x0, y, x0 + (x1 - x0) * val / 100, y + 44), 22, fill=c)
            d.text((880, y - 8), f"{val}%", font=font("anton", 56), fill=c if c != GRAY else WHITE)
            y += 80
        y += 50
    if note:
        d.text((70, y), note, font=font("Medium", 32), fill=GRAY)
    footer(img, source)
    img.convert("RGB").save(path, quality=95)


def list_frame(path, tag, subject, title, items, source):
    img = background().convert("RGBA")
    header(img, tag, subject)
    y = headline(img, [[(title, CYAN)]], 260) + 60
    d = ImageDraw.Draw(img)
    for i, (head, body) in enumerate(items, 1):
        d.rounded_rectangle((70, y, 1010, y + 230), 26, fill=(14, 32, 46), outline=CYAN, width=3)
        d.text((105, y + 30), str(i), font=font("anton", 120), fill=AMBER)
        d.text((210, y + 45), head, font=font("anton", 62), fill=WHITE)
        d.text((210, y + 135), body, font=font("Medium", 34), fill=GRAY)
        y += 270
    footer(img, source)
    img.convert("RGB").save(path, quality=95)
