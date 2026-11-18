# -*- coding: utf-8 -*-
"""Serie de 10 vídeos de curiosidades en tendencia. Uso: python serie_videos.py N  (N = 1..10)
Datos verificados en FUENTES_SERIE.md. Personajes e iconos originales (no se reproduce ninguna portada ni logo)."""
import math, sys
from PIL import Image, ImageDraw

import serie as S
from serie import (A, W, H, BL, AM, RO, VE, CI, RS, NA, CON, ease, back, texto_grande, pegar, escalar, icono, calendario,
                   E_icono, E_varios, E_texto, E_contador, E_barras, E_vs, E_persona, E_mapa, E_globo, E_final,
                   anim_pulso, anim_tachar, anim_varios, titulo, rayos, particulas, fondo, flota)
import historia as Hm

# ------------------------------------------------------------- mapas
S.mapa("ecl", -20, 55, 30, 800)
S.mapa("esp", -12, 6, 37.5, 760)
S.mapa("japon", 126, 146, 35, 800)
S.mapa("artico", -15, 55, 70, 820)
S.mapa("singapur", 96, 112, 2, 800)

CADIZ, MALAGA, CEUTA, LUXOR = (-6.29, 36.53), (-4.42, 36.72), (-5.32, 35.89), (32.64, 25.69)
FRANJA = [(-16, 37.3), (-10, 36.6), (-5.6, 36.0), (0, 35.3), (5, 34.8), (10, 33.8), (15, 32.0), (20, 30.0),
          (26, 27.6), (32.6, 25.7), (38, 23.3), (43, 19.0), (48, 13.5), (52, 9.0)]
HIROSHIMA, NAGASAKI, OKUNO = (132.46, 34.39), (129.87, 32.75), (132.99, 34.31)
LONGYEAR, OSLO = (15.63, 78.22), (10.75, 59.91)
SING = (103.82, 1.35)


# ------------------------------------------------------------- escenas especiales
def eclipse(fr, cx, cy, u, R=260, corona=True):
    """Sol tapado por la Luna: u=0 nada, u=1 total."""
    d = ImageDraw.Draw(fr)
    if u > 0.97 and corona:
        pegar(fr, corona_img(R), cx, cy)
    else:
        d.ellipse((cx - R - 30, cy - R - 30, cx + R + 30, cy + R + 30), fill=(255, 200, 80, 90))
        d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=AM, outline=NA, width=10)
    mx = cx + (1 - u) * 2.1 * R
    d.ellipse((mx - R, cy - R, mx + R, cy + R), fill=(20, 18, 30))


def corona_img(R):
    k = ("CORONA", R)
    if k not in A:
        from PIL import ImageFilter
        n = int(R * 2 + 520)
        im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        cd = ImageDraw.Draw(im)
        c = n / 2
        cd.ellipse((c - R - 40, c - R - 40, c + R + 40, c + R + 40), fill=(255, 255, 240, 255))
        for k2 in range(20):
            a = k2 * math.pi / 10 + 0.2 * (k2 % 3)
            L = R + 120 + 70 * (k2 % 4)
            cd.polygon([(c + math.cos(a - 0.08) * R, c + math.sin(a - 0.08) * R), (c + math.cos(a) * L, c + math.sin(a) * L),
                        (c + math.cos(a + 0.08) * R, c + math.sin(a + 0.08) * R)], fill=(255, 250, 220, 200))
        im = im.filter(ImageFilter.GaussianBlur(28))
        A[k] = im
    return A[k]


def s_eclipse(txt, u0=0.0, u1=1.0, fondo_="cielo"):
    def f(fr, d, tl, dur):
        u = u0 + (u1 - u0) * ease(tl / (dur * 0.8))
        base = fondo(fondo_).copy()
        if u > 0.5:   # oscurece el cielo
            osc = Image.new("RGBA", (W, H), (8, 8, 30, int(230 * min(1, (u - 0.5) / 0.47))))
            base.alpha_composite(osc)
        fr.alpha_composite(base)
        if u > 0.9:
            particulas(fr, tl, (255, 255, 230), 40, 9)
        eclipse(fr, W / 2, 800, u)
        titulo(fr, txt, tl, AM if u > 0.9 else BL)
    return f


def s_luxor(fr, d, tl, dur):
    fr.alpha_composite(fondo("noche"))
    eclipse(fr, W / 2, 560, 1.0, R=170)
    pegar(fr, escalar(icono("templo"), 1.2), W / 2, 1000)
    seg = min(383, int(383 * ease(tl / (dur * 0.7))))
    pegar(fr, texto_grande(f"{seg // 60}:{seg % 60:02d} MIN", AM, 150), W / 2, 1250 - 40)
    titulo(fr, "LUXOR, EGIPTO", tl, BL, 110, 300)


def s_estrella_pajaros(fr, d, tl, dur):
    fr.alpha_composite(fondo("noche"))
    eclipse(fr, W / 2, 620, 1.0, R=150)
    particulas(fr, tl, (255, 255, 230), 60, 2)
    pegar(fr, escalar(icono("termometro"), 0.6), 250, 1050 + flota(tl))
    pegar(fr, escalar(icono("estrella"), 0.45 * (1 + 0.1 * math.sin(tl * 6))), 820, 1050)
    titulo(fr, "DE DÍA… SE HACE DE NOCHE", tl, AM, 100)


def hongo_explota(t0=0.0, k=1.5, y=820):
    def f(fr, d, tl, dur):
        t = tl - t0
        if t < 0:
            return
        if t < 0.25:
            capa = Image.new("RGBA", (W, H), (255, 255, 240, int(255 * (1 - t / 0.25))))
            fr.alpha_composite(capa)
        u = ease(t / 0.9)
        pegar(fr, escalar(icono("hongo"), k * max(0.05, u)), W / 2, y + 200 * (1 - u))
    return f


