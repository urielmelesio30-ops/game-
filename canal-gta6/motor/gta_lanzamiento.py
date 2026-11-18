# -*- coding: utf-8 -*-
"""Vídeos cortos (30-45 s) para la semana de lanzamiento de GTA 6, en versión sobria:
gancho visible desde el primer fotograma, sin pegatinas ni destellos, rayos suaves, y portada para la cuadrícula.
Uso: python gta_lanzamiento.py N [--muestra] (N = 1..6)   ·   python gta_lanzamiento.py portadas

Datos (verificados):
- GTA V: 17 sep 2013; 800 M$ el primer día y 1.000 M$ en 3 días (récord Guinness de producto de entretenimiento);
  más de 200 M de copias, el segundo juego más vendido de la historia tras Minecraft; estaba previsto para primavera
  de 2013 y se retrasó a septiembre. Salió en tres generaciones de consolas. GTA Online, actualizado desde 2013.
  Entre medias, Rockstar lanzó Red Dead Redemption 2 (2018).
- GTA VI: tráiler 1 (5 dic 2023, adelantado por una filtración): unos 90 M de visitas en YouTube en 24 h, récord para
  un vídeo no musical; fecha inicial 2025, retrasado al 26 may 2026 y luego al 19 nov 2026 para pulirlo.
  Tráiler 2 (may 2025): 475 M de visualizaciones en 24 h sumando plataformas, según Rockstar. Sale en PS5 y Xbox Series.
- Filtración (sep 2022): ver gta_filtracion.py."""
import math, os, sys
from PIL import Image, ImageDraw

import serie as S
import historia as Hm
import anime as AN
import gta_filtracion as GF   # registra sus iconos (hotel, tele, stick, móvil, trailer, dinero…)
from serie import (A, W, H, BL, AM, RO, VE, CI, RS, NA, CON, OK, ease, back, texto_grande, pegar, escalar, icono, calendario,
                   E_icono, E_varios, E_texto, E_contador, E_vs, E_final, anim_pulso, titulo, fondo, flota)

S.FONDOS["vice"] = AN.fondo_atardecer
ROSA_GTA = (255, 90, 200)

# ------------------------------------------------------------- versión sobria del montaje
_rayos_orig = S.rayos
S.rayos = lambda fr, tl, cx=W / 2, cy=800, col=(255, 255, 255, 40), n=14: _rayos_orig(fr, tl * 0.4, cx, cy, (255, 255, 255, 16), 10)
S.particulas = lambda *a, **k: None
Hm.CICLO_PEGATINAS = [None]
Hm.GIRO = None
_conf = Hm.confeti
Hm.confeti = lambda fr, t, n=70, semilla=3: _conf(fr, t, min(n, 16), semilla)


def adornos_sobrio(fr, tg, total, kb, tl, beat):
    d = ImageDraw.Draw(fr)
    marco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(marco).rounded_rectangle((10, 10, W - 11, H - 11), radius=40, outline=Hm.COLOR_MARCO + (200,), width=10)
    fr.alpha_composite(marco)
    d.rounded_rectangle((30, 30, W - 30, 44), radius=7, fill=(0, 0, 0, 140))
    d.rounded_rectangle((30, 30, 30 + (W - 60) * min(1, tg / total), 44), radius=7, fill=Hm.COLOR_MARCO)
    pegar(fr, Hm.ADORNOS["gancho"], W / 2, 120)
    pegar(fr, Hm.ADORNOS["mascota"], 110, 1360 - abs(math.sin(tg * 6)) * 14)


Hm.adornos = adornos_sobrio


def ya(f, adelanto=0.7):
    """La escena arranca ya montada (para el primer fotograma: el gancho se ve desde el segundo 0)."""
    return lambda fr, d, tl, dur: f(fr, d, tl + adelanto, dur + adelanto)


# ------------------------------------------------------------- iconos nuevos
def ic_mando(d, S_, s):
    d.rounded_rectangle(S_(30, 130, 370, 300), radius=80 * s, fill=(40, 40, 56), outline=CON, width=OK * s)
    d.rectangle(S_(95, 185, 115, 245), fill=BL); d.rectangle(S_(75, 205, 135, 225), fill=BL)
    for x, y, c in ((285, 180, VE), (315, 210, RO), (255, 210, CI), (285, 240, AM)):
        d.ellipse(S_(x - 14, y - 14, x + 14, y + 14), fill=c)
    d.ellipse(S_(150, 240, 190, 280), fill=(90, 90, 110)); d.ellipse(S_(210, 240, 250, 280), fill=(90, 90, 110))


