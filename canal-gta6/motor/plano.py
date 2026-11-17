# -*- coding: utf-8 -*-
"""Estilo PLANO (ilustración vectorial + motion graphics), a resolución completa.

Recursos del estilo: ilustración grande con halo y anillos girando, tarjetas
que entran volando y giran, palabras gigantes en letra condensada, subtítulos
palabra a palabra (la última en color), empujes de cámara y destellos.
Todas las ilustraciones son propias: el "villano" es la mascota del canal disfrazada,
no se dibuja ningún personaje de Marvel.

Uso:  python3 plano.py      → salida/demo-estilo-plano/demo-estilo-plano.mp4
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import doomsday  # noqa: F401  (registra la pronunciación de nombres de Marvel)

audio.VELOCIDAD = 1.1
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FUENTES = os.path.join(RAIZ, "fuentes")
SALIDA = os.path.join(RAIZ, "salida")
W, H, FPS = 1080, 1920, 30
SS = 2  # superresolución para dibujar ilustraciones suaves

VERDE = (88, 230, 120)
VERDE_OSC = (24, 70, 44)
CAPA = (34, 96, 58)
CAPA_OSC = (20, 60, 38)
METAL = (176, 184, 190)
METAL_OSC = (110, 118, 126)
ORO = (222, 176, 70)
BLANCO = (255, 255, 255)
NEGRO = (10, 12, 14)
ROJO = (206, 44, 52)


def anton(tam):
    return ImageFont.truetype(os.path.join(FUENTES, "Anton-Regular.ttf"), tam)


def ease_out(u):
    u = min(max(u, 0), 1)
    return 1 - (1 - u) ** 3


def ease_back(u):
    u = min(max(u, 0), 1)
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def suave(w, h, dibujar):
    """Dibuja a doble tamaño y reduce: bordes suaves (antialias)."""
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    dibujar(ImageDraw.Draw(im), SS)
    return im.resize((w, h), Image.LANCZOS)


# ------------------------------------------------------------- ilustraciones
def tele_villana(ojos=1.0):
    """La mascota del canal (la tele) disfrazada de villano: capa, corona y ojos que brillan.
    Personaje original: no copia a ningún personaje existente."""
    def dib(d, s):
        S = lambda *v: [x * s for x in v]
        # capa morada detrás
        d.polygon(S(150, 420, 750, 420, 860, 1000, 40, 1000), fill=(70, 34, 110))
        d.polygon(S(250, 420, 650, 420, 700, 1000, 200, 1000), fill=(96, 50, 150))
        # patas
        d.rounded_rectangle(S(300, 840, 360, 1000), radius=20 * s, fill=(60, 64, 74))
        d.rounded_rectangle(S(540, 840, 600, 1000), radius=20 * s, fill=(60, 64, 74))
        # antenas
        d.line(S(380, 250, 300, 90), fill=(150, 150, 160), width=14 * s)
        d.line(S(520, 250, 610, 80), fill=(150, 150, 160), width=14 * s)
        d.ellipse(S(270, 60, 330, 120), fill=(255, 210, 80))
        d.ellipse(S(580, 50, 640, 110), fill=(255, 90, 140))
        # cuerpo de la tele
        d.rounded_rectangle(S(130, 240, 770, 860), radius=90 * s, fill=(232, 222, 200))
        d.rounded_rectangle(S(130, 780, 770, 860), radius=40 * s, fill=(200, 160, 140))
        # pantalla
        d.rounded_rectangle(S(190, 300, 640, 760), radius=60 * s, fill=(18, 24, 34))
        for y in range(320, 750, 22):
            d.line(S(210, y, 620, y), fill=(26, 34, 46), width=4 * s)
        # cejas enfadadas y ojos
        d.polygon(S(240, 430, 380, 470, 375, 495, 235, 455), fill=(0, 0, 0))
        d.polygon(S(450, 470, 590, 430, 595, 455, 455, 495), fill=(0, 0, 0))
        g = tuple(int(c * ojos + 30 * (1 - ojos)) for c in VERDE)
        d.rounded_rectangle(S(255, 500, 365, 540), radius=14 * s, fill=g)
        d.rounded_rectangle(S(465, 500, 575, 540), radius=14 * s, fill=g)
        # sonrisa malvada
        d.arc(S(300, 560, 530, 690), 20, 160, fill=g, width=14 * s)
        # botones laterales
        d.ellipse(S(670, 360, 730, 420), fill=(255, 210, 80))
        d.ellipse(S(670, 450, 730, 510), fill=(70, 200, 240))
        # corona
        d.polygon(S(300, 250, 300, 170, 360, 215, 415, 140, 470, 215, 530, 170, 530, 250), fill=ORO)
        for x in (360, 415, 470):
            d.ellipse(S(x - 12, 222, x + 12, 246), fill=(200, 40, 60))
    im = suave(900, 1000, dib)
    if ojos > 0.3:
        brillo = Image.new("RGBA", im.size, (0, 0, 0, 0))
        dd = ImageDraw.Draw(brillo)
        for x0 in (255, 465):
            dd.rounded_rectangle((x0 - 14, 488, x0 + 124, 552), radius=20, fill=VERDE + (int(170 * ojos),))
        im = Image.alpha_composite(brillo.filter(ImageFilter.GaussianBlur(18)), im)
    return im


def tarjeta(titulo, sub, c1, c2, icono):
    """Tarjeta tipo póster (diseño propio): degradado, icono simple, título."""
    w, h = 520, 720

    def dib(d, s):
        for y in range(h):
            u = y / h
            c = tuple(int(c1[i] * (1 - u) + c2[i] * u) for i in range(3))
            d.line([(0, y * s), (w * s, y * s)], fill=c, width=s)
        cx, cy = w // 2, 300
        if icono == "rayo":       # héroe: un rayo dentro de un círculo
            d.ellipse([(cx - 150) * s, (cy - 150) * s, (cx + 150) * s, (cy + 150) * s], fill=(255, 255, 255, 40))
            d.polygon([(cx + 30) * s, (cy - 130) * s, (cx - 70) * s, (cy + 20) * s, (cx - 5) * s, (cy + 20) * s,
                       (cx - 40) * s, (cy + 140) * s, (cx + 80) * s, (cy - 30) * s, (cx + 10) * s, (cy - 30) * s], fill=ORO)
        elif icono == "corona":   # villano: corona con gemas
            d.ellipse([(cx - 150) * s, (cy - 150) * s, (cx + 150) * s, (cy + 150) * s], fill=(255, 255, 255, 30))
            d.polygon([(cx - 120) * s, (cy + 70) * s, (cx - 120) * s, (cy - 60) * s, (cx - 60) * s, (cy) * s, (cx) * s, (cy - 100) * s,
                       (cx + 60) * s, (cy) * s, (cx + 120) * s, (cy - 60) * s, (cx + 120) * s, (cy + 70) * s], fill=ORO)
            for x in (cx - 60, cx, cx + 60):
                d.ellipse([(x - 16) * s, (cy + 22) * s, (x + 16) * s, (cy + 54) * s], fill=VERDE)
        elif icono == "comic":
            for i in range(3):
                d.rounded_rectangle([60 * s, (120 + i * 130) * s, (w - 60) * s, (230 + i * 130) * s], radius=10 * s,
                                    outline=NEGRO, width=6 * s, fill=(250, 236, 200))
            d.text((cx * s - 60 * s, 140 * s), "¡ZAS!", fill=ROJO, font=anton(60 * s))
        d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=28 * s, outline=(255, 255, 255, 90), width=4 * s)
    im = suave(w, h, dib)
    # esquinas redondeadas
    m = suave(w, h, lambda d, s: d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=28 * s, fill=(255, 255, 255, 255)))
    im.putalpha(Image.fromarray(np.minimum(np.array(im.getchannel("A")), np.array(m.getchannel("A")))))
    d = ImageDraw.Draw(im)
    f = anton(78)
    tw = d.textlength(titulo, font=f)
    d.text(((w - tw) / 2 + 3, 538 + 4), titulo, font=f, fill=(0, 0, 0, 160))
    d.text(((w - tw) / 2, 538), titulo, font=f, fill=BLANCO)
    f2 = anton(44)
    sw = d.textlength(sub, font=f2)
    d.text(((w - sw) / 2, 630), sub, font=f2, fill=ORO)
    return im


def castillo():
    def dib(d, s):
        S = lambda *v: [x * s for x in v]
        d.rectangle(S(150, 300, 650, 700), fill=(52, 60, 70))
        for x in range(150, 650, 60):
            d.rectangle(S(x, 260, x + 35, 300), fill=(52, 60, 70))
        for tx in (60, 600):
            d.rectangle(S(tx, 160, tx + 140, 700), fill=(40, 46, 56))
            d.polygon(S(tx - 20, 160, tx + 70, 40, tx + 160, 160), fill=CAPA)
        d.rounded_rectangle(S(340, 480, 460, 700), radius=60 * s, fill=(20, 24, 30))
        for x in (230, 520):
            d.rounded_rectangle(S(x, 380, x + 50, 450), radius=20 * s, fill=(255, 210, 120))
    return suave(800, 720, dib)


def chincheta():
    def dib(d, s):
        S = lambda *v: [x * s for x in v]
        d.ellipse(S(20, 0, 180, 160), fill=VERDE)
        d.polygon(S(40, 120, 160, 120, 100, 260), fill=VERDE)
        d.ellipse(S(65, 45, 135, 115), fill=(10, 40, 24))
    return suave(200, 260, dib)


# ------------------------------------------------------------- fondo
def fondo_radial():
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt((x - W / 2) ** 2 + (y - H * 0.42) ** 2) / (H * 0.6)
    r = np.clip(r, 0, 1)
    c0, c1 = np.array([60, 150, 92]), np.array([6, 14, 10])
    img = c0 * (1 - r[..., None]) ** 1.6 + c1 * (1 - (1 - r[..., None]) ** 1.6)
    return Image.fromarray(img.astype(np.uint8)).convert("RGBA")


def anillos():
    tam = 1700

    def dib(d, s):
        c = tam * s // 2
        for k, r in enumerate((300, 430, 560, 690, 820)):
            rr = r * s
            if k % 2:
                for a in range(0, 360, 6):
                    d.arc([c - rr, c - rr, c + rr, c + rr], a, a + 3, fill=(140, 230, 160, 70), width=3 * s)
            else:
                d.ellipse([c - rr, c - rr, c + rr, c + rr], outline=(140, 230, 160, 45), width=3 * s)
    return suave(tam, tam, dib)


# ------------------------------------------------------------- subtítulos palabra a palabra
def caption(palabras, k_actual, u_pop):
    """Hasta 4 palabras; aparecen según se dicen y la última va en verde."""
    f = anton(118)
    vis = palabras[:k_actual + 1]
    im = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lineas, act = [], []
    for p in vis:
        prueba = " ".join(act + [p])
        if d.textlength(prueba.upper(), font=f) > W - 140 and act:
            lineas.append(act); act = [p]
        else:
            act.append(p)
    lineas.append(act)
    y = 0
    for li, ln in enumerate(lineas):
        texto = " ".join(ln).upper()
        x = (W - d.textlength(texto, font=f)) / 2
        for j, p in enumerate(ln):
            ultima = li == len(lineas) - 1 and j == len(ln) - 1
            col = VERDE if ultima else BLANCO
            dy = int((1 - ease_back(u_pop)) * 30) if ultima else 0
            d.text((x + 5, y + 6 + dy), p.upper(), font=f, fill=(0, 0, 0, 200))
            d.text((x, y + dy), p.upper(), font=f, fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
            x += d.textlength(p.upper() + " ", font=f)
        y += 135
    return im


def tiempos_palabras(frase, inicio, dur):
    palabras = frase.split()
    pesos = [len(p) + 2 for p in palabras]
    tot = sum(pesos)
    t, out = inicio, []
    for p, w in zip(palabras, pesos):
        out.append((t, p))
        t += dur * w / tot
    return out


# ------------------------------------------------------------- beats de la demo
BEATS = [
    dict(a="aparece", palabra="VILLANO", say="Robert Downey Jr. vuelve a Marvel… ¡como el villano!"),
    dict(a="giro", palabra="CAMBIO DE BANDO", say="Fue Iron Man durante once años… y ahora se cambia de bando."),
    dict(a="zoom", palabra="VÍCTOR VON DOOM", say="Se llama Víctor von Doom."),
    dict(a="comics", palabra="1962", say="Nació en los cómics en 1962,"),
    dict(a="mapa", palabra="LATVERIA", say="y es el rey de su propio país: Latveria."),
]


def render():
    slug = "demo-estilo-plano"
    base = os.path.join(SALIDA, slug)
    os.makedirs(base, exist_ok=True)
    t = 0.05
    beats, clips, palabras_t = [], [], []
    for b in BEATS:
        a = audio.voz(b["say"])
        d_ = len(a) / audio.VOZ_SR
        beats.append(dict(b, t0=t, dur=d_ + 0.15))
        clips.append((t, a))
        palabras_t.append(tiempos_palabras(b["say"], t, d_))
        t += d_ + 0.15
    total = t + 0.5
    print(f"[{slug}] {total:.1f}s", flush=True)
    voz = np.zeros(int(total * audio.VOZ_SR) + 100, np.float32)
    for t0, a in clips:
        i = int(t0 * audio.VOZ_SR); voz[i:i + len(a)] += a
    wav_voz = os.path.join(base, "voz.wav"); audio.sf.write(wav_voz, voz, audio.VOZ_SR)
    mus = audio.musica(total + 1, semilla=3, bpm=96, tono="D")
    efectos = [(beats[0]["t0"] + 0.9, audio.efecto("boom")), (beats[1]["t0"] + 0.1, audio.whoosh(1)),
               (beats[1]["t0"] + beats[1]["dur"] * 0.45, audio.efecto("golpe")), (beats[2]["t0"] + 0.1, audio.efecto("subida")),
               (beats[3]["t0"] + 0.1, audio.whoosh(2)), (beats[4]["t0"] + 0.55, audio.efecto("golpe"))]
    for te, s in efectos:
        i = int(te * audio.MUS_SR); j = min(len(mus), i + len(s)); mus[i:j] += s[:j - i] * 1.6
    wav_mus = os.path.join(base, "musica.wav"); audio.sf.write(wav_mus, mus, audio.MUS_SR)

    print(f"[{slug}] ilustraciones…", flush=True)
    fondo = fondo_radial()
    ring = anillos()
    busto = tele_villana(1.0)
    busto_ap = tele_villana(0.2)
    t_heroe = tarjeta("HÉROE", "2008 – 2019", (40, 80, 170), (14, 24, 70), "rayo")
    t_villano = tarjeta("VILLANO", "2026", (40, 120, 70), (8, 30, 18), "corona")
    t_comic = [tarjeta(f"Nº {n}", "1962", (240, 200, 90), (150, 90, 30), "comic") for n in (5, 5, 5)]
    cast = castillo(); pin = chincheta()
    pal_img = {}

    mp4 = os.path.join(base, "mudo.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", mp4], stdin=subprocess.PIPE)
    kb = 0
    for fi in range(int(total * FPS)):
        tg = fi / FPS
        while kb + 1 < len(beats) and tg >= beats[kb + 1]["t0"]:
            kb += 1
        b = beats[kb]; tl = tg - b["t0"]; dur = b["dur"]
        frame = fondo.copy()
        rr = ring.rotate(tg * 8, resample=Image.BICUBIC)
        frame.alpha_composite(rr, ((W - rr.width) // 2, int(H * 0.42) - rr.height // 2))
        escena = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        a = b["a"]
        destello = 0
        if a == "aparece":
            u = ease_out(tl / 0.8)
            im = busto if tl > 0.9 else busto_ap
            escena.alpha_composite(im, ((W - im.width) // 2, int(1300 - im.height * 0.95 * u + 200 * (1 - u))))
            if 0.9 < tl < 1.05:
                destello = 120
        elif a == "giro":
            escena.alpha_composite(busto, ((W - busto.width) // 2, 1300 - int(busto.height * 0.95)))
            veil = Image.new("RGBA", (W, H), (0, 0, 0, 120)); escena.alpha_composite(veil)
            mitad = dur * 0.45
            u_in = ease_back(tl / 0.5)
            x = int(-600 + (W / 2 + 600) * u_in) - t_heroe.width // 2
            # volteo: se estrecha en horizontal y cambia de cara
            fase = (tl - (mitad - 0.2)) / 0.4
            if fase < 0.5:
                carta, k = t_heroe, max(0.02, 1 - max(0, fase) * 2)
            else:
                carta, k = t_villano, min(1, (fase - 0.5) * 2)
            c = carta.resize((max(2, int(carta.width * k)), carta.height), Image.BICUBIC)
            ang = (1 - min(1, tl / 0.5)) * 25
            c = c.rotate(ang, resample=Image.BICUBIC, expand=True)
            escena.alpha_composite(c, (x + (t_heroe.width - c.width) // 2, 330))
        elif a == "zoom":
            z = 1 + 0.9 * ease_out(tl / 1.2)
            pulso = 0.7 + 0.3 * math.sin(tg * 8)
            im = tele_villana(pulso) if fi % 2 == 0 or not hasattr(render, "_cache") else render._cache
            render._cache = im
            im = im.resize((int(im.width * z), int(im.height * z)), Image.BILINEAR)
            cx, cy = W // 2, 700
            escena.alpha_composite(im, (int(cx - 415 * z), int(cy - 520 * z)))
        elif a == "comics":
            for i, c in enumerate(t_comic):
                u = ease_back((tl - i * 0.15) / 0.5)
                if u <= 0:
                    continue
                ang = (i - 1) * 14 * u
                cc = c.resize((int(c.width * 0.8), int(c.height * 0.8)), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC, expand=True)
                x = W // 2 + (i - 1) * 230 * u - cc.width // 2
                y = 420 + abs(i - 1) * 40 + int((1 - u) * 900)
                escena.alpha_composite(cc, (int(x), int(y)))
        elif a == "mapa":
            u = ease_out(tl / 0.5)
            escena.alpha_composite(cast, ((W - cast.width) // 2, int(520 + (1 - u) * 300)))
            up = ease_back((tl - 0.3) / 0.35)
            if tl > 0.3:
                escena.alpha_composite(pin, (W // 2 - 100, int(220 + 200 * min(1, up))))
        # cámara: empuje lento + golpe al empezar el beat
        zc = 1.0 + 0.04 * (tl / dur) + 0.05 * math.exp(-tl * 10)
        if zc > 1.001:
            nw, nh = int(W * zc), int(H * zc)
            escena = escena.resize((nw, nh), Image.BILINEAR).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        frame.alpha_composite(escena)
        # palabra grande
        pk = b["palabra"]
        if pk not in pal_img:
            f = anton(210)
            tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            while tmp.textlength(pk, font=f) > W - 120:
                f = anton(f.size - 10)
            l, tt, r, bb = f.getbbox(pk)
            im = Image.new("RGBA", (r - l + 40, bb - tt + 40), (0, 0, 0, 0))
            di = ImageDraw.Draw(im)
            di.text((20 - l + 6, 20 - tt + 8), pk, font=f, fill=(0, 0, 0, 180))
            di.text((20 - l, 20 - tt), pk, font=f, fill=VERDE, stroke_width=6, stroke_fill=(0, 0, 0))
            pal_img[pk] = im
        im = pal_img[pk]
        k = 1 + 0.6 * (1 - ease_back(tl / 0.3))
        im2 = im.resize((int(im.width * k), int(im.height * k)), Image.BILINEAR)
        frame.alpha_composite(im2, ((W - im2.width) // 2, 1150 - im2.height // 2))
        # subtítulo palabra a palabra (grupos de 4)
        pts = palabras_t[kb]
        k_act = max([i for i, (t0, _) in enumerate(pts) if tg >= t0], default=-1)
        if k_act >= 0:
            g0 = (k_act // 4) * 4
            grupo = [p for _, p in pts[g0:g0 + 4]]
            cap = caption(grupo, k_act - g0, (tg - pts[k_act][0]) / 0.18)
            frame.alpha_composite(cap, (0, 1380))
        if tg < 3:
            f = ImageFont.truetype(os.path.join(FUENTES, "Jersey10-Regular.ttf"), 44)
            dd = ImageDraw.Draw(frame)
            txt = "Canal de fans. Sin relación con Marvel ni Disney."
            dd.text(((W - dd.textlength(txt, font=f)) / 2, 1700), txt, font=f, fill=(200, 210, 205))
        arr = np.asarray(frame.convert("RGB"))
        if destello:
            arr = (arr.astype(np.int16) + destello * (255 - arr.astype(np.int16)) // 255).astype(np.uint8)
        ff.stdin.write(arr.tobytes())
    ff.stdin.close(); ff.wait()
    final = os.path.join(base, f"{slug}.mp4")
    filtro = (f"[1:a]aresample=48000,{audio.CADENA_VOZ},pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];"
              "[2:a]volume=0.35[m];[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=300[md];"
              "[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-i", wav_voz, "-i", wav_mus, "-filter_complex", filtro,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                    "-shortest", final], check=True)
    for f_ in (mp4, wav_voz, wav_mus):
        os.remove(f_)
    print(f"[{slug}] OK → {final}", flush=True)


if __name__ == "__main__":
    render()
