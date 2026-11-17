"""Tratamento da logo. Uso: logo.py recortar|vetorizar|cores|extras
Resultado: vtracer REPROVADO (cores lavadas, texto deformado). Usado Real-ESRGAN anime 4x + recorte por cor (comando ampliar).
"""
import sys
from pathlib import Path
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = Path.home() / "Estudos/Captura de tela de 2026-11-17 17-07-57.png"
OUT = RAIZ / "tools/out"
SEM_FUNDO = OUT / "logo_sem_fundo.png"


def recortar(origem=ORIGEM, e=1):
    # rembg (isnet) deixou prancha/folhas semitransparentes e apagou o pirulito rosa;
    # o fundo é só rosa pastel em 2 tons, então remoção por cor ligada às bordas é exata.
    import numpy as np
    from scipy import ndimage
    a = np.array(Image.open(origem).convert("RGB")).astype(int)[4*e:-4*e, 4*e:-4*e]  # borda escura da captura
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    escuro = a.sum(-1) < 200
    escuro[60*e:] = False  # só o canto preto da captura, topo
    escuro[:, 80*e:] = False
    fundo = ((r > 232) & (g > 140) & (g < 205) & (b > 200) & (b - g > 25) & (b - g < 80)) | escuro
    # bolsões presos (entre palitos) também são fundo; o rosa da logo é saturado e não entra na faixa
    rot, n = ndimage.label(fundo)
    tam = ndimage.sum(fundo, rot, range(1, n + 1))
    fundo = np.isin(rot, 1 + np.flatnonzero(tam > 150*e*e))
    fundo = ndimage.binary_opening(fundo, iterations=e)  # tira pontinhos soltos
    # halo: pixel a ≤2px do fundo e com cor ainda próxima do rosa pastel vira fundo
    rosa = np.array([253, 172, 226])
    perto = ndimage.binary_dilation(fundo, iterations=2*e) & ~fundo
    fundo |= perto & (np.abs(a - rosa).sum(-1) < 110)
    # alpha suave: distância até o fundo, 2px de transição contra serrilhado
    dist = ndimage.distance_transform_edt(~fundo)
    alpha = np.clip((dist - 0.5) / (2*e), 0, 1) * 255
    rgba = np.dstack([a, alpha]).astype("uint8")
    out = Image.fromarray(rgba, "RGBA")
    out = out.crop(out.getbbox())
    OUT.mkdir(parents=True, exist_ok=True)
    out.save(SEM_FUNDO)
    print("salvo", SEM_FUNDO, out.size)


def vetorizar():
    import vtracer
    vtracer.convert_image_to_svg_py(
        str(SEM_FUNDO), str(OUT / "logo.svg"),
        colormode="color", filter_speckle=4, color_precision=6, mode="spline",
    )
    print("salvo", OUT / "logo.svg", (OUT / "logo.svg").stat().st_size // 1024, "KB")


def ampliar():
    """Real-ESRGAN 4x (modelo anime: bom para ilustração chapada) + recorte por cor."""
    import subprocess
    up = OUT / "up4.png"
    subprocess.run([str(RAIZ / "tools/bin/esrgan/realesrgan-ncnn-vulkan"), "-i", str(ORIGEM),
                    "-o", str(up), "-n", "realesrgan-x4plus-anime", "-s", "4"], check=True)
    recortar(up, e=4)
    logo = Image.open(SEM_FUNDO)
    (RAIZ / "assets").mkdir(exist_ok=True)
    for w, nome in [(1600, "logo.webp"), (800, "logo-800.webp"), (800, "logo.png")]:
        img = logo.resize((w, round(logo.height * w / logo.width)), Image.LANCZOS)
        img.save(RAIZ / "assets" / nome, quality=85, method=6) if nome.endswith("webp") else img.save(RAIZ / "assets" / nome, optimize=True)
    print("assets/logo.webp e logo.png", img.size)


def cores():
    import numpy as np
    a = np.array(Image.open(SEM_FUNDO).convert("RGBA"))
    px = a[a[..., 3] == 255][:, :3]
    q = Image.fromarray(px[None]).quantize(10)
    pal = q.getpalette()[:30]
    cont = sorted(q.getcolors(), reverse=True)
    for n, i in cont:
        print("#%02x%02x%02x" % tuple(pal[i * 3:i * 3 + 3]), n)


def raios(w, h, c1=(253, 177, 229), c2=(255, 196, 236), n=24):
    from PIL import ImageDraw
    import math
    img = Image.new("RGB", (w, h), c1)
    d = ImageDraw.Draw(img)
    cx, cy, R = w / 2, h / 2, max(w, h)
    for k in range(0, n, 2):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                   (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=c2)
    return img


def extras():
    logo = Image.open(SEM_FUNDO)
    # favicon: pirulito rosa da direita (região em coordenadas relativas da logo)
    w, h = logo.size
    from PIL import ImageDraw
    cx, cy, r = int(w * .636), int(h * .18), int(w * .121)  # pirulito rosa (medido no recorte 4x)
    fav = logo.crop((cx - r, cy - r, cx + r, cy + r))
    m = Image.new("L", fav.size, 0)  # máscara circular corta a lasca do pirulito azul
    ImageDraw.Draw(m).ellipse((0, 0, fav.width - 1, fav.height - 1), fill=255)
    fav.putalpha(Image.composite(fav.getchannel("A"), m, m))
    fav.thumbnail((64, 64), Image.LANCZOS)
    quad = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    quad.alpha_composite(fav, ((64 - fav.width) // 2, (64 - fav.height) // 2))
    quad.save(RAIZ / "assets/favicon.png")
    og = raios(1200, 630).convert("RGBA")
    l = logo.copy()
    l.thumbnail((1150, int(630 * .96)), Image.LANCZOS)
    og.alpha_composite(l, ((1200 - l.width) // 2, (630 - l.height) // 2))
    og.convert("RGB").save(RAIZ / "og.png", optimize=True)
    print("favicon", quad.size, "og", og.size, (RAIZ / "og.png").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    {"recortar": recortar, "vetorizar": vetorizar, "ampliar": ampliar,
     "cores": cores, "extras": extras}[sys.argv[1]]()