def s_hongo(txt, sub=None):
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo("atardecer"))
        rayos(fr, tl, col=(255, 240, 200, 50))
        hongo_explota()(fr, d, tl, dur)
        titulo(fr, txt, tl, BL)
        if sub:
            titulo(fr, sub, tl, AM, 90, 1220, 0.5)
    return f


def s_permafrost(fr, d, tl, dur):
    fr.alpha_composite(fondo("nieve"))
    capas = [(1000, (240, 248, 255)), (1060, (170, 140, 110)), (1160, (150, 190, 230)), (1300, (120, 160, 210))]
    for i, (y, c) in enumerate(capas):
        d.rectangle((0, y, W, H), fill=c)
    for k in range(9):
        x = 60 + k * 120
        d.polygon([(x, 1200), (x + 30, 1260), (x - 30, 1260)], fill=(220, 240, 255))
    pegar(fr, escalar(icono("copo"), 0.5 * (1 + 0.05 * math.sin(tl * 3))), 800, 1240)
    pegar(fr, escalar(icono("tumba"), 0.9), 330, 880)
    pegar(fr, texto_grande("PERMAFROST", CI, 130), W / 2, 1180 + flota(tl, 2, 6))
    titulo(fr, "SUELO CONGELADO", tl, BL, 120)


PROF = [("SUPERFICIE", 0), ("1 KM", 1000), ("6 KM: FÓSILES", 6000), ("12,2 KM", 12262)]


def s_taladro(fr, d, tl, dur, hasta=12262, txt="12.262 METROS"):
    fr.alpha_composite(fondo("cielo"))
    top = 420
    cols = [(120, 90, 60), (150, 110, 70), (170, 120, 80), (140, 90, 70), (120, 70, 60), (200, 90, 50)]
    for i, c in enumerate(cols):
        d.rectangle((0, top + i * 150, W, top + (i + 1) * 150), fill=c)
    pegar(fr, escalar(icono("torre_perf"), 0.7), W / 2, top - 130)
    u = ease(tl / (dur * 0.8))
    prof = hasta * u
    yb = top + (1300 - top) * prof / 12262
    d.rectangle((W / 2 - 10, top, W / 2 + 10, yb), fill=(40, 40, 50))
    d.polygon([(W / 2 - 22, yb), (W / 2 + 22, yb), (W / 2, yb + 40)], fill=(200, 200, 210), outline=CON)
    pegar(fr, texto_grande(f"{int(prof):,} M".replace(",", "."), AM, 110), W / 2 + 260, min(1250, yb))
    titulo(fr, txt, tl, BL, 100, 330)


def s_espagueti(fr, d, tl, dur):
    fr.alpha_composite(fondo("espacio"))
    pegar(fr, escalar(icono("agujero"), 1.6), W / 2, 1150)
    u = ease(tl / (dur * 0.9))
    a = icono("astronauta")
    ws, hs = max(0.12, 0.9 - 0.75 * u), 0.9 + 2.2 * u
    im = a.resize((int(a.width * ws), int(a.height * hs)), Image.BICUBIC)
    pegar(fr, im, W / 2, 520 + 330 * u)
    titulo(fr, "ESPAGUETIZACIÓN", tl, NA, 120, 300)


def s_lento(fr, d, tl, dur):
    fr.alpha_composite(fondo("espacio"))
    pegar(fr, escalar(icono("agujero"), 1.4), W / 2, 1050)
    u = ease(tl / dur)
    a = icono("astronauta")
    im = escalar(a, 0.55 - 0.15 * u)
    rojo = Image.new("RGBA", im.size, (255, 40, 30, int(160 * u)))
    rojo.putalpha(Image.eval(im.getchannel("A"), lambda v: int(v * 0.6 * u)))
    im = im.copy(); im.alpha_composite(rojo)
    im.putalpha(Image.eval(im.getchannel("A"), lambda v: int(v * (1 - 0.7 * u))))
    pegar(fr, im, W / 2, 560 + 220 * (1 - (1 - u) ** 4))
    titulo(fr, "CADA VEZ MÁS LENTO", tl, BL, 110)


def s_puerta(fr, d, tl, dur, olvida=True):
    fr.alpha_composite(fondo("papel"))
    d.rectangle((0, 1180, W, H), fill=(170, 120, 80))
    pegar(fr, escalar(icono("puerta"), 1.6), W / 2, 880)
    u = min(1, tl / dur)
    x = 120 + (W - 240) * u
    p = Hm.persona((120, 80, 160), brazo=(30 * math.sin(tl * 7), -30 * math.sin(tl * 7)), pierna=math.sin(tl * 7))
    pegar(fr, escalar(p, 0.95), x, 960)
    # bocadillo con la idea que se borra al cruzar
    k = 1 if (x < W / 2 or not olvida) else max(0, 1 - (x - W / 2) / 120)
    if k > 0.02:
        d.ellipse((x - 150, 450, x + 150, 690), fill=(255, 255, 255, int(255 * k)), outline=CON + (int(255 * k),), width=6)
        pegar(fr, escalar(icono("bombilla"), 0.45 * k + 0.01), x, 570)
    elif olvida:
        pegar(fr, texto_grande("¿?", RO, 160), x, 560)
    titulo(fr, "LA PUERTA TIENE LA CULPA" if olvida else "VUELVE ATRÁS", tl, AM, 100, 300)


def s_capitulos(fr, d, tl, dur):
    fr.alpha_composite(fondo("morado"))
    for i in range(4):
        t0 = i * 0.45
        u = back((tl - t0) / 0.35)
        if u > 0:
            x = 190 + i * 235
            pegar(fr, escalar(icono("carpeta"), 0.55 * u), x, 800 + flota(tl + i, 3, 10))
            pegar(fr, texto_grande(f"CAP. {i + 1}", AM, 54), x, 960)
    titulo(fr, "TU VIDA EN CAPÍTULOS", tl, BL, 110)


