# utils/visualizer.py
from kivy.graphics import Color, Line
from kivy.uix.widget import Widget
import numpy as np


class VisualizerCanvas(Widget):
    """
    Widget dédié à la visualisation.
    - `update_waveform(samples)` reçoit un tableau numpy normalisé [-1, 1].
    - Le spectre (FFT) est calculé à la volée et dessiné sous la forme d’une
      courbe.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.samples = np.zeros(1024)   # tampon circulaire initial

    def update_waveform(self, samples: np.ndarray):
        """Met à jour le tampon et redessine."""
        # On garde seulement les 1024 derniers échantillons
        self.samples = samples[-1024:]

        self.canvas.clear()
        with self.canvas:
            # Fond semi‑transparent
            Color(0.12, 0.12, 0.15, 0.6)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=0)

            # Dessin de l'onde (blanc)
            Color(0.8, 0.9, 1, 1)
            pts = []
            w, h = self.width, self.height
            for i, val in enumerate(self.samples):
                x = self.x