def ic_copias(d, S_, s):
    for k in range(3):
        o = k * 30
        d.rounded_rectangle(S_(60 + o, 40 + o, 280 + o, 330 + o), radius=16 * s, fill=(30, 30, 40), outline=CON, width=OK * s)
        d.rectangle(S_(80 + o, 70 + o, 260 + o, 260 + o), fill=ROSA_GTA if k == 2 else (170, 80, 255))
    d.text((140 * s, 160 * s), "V", font=S.anton(110 * s), fill=BL)


def ic_cohete_gta(d, S_, s):
    S.ICONOS["cohete"](d, S_, s)


for _n, _f in (("mando", ic_mando), ("copias", ic_copias)):
    S.ICONOS[_n] = _f


def e_esperas(fr, d, tl, dur):
    """2013 → 2026 con la edad que sube."""
    fr.alpha_composite(fondo("vice"))
    u = ease(tl / (dur * 0.7))
    anio = 2013 + int(13 * u)
    edad = 10 + int(13 * u)
    pegar(fr, texto_grande(str(anio), AM, 230), W / 2, 660)
    pegar(fr, texto_grande(f"TENÍAS 10 → TIENES {edad}", BL, 84), W / 2, 900)
    titulo(fr, "GTA 5 SALIÓ EN 2013", tl + 0.7, BL, 110, 330)


def e_retrasos(fr, d, tl, dur, paso):
    fr.alpha_composite(fondo("morado"))
    fechas = [("'25", "AÑO 2025"), ("26", "MAYO 2026"), ("19", "NOV 2026")]
    for i, (n, sub) in enumerate(fechas[:paso + 1]):
        x = 200 + i * 340
        cal = escalar(calendario(n, sub.split()[0] if i else "PLAN"), 0.62)
        pegar(fr, cal, x, 760)
        if i < paso:
            d.line((x - 120, 640, x + 120, 880), fill=RO, width=22); d.line((x + 120, 640, x - 120, 880), fill=RO, width=22)
        pegar(fr, texto_grande(sub, BL, 52), x, 960)
    titulo(fr, ["LA FECHA INICIAL", "PRIMER RETRASO", "SEGUNDO RETRASO"][paso], tl, [BL, AM, RO][paso], 110, 330)


def retraso(paso):
    return lambda fr, d, tl, dur: e_retrasos(fr, d, tl, dur, paso)


def e_hoy(fr, d, tl, dur):
    fr.alpha_composite(fondo("vice"))
    AN.lineas_foco(fr, tl, (255, 255, 255), cy=780, alfa=60, n=40)
    pegar(fr, texto_grande("HOY", AM, 260), W / 2, 640)
    pegar(fr, texto_grande("SALE GTA 6", BL, 170), W / 2, 880)
    pegar(fr, texto_grande("19 DE NOVIEMBRE", ROSA_GTA, 90), W / 2, 1100)


def final(pregunta):
    return E_final("vice", 0, pregunta)


# ------------------------------------------------------------- los 6 vídeos
V = {}

V[1] = dict(slug="31-gta6-lo-filtro-desde-un-hotel", gancho="LO FILTRÓ DESDE UN HOTEL",
            portada=("LO FILTRÓ", "DESDE UN HOTEL", "hotel"), beats=[
    dict(f=ya(E_icono("vice", "hotel", "FILTRÓ GTA 6 CON 17 AÑOS", AM, 1.3, extra=anim_pulso("stick", 830, 1120, 0.55, 0.0))),
         say="Este chico de diecisiete años filtró GTA 6… desde la habitación de un hotel."),
    dict(f=GF.e_noventa, say="En 2022 publicó noventa vídeos del juego sin terminar: la mayor filtración de la historia."),
    dict(f=E_icono("noche", "hotel", "SIN ORDENADOR NI INTERNET", BL, 1.2, extra=anim_pulso("prohibido", 820, 1130, 0.35, 0.4)),
         say="Y estaba en libertad bajo fianza, sin ordenador y sin internet."),
    dict(f=GF.e_como, say="¿Cómo lo hizo? Con la tele del hotel, un móvil… y un Fire Stick de Amazon.", sfx=("78%", "golpe")),
    dict(f=E_contador("vice", 5, "MILLONES DE DÓLARES", "LO QUE COSTÓ A ROCKSTAR", VE, "dinero"), say="A Rockstar le costó unos cinco millones de dólares."),
    dict(f=E_icono("noche", "hospital", "INTERNADO SIN FECHA DE SALIDA", RO, 1.3), say="¿Y él? Lo internaron en un hospital de seguridad, sin fecha de salida.", sfx=(0.4, "boom")),
    dict(f=final("¿LO SABÍAS?"), say="¿Lo sabías? Contesta sí o no en comentarios, y sígueme para más de GTA 6.", sfx=(0.3, "logro")),
])