def s_chicle_metro(fr, d, tl, dur):
    fr.alpha_composite(fondo("ciudad"))
    pegar(fr, escalar(icono("metro"), 1.6), W / 2, 820)
    for k, (x, y) in enumerate(((470, 780), (530, 860), (500, 940))):
        if tl > 0.3 + k * 0.25:
            d.ellipse((x - 28, y - 22, x + 28, y + 22), fill=RS, outline=CON, width=4)
    if tl > dur * 0.5 and int(tl * 4) % 2:
        pegar(fr, texto_grande("¡AVERÍA!", RO, 120), W / 2, 1220)
    titulo(fr, "PUERTAS BLOQUEADAS", tl, BL, 110)


def s_horas(fr, d, tl, dur):
    fr.alpha_composite(fondo("noche"))
    u = ease(tl / (dur * 0.7))
    h = int(264 * u)
    pegar(fr, escalar(icono("cansado"), 1.0 + 0.03 * math.sin(tl * 9)), W / 2, 680)
    pegar(fr, texto_grande(f"{h} HORAS", AM, 170), W / 2, 1000)
    pegar(fr, texto_grande(f"DÍA {min(11, h // 24 + 1) if h < 264 else 11}", BL, 90), W / 2, 1160)
    titulo(fr, "SIN DORMIR", tl, RO, 130)


def s_dias(dia, txt, ico, fondo_="noche"):
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo(fondo_))
        rayos(fr, tl)
        pegar(fr, escalar(calendario(str(dia), "DÍA"), 0.7 * max(0.05, back(tl / 0.35))), 260, 760 + flota(tl))
        pegar(fr, escalar(icono(ico), 0.9 * max(0.05, back((tl - 0.3) / 0.35))), 760, 780 + flota(tl + 1))
        titulo(fr, txt, tl, AM, 110)
    return f


# ------------------------------------------------------------- los 10 vídeos
V = {}

V[1] = dict(slug="19-portada-2027-mensajes-ocultos", gancho="LA PORTADA QUE «PREDICE» 2027", color=(240, 70, 80), giro=12,
            pron=[("The Economist", "Di Ikónomist"), ("Le Pen", "Le Pen"), ("Hollywood", "Jólibud")], beats=[
    dict(f=E_icono("rojo", "revista", "¿QUÉ PASARÁ EN 2027?", AM, 1.5), say="Esta portada dice lo que va a pasar en el mundo en 2027… y está llena de pistas escondidas."),
    dict(f=E_icono("papel", "revista", "CADA AÑO, UN ESPECIAL", RO, 1.3, rayos_=False), say="Cada año, la revista The Economist publica su número especial sobre el año que viene."),
    dict(f=E_icono("morado", "lupa", "VAMOS A DESCIFRARLA", AM, 1.4, gira=10), say="Y la gente se vuelve loca buscando mensajes ocultos en el dibujo. Vamos a descifrarlo.", sfx=("70%", "golpe")),
    dict(f=E_icono("rojo", "atril", "EL ÚLTIMO CAPÍTULO", BL, 1.4), say="En portada lo dice claro: el último capítulo de Trump… que no se irá en silencio."),
    dict(f=E_icono("lab", "cerebro", "INTELIGENCIA ARTIFICIAL", CI, 1.3, sub="ACELERACIÓN · RIESGO · RECHAZO"), say="En el centro, un cerebro hecho de circuitos: la inteligencia artificial. Aceleración, riesgos… y rechazo."),
    dict(f=E_vs("lab", "robot", "grafico", "ROBOTS", "¿BURBUJA?", "¿Y LA ECONOMÍA?", CI, RO), say="Al lado, un robot que corre, y un gráfico que se desploma. ¿Miedo a que estalle una burbuja?"),
    dict(f=E_icono("nieve", "kremlin", "RUSIA SIGUE AHÍ", RO, 1.4), say="Arriba a la derecha, el Kremlin y un jinete: Rusia sigue muy presente."),
    dict(f=E_varios("rojo", ["tanque", "petrolero", "fuego"], "DESPUÉS DE IRÁN", AM), say="Y abajo, tanques, explosiones y un petrolero encadenado: las réplicas de lo que pasó con Irán, en la región y en el mundo."),
    dict(f=E_varios("atardecer", ["termometro", "fuego", "molino"], "¿OTRA VEZ RÉCORD DE CALOR?", BL), say="Fuego, un termómetro y molinos de viento: avisan de que podría ser otra vez el año más caluroso jamás medido.", sfx=(0.3, "boom")),
    dict(f=E_icono("morado", "urna", "EL AUGE DEL POPULISMO", AM, 1.3), say="Hay una urna de votación: el auge del populismo. Y la pregunta que se hace la revista: ¿qué puede frenar a Le Pen en Francia?"),
    dict(f=E_icono("noche", "camara", "HARTOS DE SECUELAS", RS, 1.3), say="Y hasta Hollywood: una cámara de cine, porque el público está cansado de tantas secuelas y remakes."),
    dict(f=E_varios("espacio", ["cohete", "satelite"], "LA CARRERA ESPACIAL", CI, k=1.0), say="También hay cohetes, satélites y una bandera china: la carrera espacial ya no es solo cosa de Estados Unidos."),
    dict(f=E_texto("rojo", "PERO OJO", "NO ES UNA PROFECÍA"), say="Pero ojo: no es una profecía.", sfx=(0.1, "golpe")),
    dict(f=E_icono("morado", "bola", "SON SUS APUESTAS", AM, 1.3, extra=anim_tachar(0.8)), say="Son los temas que sus periodistas creen que van a marcar el año. Nada más… y nada menos."),
    dict(f=E_final("rojo", 1, "¿CUÁL SE CUMPLIRÁ?"), say="¿Cuál crees que se cumplirá? Te leo en comentarios. Y sígueme: esta es la parte uno de una serie de diez.", sfx=(0.3, "logro")),
])

