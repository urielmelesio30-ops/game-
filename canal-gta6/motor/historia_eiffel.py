# -*- coding: utf-8 -*-
"""Historia real animada en 2D: el hombre que «vendió» la Torre Eiffel (1925)."""
import math, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import historia as Hm
from historia import (A, C, W, H, persona, andar, ease, back, texto_grande, pegar, escalar, sombra, suave, anton)

audio.PRONUNCIA[:0] = [("Victor Lustig", "Víctor Lústig"), ("Lustig", "Lústig"), ("André Poisson", "André Puasón"),
                       ("Poisson", "Puasón"), ("Alcatraz", "Alcatrás")]
Hm.SALIDA = os.path.join(Hm.PL.SALIDA, "16-torre-eiffel-estafa")


def torre(h=1100):
    """Torre de hierro de celosía (silueta propia; el monumento es de dominio público)."""
    w = int(h * 0.62)

    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        col, col2 = (92, 82, 78), (120, 108, 100)
        cx = w / 2
        pts_i = [(cx - w * 0.48, h), (cx - w * 0.30, h * 0.72), (cx - w * 0.14, h * 0.45), (cx - w * 0.05, h * 0.12), (cx, 0)]
        pts_d = [(2 * cx - x, y) for x, y in pts_i]
        d.polygon(S(*sum(pts_i, ()), *sum(reversed(pts_d), ())), fill=col)
        d.chord(S(cx - w * 0.26, h * 0.80, cx + w * 0.26, h * 1.12), 180, 360, fill=(232, 210, 170, 0) if False else (200, 214, 236))
        for y, ww in ((h * 0.72, 0.36), (h * 0.45, 0.20)):
            d.rectangle(S(cx - w * ww, y - 14, cx + w * ww, y + 14), fill=col2)
        for k in range(14):
            y = h * k / 14
            d.line(S(cx - w * 0.5 * (1 - k / 14) ** 1.3, y, cx + w * 0.5 * (1 - k / 14) ** 1.3, y + h / 14), fill=col2, width=3 * s)
            d.line(S(cx + w * 0.5 * (1 - k / 14) ** 1.3, y, cx - w * 0.5 * (1 - k / 14) ** 1.3, y + h / 14), fill=col2, width=3 * s)
    return suave(w, h, dib)


def sello(txt, color=(210, 40, 50)):
    f = anton(120)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = int(tmp.textlength(txt, font=f))
    im = Image.new("RGBA", (tw + 80, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, im.width - 5, 195), radius=20, outline=color + (255,), width=12)
    d.text((40, 18), txt, font=f, fill=color + (255,))
    return im.rotate(-12, expand=True, resample=Image.BICUBIC)


def documento(lineas, sello_txt=None):
    im = Image.new("RGBA", (520, 680), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 519, 679), fill=(246, 240, 224), outline=(180, 170, 150), width=4)
    f = anton(54); y = 40
    for ln in lineas:
        d.text((260 - d.textlength(ln, font=f) / 2, y), ln, font=f, fill=(40, 40, 60)); y += 70
    for yy in range(y + 30, 600, 40):
        d.rectangle((50, yy, 470, yy + 14), fill=(200, 194, 178))
    if sello_txt:
        d.ellipse((330, 470, 490, 630), outline=(30, 60, 140), width=8)
        d.text((356, 528), sello_txt, font=anton(40), fill=(30, 60, 140))
    return im


