# ZONA 6 · Canal de TikTok sobre GTA 6

10 vídeos verticales en **pixel art** (1080×1920, 30 fps, 1,5–2,5 min) generados por código:
guion, voz amable (TTS), escenas pixel art animadas (lienzo 360×640 escalado ×3), menús tipo
RPG, subtítulos quemados, música chiptune original, efectos 8-bit y montaje.

- `PUBLICACION.md` → horario del jueves, textos y hashtags para pegar, pasos en TikTok Studio.
- `FUENTES.md` → de dónde sale cada dato y qué está sin confirmar.
- `motor/guiones.py` → los 10 guiones (edita aquí y vuelve a renderizar).
- `salida/<vídeo>/` → `.mp4` final, `portada.png`, subtítulos `.srt`.

## Regenerar

Requisitos: Python 3, ffmpeg, `pip install kokoro-onnx soundfile scipy pillow numpy`,
y el modelo de voz Kokoro (`kokoro-v1.0.onnx` y `voices-v1.0.bin`, publicados en las
releases de GitHub de `thewh1teagle/kokoro-onnx`) en `/opt/tts/` o en las rutas de
`KOKORO_MODEL` / `KOKORO_VOICES`.

```bash
cd motor
PREVIEW=1 python3 render.py 04   # prueba rápida a 360×640
python3 render.py                # los 10 en calidad final
python3 render.py 04 08          # solo algunos
python3 miniaturas.py            # portadas
```

Voz por defecto: `ef_dora` a velocidad 1.05 (femenina, pronunciación de España). Otras: `VOZ=ef_dora:0.75+em_alex:0.25` (más cálida) o `VOZ=em_alex python3 render.py` · velocidad: `VELOCIDAD=1.1`.
El tratamiento de la voz (tono, ecualización, compresión) está en `CADENA_VOZ` de `motor/audio.py`.

## Derechos

Gráficos, música y efectos están generados por código en este proyecto: no se usan
capturas, tráileres, logos ni música de Rockstar. Fuentes Press Start 2P y Jersey 10
(licencia SIL Open Font). Es un canal de fans sin relación con Rockstar
Games ni Take-Two; el aviso aparece en los primeros segundos de cada vídeo.

`muestras_voz/` tiene las muestras de voz para comparar.


## Vídeos 3D en un Mac con chip Apple (mucho más rápido)

```bash
brew install python@3.13 ffmpeg git
git clone -b claude/gta6-channel-ten-videos-1vzoms https://github.com/urielmelesio30-ops/game-.git
cd game-/canal-gta6
python3.13 -m venv .venv && source .venv/bin/activate
pip install bpy kokoro-onnx soundfile scipy pillow numpy
mkdir -p tts && curl -L -o tts/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx \
  && curl -L -o tts/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
cd motor
export KOKORO_MODEL=../tts/kokoro-v1.0.onnx KOKORO_VOICES=../tts/voices-v1.0.bin GPU=1
python video3d_doomsday.py     # 6 cosas antes de Doomsday
python video3d_teorias.py      # teorías
```
Los vídeos salen en `canal-gta6/salida/13-doomsday-6-cosas-3d/` y `canal-gta6/salida/14-doomsday-teorias-3d/`.
