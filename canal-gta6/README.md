# ZONA 6 · Canal de TikTok sobre GTA 6

10 vídeos verticales (1080×1920, 30 fps, 1–2,5 min) generados por código: guion, voz,
gráficos animados, subtítulos quemados, música original y montaje.

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
PREVIEW=1 python3 render.py 04   # prueba rápida a 540×960
python3 render.py                # los 10 en calidad final
python3 render.py 04 08          # solo algunos
python3 miniaturas.py            # portadas
```

Otra voz: `VOZ=ef_dora python3 render.py` (femenina) · velocidad: `VELOCIDAD=1.0`.

## Derechos

Gráficos, música y efectos están generados por código en este proyecto: no se usan
capturas, tráileres, logos ni música de Rockstar. Fuentes tipográficas Anton y
Montserrat (licencia SIL Open Font). Es un canal de fans sin relación con Rockstar
Games ni Take-Two; el aviso aparece en los primeros segundos de cada vídeo.