def billetes(n):
    im = Image.new("RGBA", (420, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(n):
        x, y = 30 + k * 14, 120 - k * 12
        d.rounded_rectangle((x, y, x + 320, y + 130), radius=10, fill=(120, 170, 110), outline=(70, 110, 70), width=5)
        d.ellipse((x + 130, y + 35, x + 190, y + 95), outline=(70, 110, 70), width=5)
    return im


def pez():
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        d.ellipse(S(40, 40, 300, 200), fill=(255, 160, 60))
        d.polygon(S(290, 120, 400, 40, 400, 200), fill=(240, 130, 40))
        d.ellipse(S(90, 90, 120, 120), fill=(255, 255, 255)); d.ellipse(S(100, 98, 116, 114), fill=(20, 20, 20))
    return suave(420, 240, dib)


_assets_base = Hm.assets


def assets_extra():
    _assets_base()
    A["torre"] = torre()
    A["torre_peq"] = torre(700)
    A["cielo"] = Hm.fondo_ciudad()
    A["hotel"] = hotel()
    A["pez"] = pez()


def hotel():
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        for i in range(40):
            u = i / 39
            c1, c2 = C["cielo1"], C["cielo2"]
            col = tuple(int(c2[k] * (1 - u) + c1[k] * u) for k in range(3))
            d.rectangle(S(0, 1300 * u, W, 1300 * u + 34), fill=col)
        d.rectangle(S(80, 360, 1000, 1300), fill=(226, 214, 190))
        d.rectangle(S(60, 330, 1020, 380), fill=(200, 186, 160))
        for x in range(150, 1000, 140):
            d.rectangle(S(x, 420, x + 60, 1300), fill=(240, 232, 214))
            for y in (480, 720, 960):
                d.rounded_rectangle(S(x + 70, y, x + 120, y + 130), radius=20 * s, fill=(110, 130, 170))
        d.rectangle(S(0, 1300, W, H), fill=(110, 110, 120))
    im = suave(W, H, dib)
    return im


LUSTIG = dict(ropa="traje", sombrero="bombin", bigote=True)
POISSON = dict(ropa=(70, 90, 70), pelo=(120, 90, 60))


# ------------------------------------------------------------- escenas
def e_vendida(fr, d, tl, dur):
    fr.alpha_composite(A["cielo"])
    pegar(fr, A["torre"], W / 2, 760)
    if tl > dur * 0.5:
        u = back((tl - dur * 0.5) / 0.3)
        pegar(fr, escalar(sello("VENDIDA"), max(0.05, 2.2 - 1.2 * min(1, u))), W / 2, 700)


def e_nombre(fr, d, tl, dur):
    fr.alpha_composite(A["paris"])
    pegar(fr, escalar(persona(**LUSTIG, brazo=(10, -40)), 1.6 + 0.08 * tl / dur), W / 2, 1050)
    u = back(tl / 0.45)
    tarjeta = Image.new("RGBA", (760, 200), (0, 0, 0, 0))
    td = ImageDraw.Draw(tarjeta)
    td.rounded_rectangle((0, 0, 759, 199), radius=26, fill=(20, 24, 40, 235), outline=(255, 214, 80), width=6)
    f = anton(80); t1 = "VICTOR LUSTIG"
    td.text((380 - td.textlength(t1, font=f) / 2, 22), t1, font=f, fill=(255, 255, 255))
    f2 = anton(48); t2 = "ESTAFADOR PROFESIONAL"
    td.text((380 - td.textlength(t2, font=f2) / 2, 118), t2, font=f2, fill=(255, 214, 80))
    pegar(fr, escalar(tarjeta, max(0.05, u)), W / 2, 380)


def e_periodico(fr, d, tl, dur):
    fr.alpha_composite(A["paris"])
    u = back(tl / 0.5)
    diario = Hm.periodico(["LA TORRE", "¡CUESTA", "UNA FORTUNA!"])
    pegar(fr, escalar(diario.rotate(-6 * (1 - min(1, tl / 0.5)), expand=True, resample=Image.BICUBIC), 0.95 * max(0.05, u)), W / 2, 720)
    pegar(fr, persona(**LUSTIG, brazo=(120, -120)), 870, 1240)


def e_idea(fr, d, tl, dur):
    fr.alpha_composite(A["paris"])
    pegar(fr, escalar(persona(**LUSTIG, brazo=(10, -150)), 1.4), W / 2, 1050)
    u = back(tl / 0.4)
    r = 120 * max(0.05, u)
    cx, cy = W / 2 + 40, 420
    for k in range(10):
        a = k * math.pi / 5 + tl
        d.line((cx + math.cos(a) * (r + 30), cy + math.sin(a) * (r + 30), cx + math.cos(a) * (r + 80), cy + math.sin(a) * (r + 80)), fill=(255, 230, 120), width=10)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 230, 120))
    d.rectangle((cx - r * 0.4, cy + r * 0.8, cx + r * 0.4, cy + r * 1.3), fill=(150, 150, 160))


