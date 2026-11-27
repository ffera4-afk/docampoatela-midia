#!/usr/bin/env python3
"""Ferramentas de visão do estúdio @docampoatela.cwb (rodam em CPU, sem custo).

Subcomandos:
  lance     Reenquadra um clipe para 9:16 seguindo um jogador, com círculo de destaque,
            congelamento com zoom e desfoque de rostos opcional.
  rostos    Só desfoca rostos de um clipe (atletas menores de idade).
  recorte   Recorta o atleta de uma foto (PNG com fundo transparente).
  parallax  Transforma uma foto em um clipe 9:16 com efeito 3D (Depth Anything).
  quadro    Extrai um quadro de um clipe com as caixas dos jogadores numeradas,
            para escolher qual seguir.

Modelos esperados em ./models (ou ESTUDIO_MODELS): yolox_s.onnx, yunet.onnx,
depth_anything_v2_vits.onnx. O recorte usa o rembg (baixa o modelo sozinho).
"""
import argparse, os, subprocess, sys
import numpy as np
import cv2

MODELS = os.environ.get("ESTUDIO_MODELS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"))
TEAL = (207, 196, 43)      # BGR de #2BC4CF
ORANGE = (27, 84, 242)     # BGR de #F2541B
W9, H9 = 1080, 1920


# ---------------------------------------------------------------- detecção de pessoas (YOLOX)
class Pessoas:
    def __init__(self, conf=0.35):
        import onnxruntime as ort
        self.s = ort.InferenceSession(os.path.join(MODELS, "yolox_s.onnx"), providers=["CPUExecutionProvider"])
        self.inp = self.s.get_inputs()[0].name
        self.size = 640
        self.conf = conf
        grids, strides = [], []
        for st in (8, 16, 32):
            n = self.size // st
            xv, yv = np.meshgrid(np.arange(n), np.arange(n))
            grids.append(np.stack((xv, yv), 2).reshape(1, -1, 2))
            strides.append(np.full((1, n * n, 1), st))
        self.grids = np.concatenate(grids, 1)
        self.strides = np.concatenate(strides, 1)

    def __call__(self, img):
        h, w = img.shape[:2]
        r = min(self.size / h, self.size / w)
        pad = np.full((self.size, self.size, 3), 114, np.uint8)
        pad[: int(h * r), : int(w * r)] = cv2.resize(img, (int(w * r), int(h * r)))
        x = pad.transpose(2, 0, 1)[None].astype(np.float32)
        out = self.s.run(None, {self.inp: x})[0]
        out[..., :2] = (out[..., :2] + self.grids) * self.strides
        out[..., 2:4] = np.exp(out[..., 2:4]) * self.strides
        p = out[0]
        score = p[:, 4] * p[:, 5]  # objectness * classe "pessoa"
        k = score > self.conf
        p, score = p[k], score[k]
        boxes = np.stack([p[:, 0] - p[:, 2] / 2, p[:, 1] - p[:, 3] / 2, p[:, 0] + p[:, 2] / 2, p[:, 1] + p[:, 3] / 2], 1) / r
        idx = cv2.dnn.NMSBoxes(boxes.tolist(), score.tolist(), self.conf, 0.45)
        idx = np.array(idx).flatten() if len(idx) else []
        return [(*boxes[i], score[i]) for i in idx]


