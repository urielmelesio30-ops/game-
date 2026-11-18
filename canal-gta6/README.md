# Canal de curiosidades: vídeos verticales animados

11 vídeos verticales (1080×1920, 30 fps, menos de 1:30) generados por código: guion, voz TTS en español
de España (Kokoro, voz `ef_dora`), escenas 2D animadas en pixel art, marco de neón, subtítulos palabra a palabra,
música chiptune original y efectos de sonido solo en los momentos clave.

- **Serie «Cosas que no sabías» (10 vídeos)**: `salida/19…28`. Guiones en `motor/serie_videos.py`.
- **El chico que filtró GTA 6**: `salida/30-el-chico-que-filtro-gta6`. Guion en `motor/gta_filtracion.py`.
- `serie/PUBLICAR.md` → títulos, descripciones, hashtags y fuentes de los datos.
- `CALENDARIO.md` → qué día y a qué hora subir cada vídeo.
- `perfil/` → fotos de perfil (la mascota del canal).

## Regenerar

Requisitos: Python 3, ffmpeg, `pip install kokoro-onnx soundfile scipy pillow numpy`, y el modelo de voz Kokoro
(`kokoro-v1.0.onnx` y `voices-v1.0.bin`, de las releases de GitHub de `thewh1teagle/kokoro-onnx`) en `/opt/tts/`.

```bash
cd motor
python serie_videos.py 3            # un vídeo de la serie (1..10)
python serie_videos.py 3 --muestra  # solo un fotograma por escena, para revisar
python gta_filtracion.py            # el vídeo de GTA 6
```

## Motor

- `historia.py`: montaje (marco, titular, pegatinas, transiciones, subtítulos, audio, ffmpeg).
- `serie.py`: fondos, iconos, mapas, globo terráqueo, contadores y plantillas de escena.
- `historia_aviones.py` (mapas y globo), `historia_scroll.py` (cerebro e iconos), `anime.py` (fondos de neón y efectos),
  `plano.py`, `render.py` y `audio.py`: piezas compartidas.
- `datos/ne_110m_land.geojson`: contornos de la Tierra (Natural Earth, dominio público).
