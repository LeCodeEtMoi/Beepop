# player_core.py
import random
from pathlib import Path
from typing import List, Optional

from kivy.core.audio import SoundLoader
from kivy.properties import NumericProperty, BooleanProperty, StringProperty


class Player:
    """
    Gestionnaire audio indépendant du KV.
    -------------------------------------------------
    Attributs publics (exposés à l’App) :
        - playlist          : List[Path]   (liste ordonnée des pistes)
        - index             : int          (piste courante)
        - repeat_mode       : str          ('none', 'single', 'all')
        - shuffle           : bool
        - volume            : float (0‑1)
        - muted             : bool
        - duration          : float (seconds, 0 si inconnu)
        - position          : float (seconds)
    -------------------------------------------------
    Méthodes principales :
        load_folder(folder_path)
        play(), pause(), stop()
        next(), previous()
        set_repeat(mode), toggle_shuffle()
        set_volume(v), toggle_mute()
        seek(seconds)
        update_position()   # à appeler régulièrement (Clock.schedule_interval)
    """

    # ---------- propriétés observables ----------
    volume = NumericProperty(1.0)          # 0‑1
    muted = BooleanProperty(False)
    repeat_mode = StringProperty('none')   # none | single | all
    shuffle = BooleanProperty(False)

    def __init__(self):
        self._sound = None
        self.playlist: List[Path] = []
        self.index: int = -1                # -1 = aucune piste sélectionnée
        self.duration: float = 0.0
        self.position: float = 0.0

    # ------------------------------------------------------------------ #
    #   Gestion du catalogue
    # ------------------------------------------------------------------ #
    def load_folder(self, folder: Path):
        """Construit la playlist à partir d’un répertoire."""
        exts = {'.mp3', '.wav', '.ogg'}
        self.playlist = sorted(p for p in folder.iterdir()
                               if p.suffix.lower() in exts)
        self.index = -1
        self.stop()

    # ------------------------------------------------------------------ #
    #   Lecture / pause / arrêt
    # ------------------------------------------------------------------ #
    def _load_current(self):
        """Charge le fichier pointé par self.index."""
        if not (0 <= self.index < len(self.playlist)):
            return False
        path = str(self.playlist[self.index])
        if self._sound:
            self._sound.stop()
            self._sound.unload()
        self._sound = SoundLoader.load(path)
        if not self._sound:
            return False
        self.duration = self._sound.length or 0.0
        self.position = 0.0
        self._apply_volume()
        return True

    def play(self):
        """Joue la piste actuelle ; si aucune piste n’est sélectionnée, on démarre la première."""
        if self._sound is None:
            if not self.playlist:
                return
            self.index = 0
            if not self._load_current():
                return
        self._sound.play()

    def pause(self):
        if self._sound:
            self._sound.stop()      # ffpyplayer implémente stop() comme pause

    def stop(self):
        if self._sound:
            self._sound.stop()
            self._sound.unload()
            self._sound = None
        self.position = 0.0
        self.duration = 0.0

    # ------------------------------------------------------------------ #
    #   Navigation (next / previous)
    # ------------------------------------------------------------------ #
    def next(self):
        if not self.playlist:
            return
        if self.shuffle:
            self.index = random.randint(0, len(self.playlist) - 1)
        else:
            self.index += 1
            if self.index >= len(self.playlist):
                if self.repeat_mode == 'all':
                    self.index = 0
                else:
                    self.index = len(self.playlist) - 1
                    self.stop()
                    return
        self._load_current()
        self.play()

    def previous(self):
        if not self.playlist:
            return
        if self.shuffle:
            self.index = random.randint(0, len(self.playlist) - 1)
        else:
            self.index -= 1
            if self.index < 0:
                if self.repeat_mode == 'all':
                    self.index = len(self.playlist) - 1
                else:
                    self.index = 0
        self._load_current()
        self.play()

    # ------------------------------------------------------------------ #
    #   Modes de répétition & shuffle
    # ------------------------------------------------------------------ #
    def set_repeat(self, mode: str):
        """mode ∈ {'none','single','all'}"""
        if mode in ('none', 'single', 'all'):
            self.repeat_mode = mode

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle

    # ------------------------------------------------------------------ #
    #   Volume & mute
    # ------------------------------------------------------------------ #
    def _apply_volume(self):
        if self._sound:
            vol = 0.0 if self.muted else self.volume
            self._sound.volume = vol

    def set_volume(self, v: float):
        """v entre 0.0 et 1.0"""
        self.volume = max(0.0, min(1.0, v))
        self._apply_volume()

    def toggle_mute(self):
        self.muted = not self.muted
        self._apply_volume()

    # ------------------------------------------------------------------ #
    #   Seek (progression)
    # ------------------------------------------------------------------ #
    def seek(self, seconds: float):
        """Déplace le curseur à `seconds` (si le backend le supporte)."""
        if self._sound and self.duration:
            seconds = max(0.0, min(self.duration, seconds))
            # ffpyplayer expose `seek` via `seek(position)` (en secondes)
            try:
                self._sound.seek(seconds)
                self.position = seconds
            except Exception:
                pass

    def update_position(self, dt: float):
        """À appeler chaque 0.1 s via Clock.schedule_interval."""
        if self._sound and self._sound.state == 'play':
            # ffpyplayer expose `get_pos()` en secondes
            try:
                self.position = self._sound.get_pos()
            except Exception:
                pass

        # Gestion du mode « single repeat »
        if self.repeat_mode == 'single' and self._sound:
            if self.position >= self.duration:
                self.seek(0.0)          # recommence la même piste
                self.play()
    @property
    def current_track_text(self):
        if 0 <= self.index < len(self.playlist):
            return self.playlist[self.index].name
        return "Aucun fichier sélectionné"