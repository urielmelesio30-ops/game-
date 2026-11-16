# -*- coding: utf-8 -*-
"""Foto de perfil en pixel art (1080x1080; lienzo 108x108 escalado x10).

Mascota original: una tele retro sonriente rodeada de iconos de temas variados.
Todo lo importante cabe en el círculo que recorta TikTok/Instagram."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from render import P, col, dither_vertical

N = 108
SALIDA = os.path.join(os.path.dirname(__file__), "..", "perfil")

ICONOS = {
    "mando": ["..######..", ".#......#.", "#.#....#.#", "###.##.###", "#.#....#.#", ".#..##..#.", "..##..##.."],
    "nota": ["...###", "...#.#", "...#.#", "...#..", ".###..", "####..", ".##..."],
    "estrella": ["...#...", "...#...", "#######", ".#####.", "..###..", ".##.##.", "##...##"],
    "corazon": [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."],
    "bombilla": [".###.", "#####", "#####", ".###.", "..#..", ".###.", ".###."],
}


def icono(nombre, color, x, y, d):
    for j, fila in enumerate(ICONOS[nombre]):
        for i, ch in enumerate(fila):
            if ch == "#":
                d.point((x + i, y + j), fill=col(color))


def contorno(img, color=(12, 8, 22)):
    """Contorno de 1 px alrededor de lo dibujado en una capa RGBA."""
    a = np.array(img)[:, :, 3] > 0
    borde = np.zeros_like(a)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        borde |= np.roll(np.roll(a, dx, 1), dy, 0)
    borde &= ~a
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    arr = np.array(out)
    arr[borde] = color + (255,)
    out = Image.fromarray(arr)
    out.alpha_composite(img)
    return out


def perfil(cielo, cuerpo, pantalla, cara, nombre):
    fondo = Image.fromarray(dither_vertical(N, N, cielo)).convert("RGBA")
    d = ImageDraw.Draw(fondo)
    rng = np.random.default_rng(3)
    for _ in range(26):
        x, y = rng.integers(4, N - 4, 2)
        d.point((int(x), int(y)), fill=col("crema"))
    # suelo/sombra
    d.ellipse((30, 86, 78, 94), fill=col("negro") + (255,))

    capa = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    c = ImageDraw.Draw(capa)
    # antenas
    c.line([(46, 30), (40, 18)], fill=col("gris"), width=2)
    c.line([(62, 30), (69, 17)], fill=col("gris"), width=2)
    c.rectangle((38, 15, 41, 18), fill=col("amarillo"))
    c.rectangle((68, 14, 71, 17), fill=col("rosa"))
    # patitas
    c.rectangle((40, 78, 44, 88), fill=col(cuerpo[1]))
    c.rectangle((64, 78, 68, 88), fill=col(cuerpo[1]))
    # cuerpo de la tele
    c.rounded_rectangle((24, 30, 84, 80), radius=7, fill=col(cuerpo[0]))
    c.rectangle((26, 74, 82, 79), fill=col(cuerpo[1]))       # sombra inferior
    c.line([(29, 33), (78, 33)], fill=col("crema"))          # brillo
    # pantalla
    c.rounded_rectangle((30, 37, 70, 71), radius=4, fill=col("negro"))
    c.rounded_rectangle((31, 38, 69, 70), radius=4, fill=col(pantalla))
    osc = tuple(max(0, v - 18) for v in col(pantalla))
    for y in range(40, 70, 3):                                # líneas de barrido
        c.line([(33, y), (67, y)], fill=osc)
    # cara grande y gruesa para que se lea en pequeño: ojos ^ ^, sonrisa y mejillas
    for ox in (36, 54):
        ojo = [(0, 4), (1, 3), (2, 2), (3, 1), (4, 1), (5, 1), (6, 2), (7, 3), (8, 4)]
        for dx, dy in ojo:
            c.rectangle((ox + dx, 44 + dy, ox + dx, 45 + dy), fill=col(cara))
    sonrisa = [(0, 0), (1, 1), (2, 2), (3, 2), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3), (9, 3), (10, 3), (11, 2), (12, 2), (13, 1), (14, 0)]
    for dx, dy in sonrisa:
        c.rectangle((43 + dx, 56 + dy, 43 + dx, 57 + dy), fill=col(cara))
    c.rectangle((47, 60, 53, 62), fill=col("rosa"))           # lengua
    c.rectangle((33, 54, 37, 56), fill=col("rosa"))
    c.rectangle((63, 54, 67, 56), fill=col("rosa"))
    # mandos laterales de la tele
    c.ellipse((73, 40, 79, 46), fill=col("amarillo"))
    c.ellipse((73, 50, 79, 56), fill=col("cian"))
    for y in (61, 64, 67):
        c.line([(73, y), (79, y)], fill=col(cuerpo[1]))
    capa = contorno(capa)
    fondo.alpha_composite(capa)

    # iconos alrededor (dentro del círculo)
    capa2 = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    c2 = ImageDraw.Draw(capa2)
    icono("mando", "cian", 12, 38, c2)
    icono("nota", "amarillo", 88, 34, c2)
    icono("estrella", "amarillo", 16, 64, c2)
    icono("corazon", "rosa", 86, 62, c2)
    icono("bombilla", "crema", 52, 6, c2)
    fondo.alpha_composite(contorno(capa2))

    os.makedirs(SALIDA, exist_ok=True)
    out = fondo.convert("RGB").resize((1080, 1080), Image.NEAREST)
    ruta = os.path.join(SALIDA, f"perfil_{nombre}.png")
    out.save(ruta, optimize=True)
    return ruta


if __name__ == "__main__":
    print(perfil(["noche", "morado", "magenta", "coral", "naranja"], ("crema", "coral"), "azul", "cian", "atardecer"))
    print(perfil(["negro", "marino", "azul", "uva", "magenta"], ("rosa", "magenta"), "marino", "amarillo", "noche"))
    print(perfil(["morado", "uva", "rosa", "coral", "amarillo"], ("cian", "azul"), "negro", "verde", "neon"))
