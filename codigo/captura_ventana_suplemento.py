"""
captura_ventana_suplemento.py
================================================================================
Capturas de la ventana del simulador interactivo para el material suplementario (articulo/suplemento.tex).
Abre la ventana real (simulador_gui.py), avanza con el boton «Paso» hasta t = 118 s con los valores por
defecto (720/2160 veh/h, semilla 1, 3600 s), el mismo instante de gen_fig_suplemento_simulador.py, y guarda:

  articulo/figures/fig_sup_ventana_flco.png    la ventana completa con FLC-O, con sus apartados rotulados (a) a (i)
  articulo/figures/fig_sup_ventana_pappis.png  la ventana completa con Pappis y Mamdani (1977), rotulada (a) a (i)
  articulo/figures/fig_sup_pestana_1.png       pestaña «1 · Escenario»
  articulo/figures/fig_sup_pestana_2.png       pestaña «2 · Controlador» con FLC-O (controles de 1977 apagados)
  articulo/figures/fig_sup_pestana_2p.png      pestaña «2 · Controlador» con Pappis y Mamdani (controles encendidos)
  articulo/figures/fig_sup_pestana_3.png       pestaña «3 · Vista didáctica»
  articulo/figures/fig_sup_botones.png         columna de botones (Iniciar, Pausa, Paso, Reiniciar, autos a mano, guardar)
  articulo/figures/fig_sup_editor_reglas.png   ventana «Encender / apagar reglas» (solo con el controlador de 1977)

Necesita una pantalla (en Linux sin escritorio: xvfb-run -s "-screen 0 1680x1000x24" python codigo/captura_ventana_suplemento.py).
En Windows basta con ejecutarlo: la ventana se abre, se captura sola y se cierra.
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageGrab

import simulador_gui as g

OUT = "articulo/figures"
T_STOP = 118          # instante mostrado; el primer «Paso» simula t = 0, asi que hacen falta T_STOP + 1 pasos
ROJO = (197, 48, 48)
ABAJO = {"b", "f", "h"}   # apartados cuya letra va en la esquina inferior derecha


def grab(widget):
    """Captura la region de pantalla de un widget (o de la ventana) y la devuelve como imagen."""
    widget.update()
    x, y = widget.winfo_rootx(), widget.winfo_rooty()
    w, h = widget.winfo_width(), widget.winfo_height()
    kw = {"xdisplay": os.environ["DISPLAY"]} if sys.platform.startswith("linux") else {}
    return ImageGrab.grab(bbox=(x, y, x + w, y + h), **kw)


def caja(root, widget):
    """Rectangulo (x0, y0, x1, y1) de un widget en pixeles de la captura de la ventana."""
    x0 = widget.winfo_rootx() - root.winfo_rootx()
    y0 = widget.winfo_rooty() - root.winfo_rooty()
    return (x0, y0, x0 + widget.winfo_width(), y0 + widget.winfo_height())


def caja_eje(root, app, *axes):
    """Rectangulo de uno o varios ejes de matplotlib dentro del lienzo de la ventana."""
    cw = app.canvas.get_tk_widget()
    cx, cy = cw.winfo_rootx() - root.winfo_rootx(), cw.winfo_rooty() - root.winfo_rooty()
    H = app.fig.bbox.height
    rend = app.fig.canvas.get_renderer()
    bbs = [a.get_tightbbox(rend) for a in axes]
    x0, x1 = min(b.x0 for b in bbs), max(b.x1 for b in bbs)
    y0, y1 = min(b.y0 for b in bbs), max(b.y1 for b in bbs)
    return (cx + x0 - 3, cy + H - y1 - 3, cx + x1 + 3, cy + H - y0 + 3)


def fuente(tam):
    for nombre in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(nombre, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def rotular(img, cajas, path):
    """Dibuja cada apartado con un recuadro rojo punteado y su letra, y guarda la imagen (al doble de tamaño)."""
    img = img.convert("RGB").resize((img.width * 2, img.height * 2), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    f = fuente(26)
    for letra, (x0, y0, x1, y1) in cajas:
        x0, y0, x1, y1 = [2 * v for v in (x0, y0, x1, y1)]
        x0, y0 = max(x0, 2), max(y0, 2)
        x1, y1 = min(x1, img.width - 3), min(y1, img.height - 3)
        for k in range(0, int(x1 - x0), 16):          # borde punteado
            d.line([(x0 + k, y0), (min(x0 + k + 9, x1), y0)], fill=ROJO, width=3)
            d.line([(x0 + k, y1), (min(x0 + k + 9, x1), y1)], fill=ROJO, width=3)
        for k in range(0, int(y1 - y0), 16):
            d.line([(x0, y0 + k), (x0, min(y0 + k + 9, y1))], fill=ROJO, width=3)
            d.line([(x1, y0 + k), (x1, min(y0 + k + 9, y1))], fill=ROJO, width=3)
        txt = f"({letra})"
        tw, th = d.textbbox((0, 0), txt, font=f)[2:]
        bx1 = x1 - 4
        by0 = y1 - th - 12 if letra in ABAJO else y0 + 4        # la letra va donde no tapa texto del apartado
        d.rounded_rectangle([bx1 - tw - 12, by0, bx1, by0 + th + 8], radius=6, fill=ROJO)
        d.text((bx1 - tw - 6, by0 + 2), txt, fill="white", font=f)
    img.save(path)
    print("guardado", path, img.size)


def apartados(root, app, nb, side_btns):
    """Los nueve apartados de la ventana: (a) pestañas, (b) calle, (c)-(e) columna del controlador, (f) traza,
    (g) botones, (h) explicacion, (i) registro."""
    v = app.view
    return [("a", caja(root, nb)),
            ("b", caja_eje(root, app, v.ax)),
            ("c", caja_eje(root, app, v.ax_rules, *getattr(v, "_fl_insets", []))),
            ("d", caja_eje(root, app, v.ax_grade)),
            ("e", caja_eje(root, app, v.ax_fire)),
            ("f", caja_eje(root, app, v.axq)),
            ("g", side_btns),
            ("h", caja(root, app.explain)),
            ("i", caja(root, app.log.master))]


def avanzar(app, root, n):
    app.reset()
    for _ in range(n):
        app.step1()
    root.update()


def hook(app, root):
    nb = [w for w in root.winfo_children() if w.winfo_class() == "TNotebook"][0]

    def botones():
        x0, y0, x1, _ = caja(root, app.b_start.master)
        y1 = caja(root, app.explain)[1] - 26          # hasta antes del titulo de la explicacion
        return (x0, y0, x1, y1)

    # ---------------- FLC-O ----------------
    avanzar(app, root, T_STOP + 1)
    print("FLC-O:", app.status.cget("text"))
    nb.select(0)
    root.update()
    rotular(grab(root), apartados(root, app, nb, botones()), f"{OUT}/fig_sup_ventana_flco.png")
    for i, nombre in ((0, "fig_sup_pestana_1"), (1, "fig_sup_pestana_2"), (2, "fig_sup_pestana_3")):
        nb.select(i)
        root.update()
        grab(nb).save(f"{OUT}/{nombre}.png")
        print("guardado", nombre)
    nb.select(0)
    x0, y0, x1, y1 = botones()
    img = grab(root).crop((x0, y0, x1, y1))
    img.resize((img.width * 2, img.height * 2), Image.LANCZOS).save(f"{OUT}/fig_sup_botones.png")
    print("guardado fig_sup_botones")

    # ---------------- Pappis y Mamdani (1977) ----------------
    app.v_ctrl.set(g.NOMBRES["pappis"])
    app._set_ctrl_ui()
    avanzar(app, root, T_STOP + 1)
    print("Pappis:", app.status.cget("text"))
    nb.select(0)
    root.update()
    rotular(grab(root), apartados(root, app, nb, botones()), f"{OUT}/fig_sup_ventana_pappis.png")
    nb.select(1)
    root.update()
    grab(nb).save(f"{OUT}/fig_sup_pestana_2p.png")
    print("guardado fig_sup_pestana_2p")
    antes = set(root.winfo_children())
    app.open_rules_editor()
    root.update()
    win = [w for w in root.winfo_children() if w not in antes][0]
    win.geometry("+30+30")
    win.lift()
    root.update()
    grab(win).save(f"{OUT}/fig_sup_editor_reglas.png")
    print("guardado fig_sup_editor_reglas")
    win.destroy()
    root.destroy()


if __name__ == "__main__":
    g.run_gui(test_hook=hook, controlador="flco")