V[2] = dict(slug="20-eclipse-del-siglo-2027", gancho="EL ECLIPSE DEL SIGLO", color=(255, 200, 60), giro=9,
            pron=[("Luxor", "Lúxor")], beats=[
    dict(f=s_eclipse("2 DE AGOSTO DE 2027", 0, 1), say="El 2 de agosto de 2027, el día se va a convertir en noche… en pleno verano.", sfx=("80%", "boom")),
    dict(f=s_eclipse("ECLIPSE TOTAL DE SOL", 1, 1, "noche"), say="Es un eclipse total de Sol, y ya lo llaman el eclipse del siglo."),
    dict(f=s_eclipse("LA LUNA TAPA EL SOL", 0, 1), say="La Luna se pondrá justo delante del Sol y lo tapará por completo."),
    dict(f=E_mapa("esp", [(*CADIZ, "CÁDIZ", RO), (*MALAGA, None, RO)], "SE VERÁ EN ESPAÑA", col=AM, banda=(FRANJA[:5], 170), extra=lambda fr, d, tl, dur: pegar(fr, texto_grande("MÁLAGA", BL, 58), *S.MAPAS["esp_obj"].xy(-4.0, 37.6)) if tl > 0.5 else None), say="Y en España se verá en el extremo sur: en zonas de Cádiz y de Málaga."),
    dict(f=E_mapa("ecl", [(*LUXOR, "LUXOR", AM)], "CRUZA ÁFRICA", col=BL, banda=(FRANJA, 46)), say="Luego cruzará el norte de África hasta llegar a Egipto."),
    dict(f=s_luxor, say="Y en Luxor, junto a los templos de los faraones, la noche durará más de seis minutos.", sfx=("60%", "golpe")),
    dict(f=s_estrella_pajaros, say="Durante esos minutos baja la temperatura, salen las estrellas y muchos animales se comportan como si fuera de noche."),
    dict(f=s_eclipse("LA CORONA", 1, 1, "noche"), say="Y alrededor del Sol aparece la corona: un halo blanco que normalmente es invisible."),
    dict(f=E_contador("cielo", 3, "ECLIPSES EN ESPAÑA", "¡EN MENOS DE 2 AÑOS!", AM, "sol"), say="Además, España vive una racha histórica: el de agosto de 2026, este de 2027, y uno anular en enero de 2028."),
    dict(f=E_texto("rojo", "PERO OJO", "PROTEGE TUS OJOS", RO, BL), say="Pero ojo: nunca lo mires sin gafas especiales de eclipse.", sfx=(0.1, "golpe")),
    dict(f=E_icono("cielo", "gafas", "SOLO GAFAS HOMOLOGADAS", BL, 1.5, extra=anim_pulso("prohibido", 820, 1150, 0.35, 0.6)), say="Ni con gafas de sol, ni a través del móvil o unos prismáticos: puede dañarte la vista para siempre."),
    dict(f=E_icono("noche", "sol", "APÚNTALO YA", AM, 1.2, extra=anim_pulso("gafas", 830, 1150, 0.4, 0.4)), say="Así que apúntatelo: 2 de agosto de 2027. Y prepara las gafas con tiempo."),
    dict(f=E_final("noche", 2, "GUÁRDALO"), say="Guárdalo para no olvidarlo y sígueme: esta es la parte dos de diez.", sfx=(0.3, "logro")),
])

V[3] = dict(slug="21-sobrevivio-a-dos-bombas-atomicas", gancho="SOBREVIVIÓ A DOS BOMBAS ATÓMICAS", color=(255, 150, 60), giro=8,
            pron=[("Tsutomu Yamaguchi", "Tsutómu Yamagúchi"), ("Yamaguchi", "Yamagúchi")], beats=[
    dict(f=s_hongo("2 BOMBAS EN 3 DÍAS", "Y SOBREVIVIÓ"), say="Este hombre sobrevivió a dos bombas atómicas… en solo tres días.", sfx=(0.2, "boom")),
    dict(f=E_persona("papel", "traje", "TSUTOMU YAMAGUCHI", ico="barco", sub="INGENIERO DE BARCOS"), say="Se llamaba Tsutomu Yamaguchi, y era ingeniero de barcos en Japón."),
    dict(f=E_mapa("japon", [(*HIROSHIMA, "HIROSHIMA", RO)], "VIAJE DE TRABAJO"), say="En el verano de 1945, su empresa lo mandó tres meses a la ciudad de Hiroshima."),
    dict(f=E_icono("cielo", calendario("6"), "ÚLTIMO DÍA ALLÍ", BL, 1.3), say="Era su último día allí. El 6 de agosto, por la mañana, iba de camino a la oficina…"),
    dict(f=s_hongo("A 3 KM DE ÉL"), say="Y la primera bomba atómica de la historia explotó a unos tres kilómetros de él.", sfx=(0.1, "boom")),
    dict(f=E_icono("papel", "cansado", "QUEMADO Y CASI SORDO", RO, 1.2), say="Sobrevivió, con quemaduras graves y los tímpanos rotos."),
    dict(f=E_mapa("japon", [(*HIROSHIMA, "HIROSHIMA", RO), (*NAGASAKI, "NAGASAKI", (60, 110, 230))], "VUELVE A CASA", ruta=[HIROSHIMA, (131.0, 33.9), NAGASAKI]), say="Al día siguiente cogió un tren de vuelta a su casa… en Nagasaki."),
    dict(f=E_icono("papel", calendario("9"), "VUELVE AL TRABAJO", BL, 1.3), say="El 9 de agosto, vendado, fue a trabajar y le contó a su jefe lo que había visto."),
    dict(f=E_texto("rojo", "Y ENTONCES…", "OTRO DESTELLO", AM, BL), say="Su jefe no le creía… y justo entonces, por la ventana, otro destello blanco.", sfx=("80%", "boom")),
    dict(f=s_hongo("LA SEGUNDA BOMBA", "OTRA VEZ A 3 KM"), say="La segunda bomba. Otra vez, a unos tres kilómetros."),
    dict(f=E_texto("atardecer", "Y OTRA VEZ…", "SOBREVIVIÓ", BL, VE), say="Y otra vez… sobrevivió.", sfx=(0.5, "golpe")),
    dict(f=E_icono("cielo", "prohibido", "NUNCA MÁS", RO, 1.1, extra=anim_pulso("hongo", W / 2, 820, 0.5, 0.0)), say="Años después, dedicó su vida a pedir que nunca más se usaran bombas atómicas."),
    dict(f=E_icono("papel", "diploma", "EL ÚNICO RECONOCIDO", AM, 1.3), say="En 2009, Japón le reconoció oficialmente como superviviente de las dos bombas. El único."),
    dict(f=E_contador("noche", 93, "AÑOS", "VIVIÓ HASTA LOS…", AM, "estrella"), say="Murió en 2010, con noventa y tres años."),
    dict(f=E_final("atardecer", 3, "¿LO SABÍAS?"), say="Increíble, ¿no? Sígueme, que esta es la parte tres de una serie de diez.", sfx=(0.3, "logro")),
])