V[2] = dict(slug="32-gta6-los-records-que-tiene-que-romper", gancho="LOS RÉCORDS QUE GTA 6 TIENE QUE ROMPER",
            portada=("1.000 MILLONES", "EN 3 DÍAS", "dinero"), beats=[
    dict(f=ya(E_contador("vice", 1000, "MILLONES DE DÓLARES EN 3 DÍAS", "EL RÉCORD DE GTA 5", AM, "dinero")),
         say="GTA 5 ganó mil millones de dólares en solo tres días. Y GTA 6 tiene que superarlo."),
    dict(f=E_contador("morado", 800, "MILLONES EL PRIMER DÍA", "SOLO EN 24 HORAS", VE, "dinero"), say="Solo el primer día, GTA 5 hizo ochocientos millones de dólares."),
    dict(f=E_icono("vice", "trofeo", "MÁS RÁPIDO QUE CUALQUIER PELÍCULA", AM, 1.3), say="Fue lo que más rápido llegó a mil millones en todo el entretenimiento: más que cualquier película.", sfx=(0.5, "golpe")),
    dict(f=E_contador("morado", 200, "MILLONES DE COPIAS", "Y HA VENDIDO MÁS DE…", RS, "copias"), say="Y ha vendido más de doscientos millones de copias."),
    dict(f=E_vs("vice", "copias", "trofeo", "GTA 5: Nº 2", "MINECRAFT: Nº 1", "LOS MÁS VENDIDOS", RS, AM), say="Es el segundo juego más vendido de la historia. Solo le gana Minecraft."),
    dict(f=E_icono("vice", "cohete", "¿LO SUPERARÁ GTA 6?", BL, 1.2), say="Por eso muchos analistas creen que GTA 6 puede romperlo todo desde el primer día."),
    dict(f=final("¿LO SUPERARÁ?"), say="¿Crees que lo superará? Comenta sí o no, y sígueme para más de GTA 6.", sfx=(0.3, "logro")),
])

V[3] = dict(slug="33-gta6-13-anios-esperando", gancho="13 AÑOS ESPERANDO GTA 6",
            portada=("13 AÑOS", "ESPERANDO", "mando"), beats=[
    dict(f=ya(e_esperas, 0.0), say="GTA 5 salió en 2013. Si entonces tenías diez años… ahora tienes veintitrés."),
    dict(f=E_icono("morado", "mando", "PS3 Y XBOX 360", BL, 1.4), say="En 2013 todavía jugábamos en la PlayStation 3 y la Xbox 360."),
    dict(f=E_contador("vice", 3, "GENERACIONES DE CONSOLAS", "GTA 5 SALIÓ EN…", AM, "tele"), say="GTA 5 llegó a salir en tres generaciones de consolas distintas.", sfx=("60%", "golpe")),
    dict(f=E_icono("atardecer", "trofeo", "ENTRE MEDIAS: RED DEAD 2", NA, 1.2), say="Entre medias, Rockstar solo sacó otro gran juego nuevo: Red Dead Redemption 2, en 2018."),
    dict(f=E_icono("vice", "movil", "GTA ONLINE: +10 AÑOS", CI, 1.2), say="Y GTA Online siguió recibiendo actualizaciones durante más de diez años."),
    dict(f=E_texto("vice", "LA ESPERA MÁS LARGA", "DE TODA LA SAGA", AM, BL), say="Es la espera más larga de toda la historia de GTA."),
    dict(f=final("¿CUÁNTOS AÑOS TENÍAS?"), say="¿Cuántos años tenías cuando salió GTA 5? Dímelo en comentarios.", sfx=(0.3, "logro")),
])

V[4] = dict(slug="34-gta6-por-que-se-retraso-2-veces", gancho="GTA 6 SE RETRASÓ 2 VECES",
            portada=("SE RETRASÓ", "2 VECES", "reloj"), beats=[
    dict(f=ya(E_texto("rojo", "SE RETRASÓ", "DOS VECES", AM, BL)), say="GTA 6 se retrasó dos veces. Y no, no fue por pereza."),
    dict(f=retraso(0), say="Rockstar lo presentó en diciembre de 2023, con una fecha: 2025."),
    dict(f=retraso(1), say="Luego lo retrasó al 26 de mayo de 2026.", sfx=(0.3, "golpe")),
    dict(f=retraso(2), say="Y después, otra vez: al 19 de noviembre de 2026.", sfx=(0.3, "golpe")),
    dict(f=E_icono("vice", "lupa", "PARA PULIRLO", BL, 1.3), say="Su explicación: necesitaban más tiempo para pulirlo con la calidad que se espera de ellos."),
    dict(f=E_icono("morado", "trofeo", "CON GTA 5 PASÓ IGUAL", AM, 1.2), say="Con GTA 5 pasó lo mismo: se retrasó varios meses… y acabó batiendo récords."),
    dict(f=final("¿VALIÓ LA PENA?"), say="¿Valió la pena esperar? Te leo en comentarios.", sfx=(0.3, "logro")),
])

