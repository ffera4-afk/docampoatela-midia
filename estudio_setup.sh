#!/usr/bin/env bash
# Monta a ilha de edição do @docampoatela.cwb num ambiente novo (sem GPU, sem custo).
# Uso: bash estudio_setup.sh [pasta]   (padrão: ~/ilha)
set -euo pipefail
ILHA="${1:-$HOME/ilha}"
mkdir -p "$ILHA/models" && cd "$ILHA"

echo "== 1/4 Repositório do estúdio (logos, scripts, quadros)"
if [ ! -d docampoatela-midia/.git ]; then
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/ffera4-afk/docampoatela-midia docampoatela-midia
else
  git -C docampoatela-midia pull -q --depth 1 || true
fi
cp -n docampoatela-midia/estudio_*.py . 2>/dev/null || true

echo "== 2/4 HyperFrames local (render de vídeo HTML/GSAP, sem créditos)"
[ -f package.json ] || npm init -y >/dev/null
PUPPETEER_SKIP_DOWNLOAD=1 npm install --silent hyperframes gsap@3.15.0

echo "== 3/4 Python: visão computacional"
pip install -q --break-system-packages onnxruntime rembg opencv-python-headless >/dev/null 2>&1 || \
  pip install -q onnxruntime rembg opencv-python-headless

echo "== 4/4 Modelos (GitHub)"
dl(){ [ -s "models/$2" ] || curl -sL -o "models/$2" "$1"; }
dl https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s.onnx yolox_s.onnx
dl https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx yunet.onnx
dl https://github.com/fabio-sim/Depth-Anything-ONNX/releases/download/v2.0.0/depth_anything_v2_vits.onnx depth_anything_v2_vits.onnx
python3 -c "from rembg import new_session; new_session('u2net_human_seg')" >/dev/null 2>&1 || true

CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
echo
echo "Pronto em $ILHA"
echo "Render HyperFrames: PUPPETEER_EXECUTABLE_PATH=$CHROME npx hyperframes render <projeto> -o saida.mp4"
echo "Visão: python3 estudio_visao.py -h"