V[4] = dict(slug="22-el-pueblo-donde-no-puedes-morir", gancho="EL PUEBLO DONDE NO PUEDES MORIR", color=(80, 200, 255), giro=8,
            pron=[("Longyearbyen", "Lóngyirbien"), ("Svalbard", "Esválbar")], beats=[
    dict(f=E_icono("nieve", "prohibido", "PROHIBIDO MORIR", RO, 1.3, extra=anim_pulso("tumba", W / 2, 820, 0.55, 0.0)), say="Existe un pueblo donde, en teoría, está prohibido morirse."),
    dict(f=E_mapa("artico", [(*LONGYEAR, "LONGYEARBYEN", AM)], "CERCA DEL POLO NORTE"), say="Se llama Longyearbyen, y está en Svalbard: unas islas de Noruega cerca del Polo Norte."),
    dict(f=E_vs("nieve", "oso", Hm.persona((200, 60, 60)), "OSOS", "PERSONAS", "¿QUIÉN GANA?", BL, AM), say="En el archipiélago viven unas tres mil personas… y unos tres mil osos polares."),
    dict(f=s_permafrost, say="El problema es el suelo: está congelado todo el año. Se llama permafrost."),
    dict(f=E_icono("nieve", "tumba", "NO SE DESCOMPONEN", RO, 1.3), say="Hace décadas descubrieron que los cuerpos del cementerio… no se descomponían.", sfx=("70%", "golpe")),
    dict(f=E_icono("lab", "virus", "GRIPE DE 1918", VE, 1.2, gira=8), say="Algunos habían muerto en la gripe de 1918, y los científicos encontraron restos del virus en ellos."),
    dict(f=E_icono("nieve", "tumba", "NO SE ENTIERRA A NADIE", BL, 1.2, extra=anim_tachar(0.6)), say="Así que, desde 1950, allí no se entierra a nadie."),
    dict(f=E_mapa("artico", [(*LONGYEAR, "SVALBARD", AM), (*OSLO, "CONTINENTE", BL)], "SI ENFERMAS, TE VAS", ruta=[LONGYEAR, (14, 70), OSLO], avion_=True), say="Si alguien se pone muy enfermo, lo llevan en avión al resto de Noruega."),
    dict(f=E_texto("nieve", "Y AL REVÉS…", "TAMPOCO PUEDES NACER", CI, RS), say="Y pasa lo mismo al revés: allí tampoco se puede nacer.", sfx=(0.3, "golpe")),
    dict(f=E_vs("cielo", "bebe", "avion", "BEBÉ", "AL CONTINENTE", "LAS EMBARAZADAS VIAJAN", CI, AM), say="Las embarazadas viajan al continente unas semanas antes de dar a luz."),
    dict(f=E_texto("morado", "PERO OJO", "NO HAY NINGUNA LEY", AM, BL), say="Pero ojo: no hay ninguna ley que lo prohíba. Simplemente, no se hace."),
    dict(f=E_vs("noche", "estrella", "sol", "MESES DE NOCHE", "SOL A MEDIANOCHE", "Y ADEMÁS…", CI, AM), say="Y además, allí en invierno no sale el sol durante meses… y en verano no se pone."),
    dict(f=E_final("nieve", 4, "¿VIVIRÍAS ALLÍ?"), say="¿Vivirías allí? Sígueme: esta es la parte cuatro de diez.", sfx=(0.3, "logro")),
])

