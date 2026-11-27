"""Renderiza a trilha visual (sem áudio) do Raio-X Ronaldo, sincronizada com a narração."""
import json, subprocess, sys
sys.path.insert(0, "/home/claude/scripts")
from PIL import Image, ImageDraw, ImageFont
from frames import W, H, CYAN, AMBER, WHITE, PAGE_SCALE

FPS = 30
END = 85.0
FR = "/home/claude/frames/ronaldo"
WORDS = json.load(open("/home/claude/el/words.json"))
OUT = sys.argv[1]

# cenas: (arquivo, início, zoom_inicio, região de zoom (x0,y0,x1,y1) em px do quadro)
def lupa(crop_box, zoom_box, zoom_w, card_w=980, card_y=760):
    cw = crop_box[2] - crop_box[0]; ch = crop_box[3] - crop_box[1]
    card_h = card_w * ch / cw
    zw = zoom_box[2] - zoom_box[0]; zh = zoom_box[3] - zoom_box[1]
    zy = card_y + card_h + 130
    zx = (W - zoom_w) / 2
    return (zx - 40, zy - 90, zx + zoom_w + 40, zy + zoom_w * zh / zw + 40)

SCENES = [
    ("r01_gancho.jpg", 0.0, None, None),
    ("r02_posse.jpg", 5.45, 5.9, lupa((88, 322, 836, 462), (97, 357, 276, 414), 720)),
    ("r03_bordao.jpg", 8.9, None, None),
    ("r04_ficha.jpg", 10.75, None, None),
    ("r05_amostra.jpg", 14.85, 15.7, lupa((60, 55, 865, 172), (468, 58, 664, 170), 600)),
    ("r06_aereo.jpg", 20.35, 22.5, lupa((110, 861, 815, 956), (655, 869, 805, 932), 720)),
    ("r07_1x1.jpg", 27.5, 28.6, lupa((63, 748, 557, 862), (68, 752, 382, 802), 940)),
    ("r08_interceptacoes.jpg", 30.7, None, None),
    ("r09_mental.jpg", 36.3, None, None),
    ("r10_virada.jpg", 40.45, None, None),
    ("r11_antecipacao.jpg", 42.6, 48.8, lupa((110, 462, 815, 556), (655, 470, 805, 532), 720)),
    ("r12_construcao.jpg", 58.2, 59.2, lupa((63, 748, 557, 862), (68, 803, 397, 852), 940)),
    ("r13_plano.jpg", 67.1, None, None),
    ("r14_final.jpg", 76.9, None, None),
]
imgs = {s[0]: Image.open(f"{FR}/{s[0]}").convert("RGB") for s in SCENES}

ANTON = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/ofl/anton/Anton-Regular.ttf", 86)
KEY = {"cem", "100", "vinte", "cinco", "segundos", "seis", "nove", "catorze", "dezessete", "oitenta", "dois",
       "três", "onze", "zero", "elite", "dominante", "máxima", "antecipar", "antecipa", "antecipação", "interceptar",
       "direto", "campo", "tela", "direct", "docampoatela", "perde", "terreno", "uma", "espera"}
ALERT = {"vinte", "cinco", "segundos", "perde", "terreno", "uma", "três", "onze", "espera"}

# blocos de legenda: até 3 palavras, quebrando na pontuação
words = [w for w in WORDS if w.get("type") == "word"]
chunks, cur = [], []
for w in words:
    cur.append(w)
    if len(cur) == 3 or w["text"][-1] in ".,:?":
        chunks.append(cur); cur = []
if cur: chunks.append(cur)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def view(scene_idx, t):
    name, start, zstart, zbox = SCENES[scene_idx]
    nxt = SCENES[scene_idx + 1][1] if scene_idx + 1 < len(SCENES) else END
    img = imgs[name]
    local = t - start
    # push-in lento 1.00 -> 1.06 + soco de entrada
    s = 1.0 + 0.06 * (local / max(nxt - start, 0.1)) + 0.05 * (1 - ease(local / 0.35))
    cx, cy = W / 2, H / 2
    vw, vh = W / s, H / s
    x0 = min(max(cx - vw / 2, 0), W - vw); y0 = min(max(cy - vh / 2, 0), H - vh)
    out = img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + vw, y0 + vh))
    if zbox and t >= zstart:
        k = ease((t - zstart) / 0.5)
        # holofote: escurece o resto e amplia a lupa no lugar
        bx = tuple(int(v) for v in zbox)
        lup = img.crop(bx)
        sc = 1.0 + min(0.16, 1060 / lup.width - 1) * k
        lw, lh = int(lup.width * sc), int(lup.height * sc)
        lup = lup.resize((lw, lh), Image.LANCZOS)
        dark = Image.new("RGB", (W, H), (0, 0, 0))
        out = Image.blend(out, dark, 0.6 * k)
        ccx, ccy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
        out.paste(lup, (int(ccx - lw / 2), int(ccy - lh / 2)))
    return out


def scene_at(t):
    i = 0
    for k, s in enumerate(SCENES):
        if t >= s[1]: i = k
    return i


NOCAP = {"r01_gancho.jpg", "r03_bordao.jpg", "r10_virada.jpg", "r14_final.jpg"}


def caption(frame, t):
    if SCENES[scene_at(t)][0] in NOCAP: return
    ch = next((c for c in chunks if c[0]["start"] - 0.05 <= t <= c[-1]["end"] + 0.15), None)
    if not ch: return
    d = ImageDraw.Draw(frame)
    parts = [w["text"].upper() for w in ch]
    widths = [d.textlength(p, font=ANTON) for p in parts]
    gap = 26
    x = (W - (sum(widths) + gap * (len(parts) - 1))) / 2
    y = 1430
    for w, p, wd in zip(ch, parts, widths):
        bare = w["text"].lower().strip(".,:?")
        active = w["start"] - 0.05 <= t
        color = (AMBER if bare in ALERT else CYAN) if bare in KEY else WHITE
        if not active: color = (200, 205, 210)
        d.text((x, y), p, font=ANTON, fill=color, stroke_width=7, stroke_fill=(0, 0, 0))
        x += wd + gap


ff = subprocess.Popen(["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                       "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
                       "-movflags", "+faststart", OUT], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
XF = 0.2
for n in range(int(END * FPS)):
    t = n / FPS
    i = scene_at(t)
    frame = view(i, t)
    if i > 0 and t - SCENES[i][1] < XF:  # transição: fusão rápida com a cena anterior
        a = (t - SCENES[i][1]) / XF
        frame = Image.blend(view(i - 1, t), frame, a)
    caption(frame, t)
    d = ImageDraw.Draw(frame)
    d.rectangle((0, 0, int(W * t / END), 8), fill=AMBER)
    ff.stdin.write(frame.tobytes())
ff.stdin.close(); ff.wait()
print("ok", OUT)