def e_disfraz(fr, d, tl, dur):
    fr.alpha_composite(A["paris"])
    pegar(fr, persona(**LUSTIG, brazo=(10, -60)), 300, 1230)
    u = back(tl / 0.5)
    pegar(fr, escalar(documento(["MINISTERIO", "DE CORREOS", "Y TELÉGRAFOS"], "OFICIAL").rotate(5, expand=True, resample=Image.BICUBIC), 0.9 * max(0.05, u)), 720, 760)
    if tl > dur * 0.55:
        pegar(fr, escalar(sello("FALSO"), max(0.05, back((tl - dur * 0.55) / 0.3)) * 0.8), 720, 640)


def e_cartas(fr, d, tl, dur):
    fr.alpha_composite(A["hotel"])
    for k in range(6):
        u = ease((tl - k * 0.15) / 0.7)
        if u <= 0:
            continue
        x = W / 2 + (k - 2.5) * 150
        y = 1500 - 900 * u + 40 * math.sin(tl * 3 + k)
        sob = Image.new("RGBA", (130, 90), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sob)
        sd.rectangle((0, 0, 129, 89), fill=(250, 244, 230), outline=(170, 160, 140), width=4)
        sd.line((0, 0, 65, 50, 129, 0), fill=(170, 160, 140), width=4)
        sd.ellipse((54, 40, 76, 62), fill=(200, 40, 50))
        pegar(fr, sob.rotate(10 * math.sin(tl * 2 + k), expand=True), x, y)