V[5] = dict(slug="23-el-agujero-mas-profundo-del-mundo", gancho="EL AGUJERO MÁS PROFUNDO DEL MUNDO", color=(255, 120, 60), giro=11,
            pron=[("Kola", "Kóla")], beats=[
    dict(f=E_icono("cielo", "tapa", "EL AGUJERO MÁS PROFUNDO", AM, 1.6), say="Este es el agujero más profundo que ha hecho el ser humano… y está tapado con una tapa oxidada."),
    dict(f=E_globo(30.6, 69.4, "KOLA"), say="Es el pozo superprofundo de Kola, en el norte de Rusia."),
    dict(f=E_icono("nieve", "torre_perf", "EMPEZÓ EN 1970", BL, 1.5), say="La Unión Soviética empezó a perforarlo en 1970, en plena competición con Estados Unidos."),
    dict(f=E_icono("lab", "lupa", "¿QUÉ HAY AHÍ ABAJO?", CI, 1.3), say="Querían bajar lo más hondo posible en la corteza de la Tierra, para ver qué había."),
    dict(f=s_taladro, say="Y en 1989 llegaron a doce mil doscientos sesenta y dos metros.", sfx=("75%", "golpe")),
    dict(f=E_barras("cielo", [("EVEREST", 8849, (180, 180, 200)), ("FOSA DEL OCÉANO", 10994, (60, 120, 220)), ("KOLA", 12262, RO)], "MÁS HONDO QUE…", abajo=True), say="Más que la altura del Everest… y más que el punto más hondo del océano."),
    dict(f=E_contador("papel", 23, "CENTÍMETROS DE ANCHO", "Y ES ESTRECHÍSIMO", AM, "tapa"), say="Pero el agujero mide solo veintitrés centímetros de ancho."),
    dict(f=E_contador("rojo", 180, "GRADOS", "AHÍ ABAJO…", RO, "termometro", prefijo=""), say="Allí abajo encontraron algo inesperado: la roca estaba a ciento ochenta grados.", sfx=("60%", "boom")),
    dict(f=E_icono("rojo", "fuego", "LA ROCA SE ABLANDA", AM, 1.2), say="Con ese calor, la roca se comportaba casi como plástico, y no pudieron seguir bajando."),
    dict(f=E_icono("lab", "lupa", "FÓSILES A 6 KM", VE, 1.2), say="Y hasta encontraron fósiles microscópicos de plancton a más de seis kilómetros de profundidad."),
    dict(f=E_icono("papel", "tapa", "ABANDONADO EN 1992", BL, 1.5), say="En 1992 se paró el proyecto, y hoy solo queda esa tapa soldada."),
    dict(f=E_icono("morado", "altavoz", "¿GRITOS DEL INFIERNO?", RO, 1.3, extra=anim_tachar(1.0)), say="Pero ojo con el bulo de los gritos del infierno grabados ahí abajo: es falso.", sfx=("70%", "golpe")),
    dict(f=E_barras("cielo", [("KOLA", 12262, RO), ("CORTEZA AHÍ", 35000, (150, 110, 70))], "SOLO UN TERCIO", abajo=True), say="Y aun siendo el más profundo… solo atravesó un tercio de la corteza en ese punto."),
    dict(f=E_final("noche", 5, "¿TE ATREVERÍAS?"), say="¿Bajarías ahí? Sígueme: esta es la parte cinco de diez.", sfx=(0.3, "logro")),
])

V[6] = dict(slug="24-la-isla-de-los-conejos", gancho="LA ISLA DE LOS CONEJOS (Y SU SECRETO)", color=(255, 120, 170), giro=7,
            pron=[("Okunoshima", "Okunóshima")], beats=[
    dict(f=E_varios("verde", ["conejo", "conejo", "conejo"], "LA ISLA DE LOS CONEJOS", BL), say="Esta isla de Japón está llena de conejos… y esconde un secreto muy oscuro."),
    dict(f=E_mapa("japon", [(*OKUNO, "OKUNOSHIMA", AM)], "ESTÁ EN JAPÓN"), say="Se llama Okunoshima, y hoy cientos de conejos se acercan a los turistas para que les den de comer."),
    dict(f=E_icono("papel", "isla", "NO SALÍA EN LOS MAPAS", BL, 1.3, extra=anim_tachar(0.8)), say="Pero hace menos de cien años, esta isla ni siquiera aparecía en los mapas."),
    dict(f=E_icono("rojo", "fabrica", "GAS VENENOSO", VE, 1.4), say="Entre 1929 y 1945, el ejército japonés fabricó aquí, en secreto, gas venenoso.", sfx=("60%", "golpe")),
    dict(f=E_icono("papel", "lupa", "LA BORRARON DEL MAPA", RO, 1.2), say="La borraron de los mapas para que nadie supiera lo que pasaba allí."),
    dict(f=E_persona("lab", "bata", "MUCHOS ENFERMARON", ico="virus"), say="Muchos trabajadores no sabían bien con qué trabajaban… y muchos enfermaron."),
    dict(f=E_icono("cielo", "fabrica", "SE DESTRUYÓ TODO", BL, 1.2, extra=anim_tachar(0.5)), say="Al acabar la guerra, se destruyeron las armas y la fábrica se abandonó."),
    dict(f=E_texto("verde", "¿Y LOS CONEJOS?", "NADIE LO SABE SEGURO", RS, BL), say="¿Y los conejos? Nadie lo sabe seguro.", sfx=(0.2, "golpe")),
    dict(f=E_contador("verde", 8, "CONEJOS", "LA TEORÍA MÁS FAMOSA", AM, "conejo"), say="La teoría más famosa dice que en 1971 unos escolares soltaron ocho conejos… y se multiplicaron."),
    dict(f=E_vs("verde", "conejo", "prohibido", "CONEJOS: SÍ", "PERROS Y GATOS: NO", "SUS REGLAS", VE, RO), say="Hoy en la isla no se permiten ni perros ni gatos, y los conejos viven a sus anchas."),
    dict(f=E_icono("papel", "templo", "UN MUSEO PARA RECORDAR", AM, 1.2), say="Y allí mismo hay un museo del gas venenoso, para que no se olvide lo que pasó."),
    dict(f=E_varios("verde", ["conejo", "fabrica", "conejo"], "TERNURA E HISTORIA", BL), say="Así que, si vas, entre conejo y conejo… estás pisando un trozo de historia."),
    dict(f=E_final("verde", 6, "¿IRÍAS?"), say="¿Irías? Sígueme: esta es la parte seis de diez.", sfx=(0.3, "logro")),
])

