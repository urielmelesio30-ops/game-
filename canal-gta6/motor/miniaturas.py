# -*- coding: utf-8 -*-
"""Portadas verticales 1080x1920 para TikTok.

El texto va en la franja central: la cuadrícula del perfil de TikTok recorta
la portada a 3:4, así que lo de arriba y abajo del todo no se ve ahí.
"""
import os
from PIL import Image, ImageDraw, ImageFilter
import render as R
from guiones import VIDEOS, CANAL

PW, PH = 1080, 1920


def portada(v, idx):
    tema = v["tema"]
    T = R.TEMAS[tema]
    s_prev = R.S
    marco = R.bucle_fondo(v["fondo"], tema, idx, n=1)[0]
    bg = Image.fromarray(marco).crop((R.MARGEN, 0, R.MARGEN + R.W, R.H)).resize((PW, PH), Image.LANCZOS)
    img = bg.convert("RGBA")
    img.alpha_composite(Image.new("RGBA", (PW, PH), (6, 3, 16, 120)))
    R.S = 1.0
    l1, l2, chapa = v["miniatura"]
    y = 560
    for txt, col in ((l1, R.BLANCO), (l2, T["a"])):
        tam = 190
        f = R.fuente("display", tam)
        while R.medir(txt, f)[0] > PW - 120:
            tam -= 6; f = R.fuente("display", tam)
        sp, pad = R.sprite_texto(txt, f, col, brillo=T["a"] if col == R.BLANCO else None, borde=5)
        img.alpha_composite(sp, ((PW - sp.width) // 2, y - pad))
        y += sp.height - 2 * pad + 24
    f = R.fuente("display", 120)
    w, h, l, t = R.medir(chapa, f)
    ch = Image.new("RGBA", (w + 80, h + 60), (0, 0, 0, 0))
    dc = ImageDraw.Draw(ch)
    dc.rounded_rectangle((0, 0, ch.width - 1, ch.height - 1), radius=22, fill=(255, 216, 50, 255), outline=(0, 0, 0, 255), width=7)
    dc.text((40 - l, 30 - t), chapa, font=f, fill=R.TINTA + (255,))
    ch = ch.rotate(-5, expand=True, resample=Image.BICUBIC)
    sombra = Image.new("RGBA", ch.size, (0, 0, 0, 0))
    sombra.putalpha(ch.getchannel("A").point(lambda a: int(a * 0.6)))
    sombra = sombra.filter(ImageFilter.GaussianBlur(12))
    x = (PW - ch.width) // 2
    img.alpha_composite(sombra, (x + 12, y + 40))
    img.alpha_composite(ch, (x, y + 28))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((PW // 2 - 130, 400, PW // 2 + 130, 476), radius=16, fill=(10, 8, 24, 230), outline=T["a"], width=4)
    d.text((PW // 2, 438), CANAL, font=R.fuente("display", 46), fill=R.BLANCO, anchor="mm")
    R.S = s_prev
    out = os.path.join(R.SALIDA, v["slug"], "portada.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.convert("RGB").save(out, optimize=True)
    return out


if __name__ == "__main__":
    for i, v in enumerate(VIDEOS):
        print(portada(v, i))