def e_reunion(fr, d, tl, dur):
    fr.alpha_composite(A["hotel"])
    pegar(fr, escalar(persona(**LUSTIG, brazo=(10, -150)), 0.9), W / 2, 930)
    for i, x in enumerate((230, 420, 660, 850)):
        pegar(fr, escalar(persona(POISSON["ropa"] if i == 1 else (80 + 20 * i, 80, 90), pelo=(90 + 30 * i, 70, 50), brazo=(20, -20), mira=1 if x < W / 2 else -1), 0.75), x, 1060)
    d.rounded_rectangle((120, 1150, 960, 1290), radius=30, fill=(110, 70, 40))
    u = ease(tl / (dur * 0.7))
    t = escalar(A["torre_peq"], 0.6)
    t.putalpha(Image.eval(t.getchannel("A"), lambda a: int(a * (1 - u))))
    pegar(fr, t, W / 2, 420)
    if u > 0.3:
        for k in range(14):
            x = W / 2 - 180 + (k % 7) * 60; y = 560 - (k // 7) * 40
            d.polygon([(x, y), (x + 40, y - 10), (x + 50, y + 20), (x + 10, y + 26)], fill=(100, 92, 88))
        pegar(fr, texto_grande("¡CHATARRA!", (255, 214, 80), 120), W / 2, 260)


def e_secreto(fr, d, tl, dur):
    fr.alpha_composite(A["hotel"])
    pegar(fr, escalar(persona(**LUSTIG, brazo=(10, -155)), 1.5), W / 2, 1050)
    d.rounded_rectangle((W / 2 + 70, 600, W / 2 + 96, 700), radius=12, fill=C["piel"])
    pegar(fr, escalar(sello("SECRETO", (40, 40, 40)), max(0.05, back(tl / 0.4)) * 0.85), W / 2, 330)


def e_visita(fr, d, tl, dur):
    fr.alpha_composite(A["cielo"])
    pegar(fr, A["torre"], W / 2, 760)
    for i in range(4):
        x = 80 + i * 120 + 380 * ease(tl / (dur * 0.6))
        pegar(fr, escalar(persona(**(LUSTIG if i == 0 else dict(ropa=(70 + 25 * i, 80, 90))), pierna=andar(tl + i), brazo=(15, -15)), 0.7), x, 1330)
    if tl > dur * 0.6:
        u = back((tl - dur * 0.6) / 0.3)
        pegar(fr, escalar(A["pez"], max(0.05, u) * 0.9), W - 260, 560)
        pegar(fr, texto_grande("POISSON = PEZ", (255, 255, 255), 90), W - 300, 400)


def e_soborno(fr, d, tl, dur):
    fr.alpha_composite(A["hotel"])
    pegar(fr, persona(**LUSTIG, brazo=(10, -60), mira=1), 280, 1000)
    pegar(fr, persona(**POISSON, brazo=(60, -10), mira=-1), 800, 1000)
    d.rounded_rectangle((120, 1120, 960, 1260), radius=30, fill=(110, 70, 40))
    u = ease(tl / (dur * 0.6))
    pegar(fr, escalar(billetes(4), 0.6), 760 - 400 * u, 1120)
    pegar(fr, texto_grande("¿UN SOBORNO?", (255, 214, 80), 120), W / 2, 300)


def e_huye(fr, d, tl, dur):
    fr.alpha_composite(A["paris"])
    x = 200 + (W + 200) * ease(tl / dur)
    pegar(fr, persona(**LUSTIG, pierna=andar(tl, 11), brazo=(50 * andar(tl, 11), -60)), x, 1230)
    d.rounded_rectangle((x + 40, 1100, x + 190, 1200), radius=10, fill=(120, 80, 40))
    pegar(fr, texto_grande("A AUSTRIA", (255, 255, 255), 120), W / 2, 330)


def e_verguenza(fr, d, tl, dur):
    fr.alpha_composite(A["hotel"])
    p = escalar(persona(**POISSON, brazo=(165, 165)), 1.4)
    pegar(fr, p, W / 2, 1050)
    rojo = Image.new("RGBA", (60, 34), (0, 0, 0, 0))
    ImageDraw.Draw(rojo).ellipse((0, 0, 59, 33), fill=(240, 80, 80, 170))
    for dx in (-62, 62):
        pegar(fr, rojo, W / 2 + dx + 25, 862)
    pegar(fr, texto_grande("NO LO DENUNCIA", (255, 255, 255), 120), W / 2, 330)


def e_otravez(fr, d, tl, dur):
    fr.alpha_composite(A["cielo"])
    pegar(fr, A["torre"], W / 2, 760)
    pegar(fr, escalar(texto_grande("OTRA VEZ", (255, 214, 80), 200), max(0.05, back(tl / 0.4))), W / 2, 420)


def e_policia(fr, d, tl, dur):
    fr.alpha_composite(A["paris"])
    luz = int(tl * 6) % 2
    fr.alpha_composite(Image.new("RGBA", (W, H), (255, 40, 40, 60) if luz else (40, 80, 255, 60)))
    for i, x in enumerate((240, 840)):
        pegar(fr, persona("policia", sombrero="kepi", pierna=andar(tl + i), brazo=(40, -40), mira=1 if i == 0 else -1), x, 1230)
    pegar(fr, texto_grande("¡LA POLICÍA!", (255, 255, 255), 140), W / 2, 330)


def e_escapa(fr, d, tl, dur):
    fr.alpha_composite(A["paris"])
    d.rectangle((W - 260, 900, W - 40, 1300), fill=(90, 60, 40))
    x = 200 + (W - 360) * ease(tl / (dur * 0.7))
    pegar(fr, persona(**LUSTIG, pierna=andar(tl, 12), brazo=(60, -60)), x, 1230)
    if tl > dur * 0.7:
        d.rectangle((W - 240, 920, W - 60, 1300), fill=(60, 40, 30))
    pegar(fr, persona("policia", sombrero="kepi", pierna=andar(tl, 12), brazo=(40, -40)), x - 330, 1230)


def e_alcatraz(fr, d, tl, dur):
    fr.alpha_composite(A["paris_noche"])
    pegar(fr, escalar(persona(**LUSTIG, brazo=(20, -20)), 1.3), W / 2, 1000)
    for k in range(7):
        x = W / 2 - 330 + k * 110
        d.rectangle((x, 480 + (1 - ease(tl / 0.4)) * -700, x + 22, 1380), fill=(70, 70, 80))
    pegar(fr, texto_grande("ALCATRAZ", (255, 214, 80), 160), W / 2, 330)


def e_cta(fr, d, tl, dur):
    fr.alpha_composite(A["cielo"])
    pegar(fr, escalar(A["torre"], 0.7), 200, 900)
    u = back(tl / 0.5)
    pegar(fr, escalar(A["masc"], 0.6 * max(0.05, u)), W / 2 + 120, 900 - 20 * abs(math.sin(tl * 4)))
    pegar(fr, texto_grande("¿TÚ HABRÍAS PICADO?", (255, 90, 140), 110), W / 2, 330)


BEATS = [
    dict(f=e_vendida, say="En 1925, un hombre vendió la Torre Eiffel. Y no era suya.", sfx=("50%", "golpe")),
    dict(f=e_nombre, say="Se llamaba Victor Lustig, y era uno de los estafadores más hábiles de la historia."),
    dict(f=e_periodico, say="Un día leyó en el periódico que mantener la torre costaba una fortuna."),
    dict(f=e_idea, say="Y tuvo una idea genial… y totalmente ilegal.", sfx=(0.3, "logro")),
    dict(f=e_disfraz, say="Se hizo pasar por un alto cargo del Gobierno francés, con papeles oficiales falsos.", sfx=("55%", "golpe")),
    dict(f=e_cartas, say="Y citó a varios chatarreros de París en un hotel de lujo."),
    dict(f=e_reunion, say="Allí les contó un secreto: el Gobierno iba a vender la torre como chatarra."),
    dict(f=e_secreto, say="Y nadie podía saberlo, para no enfadar a los parisinos.", sfx=(0.2, "golpe")),
    dict(f=e_visita, say="Les llevó a ver la torre… y uno de ellos, André Poisson, picó."),
    dict(f=e_soborno, say="Lustig incluso le pidió un soborno. Y eso le convenció del todo: un funcionario corrupto parecía muy real."),
    dict(f=e_huye, say="Poisson pagó. Y Lustig se fue a Austria con el dinero."),
    dict(f=e_verguenza, say="Lo más increíble: a Poisson le dio tanta vergüenza que ni siquiera lo denunció."),
    dict(f=e_otravez, say="Así que, poco después, Lustig volvió a París… para intentarlo otra vez.", sfx=(0.2, "golpe")),
    dict(f=e_policia, say="Pero esta vez, uno de los chatarreros sospechó y avisó a la policía."),
    dict(f=e_escapa, say="Lustig escapó por los pelos."),
    dict(f=e_alcatraz, say="Años después lo detuvieron en Estados Unidos por falsificar billetes, y acabó en Alcatraz.", sfx=(0.35, "golpe")),
    dict(f=e_cta, say="¿Tú habrías picado? Sígueme para más historias reales que parecen inventadas."),
]

Hm.BEATS = BEATS
Hm.assets = assets_extra

if __name__ == "__main__":
    Hm.render()