V[7] = dict(slug="25-el-pais-donde-el-chicle-esta-prohibido", gancho="EL PAÍS DONDE EL CHICLE ESTÁ PROHIBIDO", color=(255, 90, 140), giro=7,
            pron=[], beats=[
    dict(f=E_icono("rojo", "chicle", "CHICLE PROHIBIDO", AM, 1.5, extra=anim_tachar(0.7)), say="En este país no puedes comprar chicle. Está prohibido desde 1992."),
    dict(f=E_mapa("singapur", [(*SING, "SINGAPUR", AM)], "UNA CIUDAD-PAÍS"), say="Es Singapur, una de las ciudades más limpias del mundo."),
    dict(f=E_varios("ciudad", ["chicle", "chicle", "chicle"], "CHICLES POR TODAS PARTES", RS), say="Todo empezó porque la gente pegaba chicles en todas partes: en ascensores, en buzones, en el suelo…"),
    dict(f=E_icono("ciudad", "metro", "Y LLEGÓ EL METRO", BL, 1.4), say="Pero lo peor llegó con el metro."),
    dict(f=s_chicle_metro, say="Algunos vándalos pegaban chicles en los sensores de las puertas… y los trenes se quedaban parados.", sfx=("50%", "golpe")),
    dict(f=E_icono("rojo", "prohibido", "VENDER E IMPORTAR: NO", BL, 1.2, extra=anim_pulso("chicle", W / 2, 820, 0.45, 0.0)), say="Así que en 1992 el gobierno prohibió vender e importar chicle."),
    dict(f=E_icono("papel", "multa", "MULTAS ALTAS", RO, 1.3, gira=6), say="Si intentas meterlo en el país en cantidad, te puede caer una buena multa."),
    dict(f=E_texto("morado", "PERO OJO", "MASTICARLO NO ES DELITO", AM, BL), say="Pero ojo: masticarlo no es ilegal.", sfx=(0.1, "golpe")),
    dict(f=E_icono("cielo", "farmacia", "LA EXCEPCIÓN", VE, 1.3), say="Y desde 2004 hay una excepción: el chicle medicinal, como el de nicotina, que se compra en la farmacia."),
    dict(f=E_varios("ciudad", ["multa", "metro", "multa"], "NORMAS MUY ESTRICTAS", AM), say="Singapur es famosa por sus normas estrictas: también hay multas por tirar basura… o por no tirar de la cadena en un baño público."),
    dict(f=E_vs("ciudad", "chicle", "estrella", "¿EXAGERADO?", "¿FUNCIONA?", "TÚ DECIDES", RO, VE), say="¿Exagerado… o funciona? Te leo en comentarios."),
    dict(f=E_final("rojo", 7, "SÍGUEME"), say="Y sígueme, que esta es la parte siete de diez.", sfx=(0.3, "logro")),
])

V[8] = dict(slug="26-11-dias-sin-dormir", gancho="11 DÍAS SIN DORMIR", color=(150, 120, 255), giro=9,
            pron=[("Randy Gardner", "Rándi Gárdner"), ("William Dement", "Uíliam Démen"), ("Stanford", "Éstanford"), ("Guinness", "Guínes")], beats=[
    dict(f=E_icono("noche", "cansado", "11 DÍAS SIN DORMIR", AM, 1.4, gira=6), say="Un chico de diecisiete años estuvo once días seguidos sin dormir. Y esto es lo que le pasó."),
    dict(f=E_persona("ciudad", (60, 120, 200), "RANDY GARDNER", ico="trofeo", sub="17 AÑOS · 1963"), say="Se llamaba Randy Gardner, y lo hizo a finales de 1963, para una feria de ciencias del instituto, en San Diego."),
    dict(f=E_varios("noche", [Hm.persona((200, 80, 80)), "cansado", Hm.persona((80, 160, 90))], "SUS AMIGOS LO VIGILABAN", BL, k=0.7), say="Sus amigos se turnaban para mantenerlo despierto."),
    dict(f=s_dias(2, "NO ENFOCA LA VISTA", "lupa"), say="Al segundo día ya le costaba enfocar la vista."),
    dict(f=s_dias(4, "EMPIEZA A VER COSAS", "estrella", "morado"), say="Hacia el cuarto día empezó a imaginar cosas: llegó a creer que era un famoso jugador de fútbol americano.", sfx=("60%", "golpe")),
    dict(f=E_icono("morado", "carpeta", "SE LE OLVIDA TODO", RO, 1.2, extra=anim_tachar(0.8)), say="Se le olvidaba lo que estaba diciendo a mitad de frase."),
    dict(f=E_persona("lab", "bata", "UN CIENTÍFICO DEL SUEÑO", ico="cerebro", sub="UNIVERSIDAD DE STANFORD"), say="Un científico del sueño de la Universidad de Stanford, William Dement, se unió para vigilarlo."),
    dict(f=s_horas, say="Al final aguantó doscientas sesenta y cuatro horas: once días y unos minutos.", sfx=("72%", "golpe")),
    dict(f=E_icono("noche", "cama", "DURMIÓ 14 HORAS", CI, 1.5), say="Y después durmió unas catorce horas seguidas."),
    dict(f=E_texto("noche", "PERO OJO", "LO PAGÓ CON LOS AÑOS", AM, RO), say="Pero ojo: años después contó que sufrió insomnio durante mucho tiempo.", sfx=(0.1, "golpe")),
    dict(f=E_icono("papel", "trofeo", "RÉCORD QUE YA NO EXISTE", BL, 1.3, extra=anim_tachar(0.8)), say="Hoy, el libro Guinness ya no acepta este tipo de récords: es demasiado peligroso."),
    dict(f=E_icono("morado", "cerebro", "DORMIR LIMPIA TU CEREBRO", CI, 1.2), say="Porque dormir no es perder el tiempo: es cuando tu cerebro se limpia y guarda tus recuerdos."),
    dict(f=E_final("noche", 8, "A DORMIR…"), say="Así que vete a dormir… pero antes, sígueme. Esta es la parte ocho de diez.", sfx=(0.3, "logro")),
])

