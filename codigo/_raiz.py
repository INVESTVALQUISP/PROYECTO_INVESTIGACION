"""Fija la carpeta del proyecto como directorio de trabajo.

Los scripts leen y escriben con rutas relativas (resultados/, figures/, salidas/, ...).
Importar este modulo primero permite ejecutarlos desde cualquier carpeta.
"""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
