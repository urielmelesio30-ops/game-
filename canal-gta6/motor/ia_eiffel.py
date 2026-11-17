# -*- coding: utf-8 -*-
"""Vídeo de la Torre Eiffel con arte pixel generado por IA (Canva) + animación por código.

- Fondos: escenas IA (París al atardecer, café, cuarto de noche) con encuadres y cámara.
- Personajes: recortes de las escenas IA (la tele estafadora, la tele leyendo, el móvil
  gruñón) animados como marionetas (botar, deslizar, temblar, correr).
- Encima: objetos pixel dibujados (sellos, bombilla, papeles, billetes, sirenas, barrotes…).
- Subtítulo pixel grande con banda oscura, efectos solo en momentos clave.
Personajes originales del canal.
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import render as R
import historia as Hm
import historia_eiffel as HE

W, H, FPS = 1080, 1920, 30
ARTE = os.path.join(Hm.PL.RAIZ if hasattr(Hm.PL, "RAIZ") else os.path.dirname(os.path.dirname(__file__)), "arte_ia")
ARTE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "arte_ia")
SLUG = "16-torre-eiffel-estafa"
SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "salida", SLUG)
PX = 4   # tamaño del "píxel" de los elementos dibujados por código


def cargar(ruta):
    return Image.open(os.path.join(ARTE, ruta)).convert("RGBA")


def limpiar(im):
    a = np.array(im)
    a[..., 3] = np.where(a[..., 3] > 140, 255, 0)
    return Image.fromarray(a)


def recorte9x16(im, cx, cy, ancho):
    """Encuadre vertical 9:16 de una imagen, ampliado a 1080x1920 sin suavizar (pixel)."""
    alto = ancho * 16 / 9
    x0, y0 = max(0, cx - ancho / 2), max(0, cy - alto / 2)
    x0, y0 = min(x0, im.width - ancho), min(y0, im.height - alto)
    return im.crop((int(x0), int(y0), int(x0 + ancho), int(y0 + alto))).resize((W, H), Image.NEAREST)


def pixelado(im, k=PX):
    """Dibujo pequeño → escala entera sin suavizar."""
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def a_pixel(im, ancho):
    """Ilustración vectorial → sprite pixel (para objetos dibujados por código)."""
    alto = max(1, round(im.height * ancho / im.width))
    peq = im.resize((ancho, alto), Image.BOX)
    arr = np.array(peq)
    arr[..., 3] = np.where(arr[..., 3] > 110, 255, 0)
    return pixelado(Image.fromarray(arr))


def texto_px(t, tam=16, color="blanco", sombra="negro", k=PX):
    return pixelado(R.txt_img(t, R.fuente("pixel", tam), color, sombra, contorno=sombra is not None), k)


def pegar(c, im, x, y):
    c.alpha_composite(im, (int(round(x - im.width / 2)), int(round(y - im.height / 2))))


def escalar(im, k):
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.NEAREST)


def pop(im, tl, dur=0.25):
    u = min(1.0, max(0.0, tl / dur))
    k = [0.3, 0.7, 1.15, 1.0][min(3, int(u * 4))]
    return im if k == 1.0 else escalar(im, k)


def camara(fondo, tl, dur, z0=1.0, z1=1.12, dx=0, dy=0):
    """Zoom/paneo lento (Ken Burns) sobre el fondo."""
    u = tl / max(dur, 0.01)
    z = z0 + (z1 - z0) * u
    nw, nh = int(W * z), int(H * z)
    im = fondo.resize((nw, nh), Image.NEAREST)
    x0 = (nw - W) / 2 + dx * u * (nw - W) / 2
    y0 = (nh - H) / 2 + dy * u * (nh - H) / 2
    return im.crop((int(x0), int(y0), int(x0) + W, int(y0) + H))


def sombra(c, x, y, ancho):
    s = Image.new("RGBA", (int(ancho), int(ancho * 0.16)), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse((0, 0, s.width - 1, s.height - 1), fill=(0, 0, 0, 90))
    pegar(c, s, x, y)


def personaje(c, im, x, suelo, tl, bote=True, escala=1.0, temblor=0, corre=False):
    sp = escalar(im, escala)
    dy = -abs(math.sin(tl * (10 if corre else 4))) * (26 if corre else 10) if bote else 0
    dx = (np.random.default_rng(int(tl * 60)).integers(-temblor, temblor + 1) if temblor else 0)
    sombra(c, x, suelo, sp.width * 0.8)
    if corre:
        sp = sp.rotate(-8 + 4 * math.sin(tl * 10), resample=Image.NEAREST, expand=True)
    pegar(c, sp, x + dx, suelo - sp.height / 2 + dy)


# ------------------------------------------------------------- recursos
A = {}


def recursos():
    A["paris"] = cargar("eiffel/01_estafador_torre.png")
    A["cafe"] = cargar("eiffel/02_periodico_cafe.png")
    A["cuarto"] = cargar("escena_prueba_tele_movil.png")
    A["estafador"] = limpiar(cargar("recortes/tele_estafador.png"))
    A["lee"] = limpiar(cargar("recortes/tele_periodico.png"))
    A["normal"] = limpiar(cargar("recortes/tele_normal.png"))
    A["movil"] = limpiar(cargar("recortes/movil_grunon.png"))
    # fondos sin personajes (encuadres de las partes vacías de cada escena)
    A["cielo_paris"] = recorte9x16(A["paris"], 700, 520, 560)          # la torre y el cielo
    A["cielo_cafe"] = recorte9x16(A["cafe"], 640, 440, 500)
    A["ciudad_noche"] = recorte9x16(A["cuarto"], 860, 330, 380)        # la ventana con la ciudad
    A["suelo_cuarto"] = recorte9x16(A["cuarto"], 540, 1760, 300)
    A["sello_vendida"] = a_pixel(HE.sello("VENDIDA"), 160)
    A["sello_falso"] = a_pixel(HE.sello("FALSO"), 120)
    A["sello_secreto"] = a_pixel(HE.sello("SECRETO", (60, 60, 60)), 150)
    A["doc"] = a_pixel(HE.documento(["MINISTERIO", "DE CORREOS", "Y TELÉGRAFOS"], "OFICIAL"), 110)
    A["billetes"] = a_pixel(HE.billetes(4), 90)
    A["billete"] = a_pixel(HE.billetes(1), 50)
    A["pez"] = a_pixel(HE.pez(), 80)
    A["diario"] = a_pixel(Hm.periodico(["LA TORRE", "¡CUESTA", "UNA FORTUNA!"]), 130)
    A["torre_peq"] = a_pixel(HE.torre(700), 70)


def bombilla(c, x, y, tl):
    im = Image.new("RGBA", (30, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    brillo = (255, 236, 120) if int(tl * 6) % 2 else (255, 250, 200)
    for k in range(8):
        a = k * math.pi / 4
        d.line((15 + math.cos(a) * 11, 14 + math.sin(a) * 11, 15 + math.cos(a) * 14, 14 + math.sin(a) * 14), fill=(255, 230, 120))
    d.ellipse((7, 6, 23, 22), fill=(40, 30, 30)); d.ellipse((8, 7, 22, 21), fill=brillo)
    d.rectangle((11, 22, 19, 28), fill=(40, 30, 30)); d.rectangle((12, 23, 18, 27), fill=(150, 150, 160))
    pegar(c, pop(pixelado(im, 5), tl), x, y)


def tarjeta(t1, t2, tl):
    a, b = R.txt_img(t1, R.fuente("pixel", 16), "blanco", "negro", contorno=True), R.txt_img(t2, R.fuente("pixel", 8), "amarillo", "negro", contorno=True)
    w = max(a.width, b.width) + 16
    c = R.caja(w, a.height + b.height + 16, borde="amarillo", relleno="caja")
    c.alpha_composite(a, ((c.width - a.width) // 2, 6)); c.alpha_composite(b, ((c.width - b.width) // 2, 10 + a.height))
    return pop(pixelado(c), tl)


def tinte(c, color, alfa):
    c.alpha_composite(Image.new("RGBA", (W, H), color + (alfa,)))


def barrotes(c, tl):
    d = ImageDraw.Draw(c)
    caida = int((1 - min(1, tl / 0.4)) * -1200)
    for k in range(8):
        x = 120 + k * 120
        d.rectangle((x, 300 + caida, x + 28, 1500), fill=(40, 40, 48))
        d.rectangle((x + 4, 300 + caida, x + 10, 1500), fill=(110, 110, 124))


# ------------------------------------------------------------- escenas (una por frase)
SUELO = 1500


def e0(c, tl, dur):
    c.paste(camara(A["paris"], tl, dur, 1.0, 1.15, 0, -0.4))
    if tl > dur * 0.5:
        k = max(1.0, 2.6 - (tl - dur * 0.5) * 8)
        pegar(c, escalar(A["sello_vendida"], k), W / 2 + 60, 760)


def e1(c, tl, dur):
    c.paste(camara(A["cielo_paris"], tl, dur, 1.0, 1.08))
    personaje(c, A["estafador"], W / 2, SUELO, tl, escala=1.1)
    pegar(c, tarjeta("VICTOR LUSTIG", "ESTAFADOR PROFESIONAL", tl), W / 2, 420)


def e2(c, tl, dur):
    c.paste(camara(A["cafe"], tl, dur, 1.0, 1.25, -0.3, 0.3))
    if tl > 0.3:
        pegar(c, pop(A["diario"].rotate(-6, expand=True, resample=Image.NEAREST), tl - 0.3), W / 2 + 120, 560)


def e3(c, tl, dur):
    c.paste(camara(A["ciudad_noche"], tl, dur, 1.0, 1.06))
    tinte(c, (10, 6, 30), 70)
    personaje(c, A["estafador"], W / 2, SUELO, tl, escala=1.1)
    bombilla(c, W / 2 + 40, 600, tl)


def e4(c, tl, dur):
    c.paste(camara(A["cielo_cafe"], tl, dur, 1.05, 1.12))
    tinte(c, (10, 6, 30), 60)
    personaje(c, A["estafador"], 270, SUELO, tl, escala=0.85)
    pegar(c, pop(A["doc"].rotate(5, expand=True, resample=Image.NEAREST), tl), 720, 900)
    if tl > dur * 0.55:
        pegar(c, pop(A["sello_falso"], tl - dur * 0.55), 740, 780)


def e5(c, tl, dur):
    c.paste(camara(A["cielo_paris"], tl, dur, 1.1, 1.0))
    d = ImageDraw.Draw(c)
    for k in range(6):
        u = min(1, max(0, (tl - k * 0.15) / 0.8))
        if u <= 0:
            continue
        x = 150 + k * 160 + 30 * math.sin(tl * 3 + k)
        y = 1700 - 1200 * u
        sob = Image.new("RGBA", (34, 24), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sob)
        sd.rectangle((0, 0, 33, 23), fill=(60, 50, 40)); sd.rectangle((1, 1, 32, 22), fill=(250, 244, 230))
        sd.line((1, 1, 17, 13, 32, 1), fill=(170, 160, 140)); sd.rectangle((15, 11, 19, 15), fill=(200, 40, 50))
        pegar(c, pixelado(sob, 4).rotate(12 * math.sin(tl * 2 + k), expand=True, resample=Image.NEAREST), x, y)


def e6(c, tl, dur):
    c.paste(camara(A["suelo_cuarto"], tl, dur, 1.0, 1.05))
    tinte(c, (40, 20, 10), 50)
    personaje(c, A["estafador"], W / 2, 1180, tl, escala=0.75)
    for i, x in enumerate((180, 400, 680, 900)):
        personaje(c, A["movil"], x, SUELO + 40, tl + i * 0.4, escala=0.75)
    u = min(1, tl / (dur * 0.7))
    t = A["torre_peq"].copy()
    t.putalpha(Image.eval(t.getchannel("A"), lambda a: int(a * (1 - u))))
    pegar(c, t, W / 2, 420)
    if u > 0.4:
        pegar(c, texto_px("¡CHATARRA!", 16, "amarillo"), W / 2, 420)


def e7(c, tl, dur):
    c.paste(camara(A["ciudad_noche"], tl, dur, 1.0, 1.1))
    tinte(c, (10, 6, 30), 90)
    personaje(c, A["estafador"], W / 2, 1650, tl, escala=1.6, bote=False)
    k = max(1.0, 2.4 - tl * 8)
    pegar(c, escalar(A["sello_secreto"], k), W / 2, 420)


def e8(c, tl, dur):
    c.paste(camara(A["paris"], tl, dur, 1.15, 1.0, 0, 0.3))
    x = W + 200 - (W / 2) * min(1, tl / 0.8)
    personaje(c, A["movil"], x, SUELO + 80, tl, escala=0.8)
    if tl > dur * 0.55:
        pegar(c, pop(A["pez"], tl - dur * 0.55), W - 260, 520)
        pegar(c, pop(texto_px("POISSON = PEZ", 8, "blanco"), tl - dur * 0.55), W - 300, 400)


def e9(c, tl, dur):
    c.paste(camara(A["suelo_cuarto"], tl, dur, 1.05, 1.0))
    tinte(c, (40, 20, 10), 60)
    personaje(c, A["estafador"], 290, SUELO, tl, escala=0.85)
    personaje(c, A["movil"], 800, SUELO, tl + 0.5, escala=0.9)
    u = min(1, tl / (dur * 0.6))
    pegar(c, A["billetes"], 760 - 420 * u, 1180 - math.sin(u * math.pi) * 200)
    pegar(c, texto_px("¿UN SOBORNO?", 16, "amarillo"), W / 2, 420)


def e10(c, tl, dur):
    c.paste(camara(A["cielo_paris"], tl, dur, 1.0, 1.1, 0.6, 0))
    tinte(c, (60, 20, 40), 50)
    x = -200 + (W + 400) * min(1, tl / dur)
    personaje(c, A["estafador"], x, SUELO, tl, escala=0.9, corre=True)
    for k in range(6):
        bx = x - 160 - k * 90; by = 1100 - k * 60 + 50 * math.sin(tl * 6 + k)
        pegar(c, A["billete"].rotate(30 * math.sin(tl * 5 + k), expand=True, resample=Image.NEAREST), bx, by)
    pegar(c, texto_px("A AUSTRIA", 16, "blanco"), W / 2, 420)


def e11(c, tl, dur):
    c.paste(camara(A["cielo_cafe"], tl, dur, 1.0, 1.05))
    tinte(c, (60, 0, 20), 70)
    personaje(c, A["movil"], W / 2, 1600, tl, escala=2.2, bote=False, temblor=6)
    rubor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(rubor).ellipse((W / 2 - 160, 1000, W / 2 + 160, 1120), fill=(255, 40, 60, 90))
    c.alpha_composite(rubor)
    pegar(c, texto_px("NO LO DENUNCIA", 16, "blanco"), W / 2, 420)


def e12(c, tl, dur):
    c.paste(camara(A["paris"], tl, dur, 1.0, 1.18, 0, -0.5))
    k = max(1.0, 2.6 - tl * 8)
    pegar(c, escalar(texto_px("OTRA VEZ", 24, "amarillo"), k), W / 2, 420)


def e13(c, tl, dur):
    c.paste(camara(A["cielo_paris"], tl, dur, 1.1, 1.0))
    tinte(c, (255, 40, 40) if int(tl * 6) % 2 else (40, 80, 255), 70)
    x = 200 + 500 * min(1, tl / dur)
    personaje(c, A["estafador"], x, SUELO, tl, escala=0.85, corre=True, temblor=4)
    pegar(c, texto_px("¡LA POLICÍA!", 16, "blanco"), W / 2, 420)


def e14(c, tl, dur):
    c.paste(camara(A["ciudad_noche"], tl, dur, 1.0, 1.1, -0.5, 0))
    tinte(c, (10, 6, 30), 80)
    x = W / 2 + (W) * min(1, tl / (dur * 0.8))
    personaje(c, A["estafador"], x, SUELO, tl, escala=0.9, corre=True)
    pegar(c, texto_px("¡POR LOS PELOS!", 16, "amarillo"), W / 2, 420)


def e15(c, tl, dur):
    c.paste(camara(A["ciudad_noche"], tl, dur, 1.1, 1.0))
    tinte(c, (10, 6, 30), 110)
    personaje(c, A["estafador"], W / 2, SUELO, tl, escala=1.1, bote=False)
    barrotes(c, tl)
    pegar(c, texto_px("ALCATRAZ", 24, "amarillo"), W / 2, 420)


def e16(c, tl, dur):
    c.paste(camara(A["cuarto"], tl, dur, 1.0, 1.06))
    pegar(c, texto_px("¿TÚ HABRÍAS", 16, "rosa"), W / 2, 360)
    pegar(c, texto_px("PICADO?", 16, "rosa"), W / 2, 460)
    d = ImageDraw.Draw(c)
    rng = np.random.default_rng(3)
    cols = [(255, 90, 140), (80, 220, 255), (255, 214, 80), (120, 230, 140)]
    for i in range(50):
        x0 = rng.uniform(0, W); v = rng.uniform(500, 900)
        y = -40 + v * tl - (i % 7) * 60
        if 0 <= y <= H:
            x = x0 + math.sin(tl * 4 + i) * 30
            d.rectangle((x, y, x + 12, y + 8), fill=cols[i % 4])


ESCENAS = [e0, e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13, e14, e15, e16]
assert len(ESCENAS) == len(HE.BEATS)


def subtitulo(palabras, k):
    f = R.fuente("texto", 30)
    piezas = [R.txt_img(p.upper(), f, "amarillo" if i == k else "blanco", "negro", contorno=True) for i, p in enumerate(palabras[:k + 1])]
    w = sum(p.width for p in piezas) + 6 * (len(piezas) - 1)
    hh = max(p.height for p in piezas)
    out = Image.new("RGBA", (270, hh + 8), (0, 0, 0, 0))
    ImageDraw.Draw(out).rectangle((0, 0, 269, out.height), fill=(10, 8, 18, 140))
    x = (270 - w) // 2
    for p in piezas:
        out.alpha_composite(p, (x, 4)); x += p.width + 6
    return pixelado(out)


def render():
    os.makedirs(SALIDA, exist_ok=True)
    t = 0.05
    beats, clips, palabras_t = [], [], []
    for b in HE.BEATS:
        a = audio.voz(b["say"]); d_ = len(a) / audio.VOZ_SR
        beats.append(dict(b, t0=t, dur=d_ + 0.12)); clips.append((t, a))
        palabras_t.append(Hm.PL.tiempos_palabras(b["say"], t, d_))
        t += d_ + 0.12
    total = t + 0.5
    print(f"[{SLUG}] {total:.1f}s", flush=True)
    voz = np.zeros(int(total * audio.VOZ_SR) + 100, np.float32)
    for t0, a in clips:
        i = int(t0 * audio.VOZ_SR); voz[i:i + len(a)] += a
    wav_voz = os.path.join(SALIDA, "voz.wav"); audio.sf.write(wav_voz, voz, audio.VOZ_SR)
    mus = audio.chiptune(total + 1, semilla=6, bpm=104, tono="F")
    for b in beats:
        if "sfx" in b:
            off, nombre = b["sfx"]
            off = b["dur"] * float(off[:-1]) / 100 if isinstance(off, str) else off
            s = audio.efecto(nombre)
            i = int((b["t0"] + off) * audio.MUS_SR); j = min(len(mus), i + len(s)); mus[i:j] += s[:j - i] * 1.7
    wav_mus = os.path.join(SALIDA, "musica.wav"); audio.sf.write(wav_mus, mus, audio.MUS_SR)
    recursos()
    bayer = np.tile(R._b8, (H // 8 + 1, W // 8 + 1))[:H, :W]
    muestra = "--muestra" in sys.argv
    mp4 = os.path.join(SALIDA, "mudo.mp4")
    ff = None if muestra else subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", mp4], stdin=subprocess.PIPE)
    cuadros = range(int(total * FPS)) if not muestra else [int((b["t0"] + b["dur"] * 0.6) * FPS) for b in beats]
    for fi in cuadros:
        tg = fi / FPS
        kb = max((i for i, b in enumerate(beats) if b["t0"] <= tg), default=0)
        b = beats[kb]; tl = max(0.0, tg - b["t0"])
        c = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        ESCENAS[kb](c, tl, b["dur"])
        pts = palabras_t[kb]
        k_act = max([i for i, (t0, _) in enumerate(pts) if tg >= t0], default=-1)
        if k_act >= 0:
            g0 = (k_act // 3) * 3
            sub = subtitulo([p for _, p in pts[g0:g0 + 3]], k_act - g0)
            c.alpha_composite(sub, (0, 1300 + (4 if tg - pts[k_act][0] < 0.07 else 0)))
        arr = np.asarray(c.convert("RGB"))
        temblor, flash = Hm.momento_clave(b, tl)
        if temblor:
            rng = np.random.default_rng(fi)
            arr = np.roll(arr, (int(rng.integers(-3, 4)) * 4, int(rng.integers(-3, 4)) * 4), (0, 1))
        if flash:
            arr = (arr * (1 - flash) + 255 * flash).astype(np.uint8)
        if kb > 0 and tl < 0.14:
            arr = arr.copy(); arr[bayer < 1 - tl / 0.14] = (12, 8, 22)
        if muestra:
            Image.fromarray(arr).resize((270, 480), Image.NEAREST).save(os.path.join(SALIDA, f"muestra_{kb:02d}.png")); continue
        ff.stdin.write(arr.tobytes())
    if muestra:
        return
    ff.stdin.close(); ff.wait()
    final = os.path.join(SALIDA, f"{SLUG}.mp4")
    filtro = (f"[1:a]aresample=48000,{audio.CADENA_VOZ},pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];"
              "[2:a]volume=0.3[m];[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=300[md];"
              "[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-i", wav_voz, "-i", wav_mus, "-filter_complex", filtro,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                    "-shortest", final], check=True)
    for f_ in (mp4, wav_voz, wav_mus):
        os.remove(f_)
    print(f"[{SLUG}] OK → {final} ({total:.1f}s)", flush=True)


if __name__ == "__main__":
    render()
