# -*- coding: utf-8 -*-
"""Portadas en pixel art, 1080x1920 (lienzo 360x640 escalado x3).

El texto va en la franja central: la cuadrícula del perfil de TikTok recorta
la portada a 3:4, así que lo de arriba y abajo del todo no se ve ahí.
"""
import os
from PIL import Image
import render as R
from guiones import VIDEOS


def portada(v, idx):
    tema = R.TEMAS[v["tema"]]
    fondo = R.Fondo(v["fondo"], v["tema"], idx)
    img = fondo.frame(1.0, R.MG).convert("RGBA")
    img.alpha_composite(Image.new("RGBA", img.size, R.col("negro") + (90,)))
    l1, l2, chapa = v["miniatura"]
    y = 186
    for txt, color in ((l1, "blanco"), (l2, tema["a"])):
        for tam in (32, 24, 16):
            f = R.fuente("pixel", tam)
            if R.ancho_txt(txt, f) <= R.ANCHO + 20:
                break
        im = R.txt_img(txt, f, color, "negro" if color != "blanco" else tema["a"])
        img.alpha_composite(im, ((R.BW - im.width) // 2, y))
        y += im.height + 8
    f = R.fuente("pixel", 16)
    t = R.txt_img(chapa, f, "negro", None)
    c = R.caja(t.width + 20, t.height + 14, borde="negro", relleno="amarillo")
    c.alpha_composite(t, (10, 7))
    img.alpha_composite(c, ((R.BW - c.width) // 2, y + 10))
    logo = R.logo_img(tema)
    img.alpha_composite(logo, ((R.BW - logo.width) // 2, 150))
    out = os.path.join(R.SALIDA, v["slug"], "portada.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.convert("RGB").resize((1080, 1920), Image.NEAREST).save(out, optimize=True)
    return out


if __name__ == "__main__":
    for i, v in enumerate(VIDEOS):
        print(portada(v, i))