V[9] = dict(slug="27-que-pasa-si-caes-en-un-agujero-negro", gancho="¿Y SI CAES EN UN AGUJERO NEGRO?", color=(255, 160, 60), giro=5,
            pron=[], beats=[
    dict(f=E_icono("espacio", "agujero", "¿Y SI CAES DENTRO?", AM, 1.8, rayos_=False, gira=4), say="¿Qué te pasaría si cayeras en un agujero negro? Spoiler: nada bueno."),
    dict(f=E_icono("espacio", "agujero", "NI LA LUZ ESCAPA", BL, 1.6, rayos_=False, extra=anim_pulso("estrella", 820, 500, 0.25, 0.5)), say="Un agujero negro es un lugar donde la gravedad es tan fuerte que ni siquiera la luz puede escapar."),
    dict(f=E_icono("espacio", "astronauta", "CAES DE PIES", CI, 1.3, rayos_=False, gira=25), say="Imagina que caes con los pies por delante."),
    dict(f=E_vs("espacio", "astronauta", "agujero", "CABEZA", "PIES", "TIRA MÁS DE TUS PIES", BL, NA), say="La gravedad tira mucho más fuerte de tus pies que de tu cabeza…"),
    dict(f=s_espagueti, say="Y te estira como un espagueti. Los científicos lo llaman, de verdad, espaguetización.", sfx=("55%", "golpe")),
    dict(f=E_texto("espacio", "PERO OJO", "SI ES GIGANTE…", AM, CI), say="Pero ojo: si el agujero negro es gigante, podrías cruzar el borde sin notar nada.", sfx=(0.1, "golpe")),
    dict(f=E_icono("espacio", "agujero", "HORIZONTE DE SUCESOS", NA, 1.6, rayos_=False, sub="NO HAY VUELTA ATRÁS", sub_col=RO), say="Ese borde se llama horizonte de sucesos. A partir de ahí, no hay vuelta atrás."),
    dict(f=E_icono("espacio", "lupa", "DESDE FUERA…", BL, 1.2, rayos_=False), say="Y lo más raro: alguien que te mirara desde fuera nunca te vería entrar."),
    dict(f=s_lento, say="Te vería ir cada vez más lento… y volverte rojo, hasta desaparecer."),
    dict(f=E_icono("espacio", "reloj", "EL TIEMPO VA MÁS LENTO", AM, 1.4, rayos_=False, gira=15), say="Porque cerca de un agujero negro, el tiempo pasa más despacio."),
    dict(f=E_contador("espacio", 4, "MILLONES DE SOLES", "EN NUESTRA GALAXIA", AM, "agujero"), say="En el centro de nuestra galaxia hay uno con la masa de unos cuatro millones de soles."),
    dict(f=E_contador("espacio", 26000, "AÑOS LUZ", "TRANQUI: ESTÁ LEJOS", VE, "estrella"), say="Tranquilo: está a unos veintiséis mil años luz de aquí."),
    dict(f=E_final("espacio", 9, "SÍGUEME"), say="¿Te lanzarías? Sígueme: esta es la parte nueve de diez.", sfx=(0.3, "logro")),
])

V[10] = dict(slug="28-por-que-olvidas-al-cruzar-una-puerta", gancho="POR QUÉ OLVIDAS AL CRUZAR UNA PUERTA", color=(90, 230, 120), giro=9,
             pron=[("Radvansky", "Radvánski")], beats=[
    dict(f=lambda fr, d, tl, dur: s_puerta(fr, d, tl, dur), say="¿Te ha pasado entrar en una habitación… y no acordarte de a qué ibas?"),
    dict(f=E_texto("papel", "NO ES TU MEMORIA", "ES LA PUERTA", BL, RO), say="No es que estés perdiendo la memoria. La culpa es… de la puerta.", sfx=("70%", "golpe")),
    dict(f=E_persona("lab", "bata", "EL EFECTO PUERTA", ico="puerta", sub="GABRIEL RADVANSKY"), say="Se llama el efecto puerta, y lo estudió el psicólogo Gabriel Radvansky, en Estados Unidos."),
    dict(f=E_varios("papel", ["carpeta", "puerta", "carpeta"], "EL EXPERIMENTO", AM), say="En sus experimentos, la gente cogía objetos y los llevaba de una habitación a otra."),
    dict(f=E_vs("papel", "puerta", "estrella", "CON PUERTA", "SIN PUERTA", "¿CUÁNDO OLVIDAS MÁS?", RO, VE), say="Y al cruzar una puerta, olvidaban más que si recorrían la misma distancia sin salir de la habitación."),
    dict(f=E_icono("morado", "robot", "¡HASTA EN UN VIDEOJUEGO!", CI, 1.2), say="Pasaba incluso en un videojuego, con puertas virtuales."),
    dict(f=s_capitulos, say="La explicación: tu cerebro guarda la vida en capítulos, como una serie."),
    dict(f=E_icono("morado", "carpeta", "CAPÍTULO CERRADO", AM, 1.3, extra=anim_pulso("puerta", 820, 1050, 0.4, 0.4)), say="Y una puerta es como el final de un capítulo: tu cerebro archiva lo anterior y abre uno nuevo."),
    dict(f=E_icono("papel", "bombilla", "LA IDEA SE QUEDA ATRÁS", BL, 1.2, extra=anim_tachar(0.9)), say="Por eso lo que pensabas se queda… en la otra habitación."),
    dict(f=E_texto("verde", "EL TRUCO", "VUELVE ATRÁS", AM, BL), say="El truco: vuelve a la habitación donde estabas.", sfx=(0.2, "golpe")),
    dict(f=lambda fr, d, tl, dur: s_puerta(fr, d, tl, dur, olvida=False), say="Muchas veces, al volver, te acuerdas al instante."),
    dict(f=E_icono("verde", "altavoz", "O DILO EN VOZ ALTA", BL, 1.2), say="O repítelo en voz alta mientras caminas."),
    dict(f=E_final("verde", 10, "SÍGUEME"), say="Y el último truco: sígueme. Esta era la parte diez de diez… y vienen más.", sfx=(0.3, "logro")),
])


if __name__ == "__main__":
    n = int(sys.argv[1])
    v = V[n]
    S.lanzar(v["slug"], v["gancho"], v["color"], v["giro"], v["beats"], v["pron"])