# ---------------------------------------------------------------- rostos (YuNet)
class Rostos:
    def __init__(self):
        self.d = None

    def borrar(self, img):
        h, w = img.shape[:2]
        if self.d is None or self.d.getInputSize() != (w, h):
            self.d = cv2.FaceDetectorYN.create(os.path.join(MODELS, "yunet.onnx"), "", (w, h), 0.6, 0.3, 5000)
            self.d.setInputSize((w, h))
        _, faces = self.d.detect(img)
        if faces is None:
            return img
        for f in faces:
            x, y, fw, fh = [int(v) for v in f[:4]]
            m = int(0.35 * max(fw, fh))
            x0, y0, x1, y1 = max(x - m, 0), max(y - m, 0), min(x + fw + m, w), min(y + fh + m, h)
            roi = img[y0:y1, x0:x1]
            if roi.size:
                k = max(31, (max(x1 - x0, y1 - y0) // 2) | 1)
                img[y0:y1, x0:x1] = cv2.GaussianBlur(roi, (k, k), 0)
        return img


# ---------------------------------------------------------------- utilidades de vídeo
def ler(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    return frames, fps


def escritor(out, fps, w, h):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                             "-s", f"{w}x{h}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                             "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)


def anel(img, box, cor=TEAL, rotulo=None):
    """Círculo de destaque no chão, sob o jogador (estilo transmissão)."""
    x0, y0, x1, y1 = box
    cx, cy = int((x0 + x1) / 2), int(y1)
    rx = int(max((x1 - x0) * 0.75, 18)); ry = int(rx * 0.32)
    glow = img.copy()
    cv2.ellipse(glow, (cx, cy), (rx + 6, ry + 4), 0, 0, 360, cor, -1, cv2.LINE_AA)
    img[:] = cv2.addWeighted(glow, 0.28, img, 0.72, 0)
    cv2.ellipse(img, (cx, cy), (rx, ry), 0, 0, 360, cor, max(3, rx // 10), cv2.LINE_AA)
    if rotulo:
        fs = max(0.6, (x1 - x0) / 90)
        (tw, th), _ = cv2.getTextSize(rotulo, cv2.FONT_HERSHEY_DUPLEX, fs, 2)
        tx, ty = cx - tw // 2, int(y0) - 14
        cv2.rectangle(img, (tx - 10, ty - th - 10), (tx + tw + 10, ty + 8), cor, -1)
        cv2.putText(img, rotulo, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, fs, (255, 255, 255), 2, cv2.LINE_AA)


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-6)


def seguir(frames, alvo_xy, det_every=1):
    """Segue o jogador mais próximo de alvo_xy (x,y no 1º quadro). Devolve uma caixa por quadro."""
    det = Pessoas()
    last, vel, caixas, perdido = None, (0.0, 0.0), [], 0
    for f in frames:
        ds = det(f)
        if last is None:
            if ds:
                ax, ay = alvo_xy
                last = min(ds, key=lambda d: ((d[0] + d[2]) / 2 - ax) ** 2 + ((d[1] + d[3]) / 2 - ay) ** 2)[:4]
        else:
            pred = (last[0] + vel[0], last[1] + vel[1], last[2] + vel[0], last[3] + vel[1])
            ph = pred[3] - pred[1]
            pc = ((pred[0] + pred[2]) / 2, (pred[1] + pred[3]) / 2)
            novo = None
            if ds:
                def custo(d):
                    c = ((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)
                    dist = ((c[0] - pc[0]) ** 2 + (c[1] - pc[1]) ** 2) ** 0.5 / ph
                    tam = abs((d[3] - d[1]) - ph) / ph
                    return dist + tam
                best = min(ds, key=custo)
                limite = 0.6 + 0.25 * perdido
                if custo(best) < limite:
                    novo = best[:4]
            if novo is None:  # oclusão: segura no lugar e procura num raio que cresce
                novo = last
                vel = (vel[0] * 0.3, vel[1] * 0.3)
                perdido += 1
            else:
                v = ((novo[0] + novo[2] - last[0] - last[2]) / 2, (novo[1] + novo[3] - last[1] - last[3]) / 2)
                vel = (vel[0] * 0.5 + v[0] * 0.5, vel[1] * 0.5 + v[1] * 0.5)
                perdido = 0
            last = novo
        caixas.append(tuple(float(v) for v in last) if last is not None else None)
    # preenche buracos e suaviza
    for i in range(len(caixas)):
        if caixas[i] is None:
            caixas[i] = next((c for c in caixas[i:] if c), None) or next((c for c in reversed(caixas[:i]) if c), (0, 0, 1, 1))
    arr = np.array(caixas)
    k = 3
    pad = np.pad(arr, ((k, k), (0, 0)), mode="edge")
    sm = np.stack([np.convolve(pad[:, j], np.ones(2 * k + 1) / (2 * k + 1), mode="valid") for j in range(4)], 1)
    return [tuple(b) for b in sm]


# ---------------------------------------------------------------- subcomandos
def cmd_quadro(a):
    frames, _ = ler(a.clipe)
    f = frames[min(int(a.t * 30), len(frames) - 1)].copy()
    for i, d in enumerate(Pessoas()(f)):
        x0, y0, x1, y1 = [int(v) for v in d[:4]]
        cv2.rectangle(f, (x0, y0), (x1, y1), TEAL, 2)
        cv2.putText(f, f"{i} ({(x0+x1)//2},{(y0+y1)//2})", (x0, y0 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, ORANGE, 2)
    cv2.imwrite(a.saida, f)
    print("salvo", a.saida)


def cmd_lance(a):
    frames, fps = ler(a.clipe)
    h, w = frames[0].shape[:2]
    caixas = seguir(frames, tuple(map(float, a.alvo.split(","))))
    rost = Rostos() if a.borrar_rostos else None
    cw = min(w, int(h * 9 / 16))  # janela 9:16 dentro do quadro original
    ff = escritor(a.saida, fps, W9, H9)
    cx_s = None
    fz = (float(a.congelar), float(a.congelar_dur)) if a.congelar else None

    def compor(f, box, zoom=1.0):
        nonlocal cx_s
        f = f.copy()
        if rost: rost.borrar(f)
        anel(f, box, TEAL, a.rotulo)
        cx = (box[0] + box[2]) / 2
        cx_s = cx if cx_s is None else cx_s + (cx - cx_s) * 0.15
        ww, hh = cw / zoom, h / zoom
        cy = (box[1] + box[3]) / 2 if zoom > 1 else h / 2
        x0 = min(max(cx_s - ww / 2, 0), w - ww); y0 = min(max(cy - hh / 2, 0), h - hh)
        crop = f[int(y0):int(y0 + hh), int(x0):int(x0 + ww)]
        out = cv2.resize(crop, (W9, H9), interpolation=cv2.INTER_CUBIC)
        if a.modo == "encaixe":  # quadro 16:9 inteiro no meio, fundo desfocado
            bg = cv2.GaussianBlur(cv2.resize(f, (W9, H9)), (0, 0), 25) // 2
            fh = int(W9 * h / w)
            bg[(H9 - fh) // 2:(H9 - fh) // 2 + fh] = cv2.resize(f, (W9, fh), interpolation=cv2.INTER_AREA)
            out = bg
        return out

    for i, (f, b) in enumerate(zip(frames, caixas)):
        t = i / fps
        ff.stdin.write(compor(f, b).tobytes())
        if fz and abs(t - fz[0]) < 0.5 / fps:  # congela com zoom no jogador
            n = int(fz[1] * fps)
            for j in range(n):
                k = min(1.0, j / (0.4 * fps))
                ff.stdin.write(compor(f, b, 1 + 0.5 * (k * k * (3 - 2 * k))).tobytes())
    ff.stdin.close(); ff.wait()
    print("salvo", a.saida)


def cmd_rostos(a):
    frames, fps = ler(a.clipe)
    h, w = frames[0].shape[:2]
    r = Rostos(); ff = escritor(a.saida, fps, w, h)
    for f in frames:
        ff.stdin.write(r.borrar(f.copy()).tobytes())
    ff.stdin.close(); ff.wait()
    print("salvo", a.saida)


def cmd_recorte(a):
    from rembg import remove, new_session
    from PIL import Image
    out = remove(Image.open(a.foto), session=new_session(a.modelo))
    out = out.crop(out.getbbox())
    out.save(a.saida)
    print("salvo", a.saida, out.size)


def cmd_parallax(a):
    import onnxruntime as ort
    img = cv2.imread(a.foto)
    h, w = img.shape[:2]
    s = ort.InferenceSession(os.path.join(MODELS, "depth_anything_v2_vits.onnx"), providers=["CPUExecutionProvider"])
    x = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (518, 518)).astype(np.float32) / 255
    x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
    d = s.run(None, {s.get_inputs()[0].name: x})[0].squeeze()
    d = cv2.resize((d - d.min()) / (d.max() - d.min() + 1e-6), (w, h))
    d = cv2.GaussianBlur(d.astype(np.float32), (0, 0), 3)
    # enquadra a foto em 9:16 (cobre a tela)
    sc = max(W9 / w, H9 / h) * 1.12
    img2 = cv2.resize(img, (int(w * sc), int(h * sc)), interpolation=cv2.INTER_CUBIC)
    d2 = cv2.resize(d, (img2.shape[1], img2.shape[0]))
    ff = escritor(a.saida, 30, W9, H9)
    n = int(a.duracao * 30)
    yy, xx = np.mgrid[0:H9, 0:W9].astype(np.float32)
    ox, oy = (img2.shape[1] - W9) / 2, (img2.shape[0] - H9) / 2
    for i in range(n):
        p = i / max(n - 1, 1)
        dx = (p - 0.5) * a.forca * 2; dz = 1 + 0.06 * p
        dd = d2[int(oy):int(oy) + H9, int(ox):int(ox) + W9]
        mx = ox + (xx - W9 / 2) / dz + W9 / 2 + dx * dd
        my = oy + (yy - H9 / 2) / dz + H9 / 2 - dx * 0.3 * dd
        ff.stdin.write(cv2.remap(img2, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).tobytes())
    ff.stdin.close(); ff.wait()
    print("salvo", a.saida)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("quadro"); q.add_argument("clipe"); q.add_argument("saida"); q.add_argument("--t", type=float, default=0)
    l = sp.add_parser("lance"); l.add_argument("clipe"); l.add_argument("saida")
    l.add_argument("--alvo", required=True, help="x,y do jogador no 1º quadro (use o subcomando quadro)")
    l.add_argument("--rotulo", default=None, help="texto acima do jogador, ex.: 'RONALDO'")
    l.add_argument("--congelar", default=None, help="segundo para congelar com zoom")
    l.add_argument("--congelar-dur", default=1.5)
    l.add_argument("--modo", choices=["seguir", "encaixe"], default="seguir")
    l.add_argument("--borrar-rostos", action="store_true")
    r = sp.add_parser("rostos"); r.add_argument("clipe"); r.add_argument("saida")
    c = sp.add_parser("recorte"); c.add_argument("foto"); c.add_argument("saida"); c.add_argument("--modelo", default="u2net_human_seg")
    x = sp.add_parser("parallax"); x.add_argument("foto"); x.add_argument("saida")
    x.add_argument("--duracao", type=float, default=5); x.add_argument("--forca", type=float, default=28)
    a = p.parse_args()
    {"quadro": cmd_quadro, "lance": cmd_lance, "rostos": cmd_rostos, "recorte": cmd_recorte, "parallax": cmd_parallax}[a.cmd](a)


if __name__ == "__main__":
    main()