V[5] = dict(slug="35-gta6-el-trailer-que-rompio-youtube", gancho="EL TRÁILER QUE ROMPIÓ YOUTUBE",
            portada=("90 MILLONES", "EN 1 DÍA", "trailer"), beats=[
    dict(f=ya(E_contador("vice", 90, "MILLONES DE VISITAS EN 1 DÍA", "UN TRÁILER DE GTA 6", AM, "trailer")),
         say="Un tráiler de GTA 6 tuvo noventa millones de visitas en un solo día."),
    dict(f=E_icono("morado", "trofeo", "RÉCORD DE YOUTUBE", AM, 1.3), say="Fue en diciembre de 2023, y batió el récord de YouTube para un vídeo que no era de música.", sfx=(0.6, "golpe")),
    dict(f=E_icono("noche", "alarma", "SE FILTRÓ ANTES", RO, 1.2), say="Y Rockstar tuvo que estrenarlo antes de tiempo, porque se había filtrado."),
    dict(f=E_contador("vice", 475, "MILLONES EN 24 HORAS", "EL SEGUNDO TRÁILER", RS, "trailer"), say="El segundo tráiler fue aún más lejos: cuatrocientos setenta y cinco millones de visualizaciones en veinticuatro horas, sumando todas las plataformas.", sfx=("70%", "boom")),
    dict(f=E_texto("vice", "EL MAYOR ESTRENO", "DE UN VÍDEO EN 24 H", AM, BL), say="Según Rockstar, el mayor estreno de un vídeo en veinticuatro horas de la historia."),
    dict(f=final("¿LO VISTE EL DÍA 1?"), say="¿Viste el tráiler el primer día? Comenta, y sígueme para más de GTA 6.", sfx=(0.3, "logro")),
])

V[6] = dict(slug="36-hoy-sale-gta6", gancho="HOY SALE GTA 6",
            portada=("HOY SALE", "GTA 6", "mando"), beats=[
    dict(f=e_hoy, say="Hoy, 19 de noviembre, por fin sale GTA 6.", sfx=(0.1, "boom")),
    dict(f=E_contador("morado", 13, "AÑOS DESPUÉS DE GTA 5", "LA ESPERA TERMINA", AM, "mando"), say="Trece años después de GTA 5."),
    dict(f=E_varios("vice", ["reloj", "codigo", "trailer"], "2 RETRASOS · 90 VÍDEOS · RÉCORDS", BL, k=0.7),
         say="Dos retrasos, noventa vídeos filtrados, y tráileres que rompieron récords."),
    dict(f=E_vs("vice", "mando", "mando", "PLAYSTATION 5", "XBOX SERIES", "¿DÓNDE SALE?", CI, VE), say="Sale en PlayStation 5 y en Xbox Series."),
    dict(f=E_texto("vice", "BIENVENIDO", "DE VUELTA A VICE CITY", RS, AM), say="Bienvenido de vuelta a Vice City."),
    dict(f=final("¿PLAY O XBOX?"), say="¿PlayStation o Xbox? Comenta dónde lo vas a jugar, y sígueme.", sfx=(0.3, "logro")),
])


# ------------------------------------------------------------- portadas (título dentro de la zona 3:4 de la cuadrícula)
def portada(n):
    v = V[n]
    l1, l2, ico = v["portada"]
    fr = fondo("vice").copy()
    S.rayos(fr, 0.3, cy=980)
    pegar(fr, escalar(icono(ico), 1.05), W / 2, 1170)
    pegar(fr, texto_grande(l1, BL, 190), W / 2, 560)
    pegar(fr, texto_grande(l2, AM, 150), W / 2, 760)
    pegar(fr, texto_grande("GTA 6", ROSA_GTA, 80), W / 2, 380)
    marco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(marco).rounded_rectangle((10, 10, W - 11, H - 11), radius=40, outline=ROSA_GTA + (220,), width=12)
    fr.alpha_composite(marco)
    arr = Hm.pixelar(__import__("numpy").asarray(fr.convert("RGB")))
    im = arr.convert("RGB").resize((W, H), Image.NEAREST)
    out = os.path.join(Hm.PL.SALIDA, v["slug"])
    os.makedirs(out, exist_ok=True)
    im.save(os.path.join(out, "portada.png"))
    return os.path.join(out, "portada.png")


if __name__ == "__main__":
    if sys.argv[1] == "portadas":
        Hm.preparar_adornos()
        for n in V:
            print(portada(n))
    else:
        n = int(sys.argv[1])
        v = V[n]
        S.lanzar(v["slug"], v["gancho"], ROSA_GTA, None, v["beats"], [("Fire Stick", "Fáier Estik"), ("YouTube", "Yutub"), ("Minecraft", "Máinkraft"), ("Red Dead Redemption 2", "Red Ded Redémpshon dos"), ("Xbox", "Ekisbox")])
