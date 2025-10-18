from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.graphics import Color, Rectangle
from kivy.event import EventDispatcher
from kivy.core.audio import SoundLoader
import os
import time


# --------------------------------------------------------------
#  VISUALISATEUR (placeholder visuel)
# --------------------------------------------------------------
class VisualizerCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0.2, 0.7, 0.3, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# --------------------------------------------------------------
#  PLAYER : version avec vrai son
# --------------------------------------------------------------
class Player(EventDispatcher):
    current_track_text = StringProperty("No track loaded")
    position = NumericProperty(0.0)
    duration = NumericProperty(0.0)
    volume = NumericProperty(0.5)
    muted = BooleanProperty(False)
    shuffle = BooleanProperty(False)
    repeat_mode = StringProperty("none")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.playing = False
        self.sound = None
        self.file_path = None

    def load(self, filename):
        """Charge un fichier audio"""
        if self.sound:
            self.sound.stop()
        self.sound = SoundLoader.load(filename)
        if self.sound:
            self.file_path = filename
            self.duration = self.sound.length or 0.0
            self.current_track_text = f"🎵 Loaded: {os.path.basename(filename)}"
        else:
            self.current_track_text = "❌ Impossible de charger le fichier"

    def play(self):
        if not self.sound:
            self.current_track_text = "⚠️ Aucun fichier audio chargé"
            return
        self.sound.play()
        self.playing = True
        self.current_track_text = f"▶️ Playing: {os.path.basename(self.file_path)}"

    def pause(self):
        if self.sound:
            self.sound.stop()
        self.playing = False
        self.current_track_text = "⏸ Paused"

    def stop(self):
        if self.sound:
            self.sound.stop()
        self.playing = False
        self.position = 0
        self.current_track_text = "⏹ Stopped"

    def set_volume(self, value):
        self.volume = value
        if self.sound:
            self.sound.volume = value
        if not self.muted:
            self.current_track_text = f"🔊 Volume: {int(value * 100)}%"

    def toggle_mute(self):
        self.muted = not self.muted
        if self.sound:
            self.sound.volume = 0 if self.muted else self.volume
        self.current_track_text = "🔇 Muted" if self.muted else f"🔊 Volume: {int(self.volume * 100)}%"

    def update(self, dt):
        """Met à jour la position de lecture"""
        if self.playing and self.sound:
            self.position = self.sound.get_pos() or 0.0
            if self.position >= self.duration and self.duration > 0:
                self.stop()


# --------------------------------------------------------------
#  ROOT WIDGET
# --------------------------------------------------------------
class RootWidget(BoxLayout):
    music_files = ListProperty([])

    def on_music_files(self, instance, value):
        """S'exécute automatiquement quand music_files change"""
        self.ids.music_list.clear_widgets()
        from kivy.uix.button import Button
        import os
        for path in value:
            b = Button(text=os.path.basename(path), size_hint_y=None, height=40)
            b.bind(on_release=lambda btn, p=path: App.get_running_app().play_selected(p))
            self.ids.music_list.add_widget(b)

# --------------------------------------------------------------
#  APPLICATION PRINCIPALE
# --------------------------------------------------------------
class AudioPlayerApp(App):
    def build(self):
        Builder.load_file("audio_player.kv")
        self.player = Player()
        self.root_widget = RootWidget()

        Clock.schedule_interval(self.update_ui, 0.1)
        return self.root_widget

    # 🧭 Scan du dossier musique
    def scan_music_folder(self, folder_path="Musique"):
        """Scanne un dossier et liste les fichiers audio"""
        exts = (".mp3", ".wav", ".ogg", ".flac")
        found = []
        if os.path.exists(folder_path):
            for root, _, files in os.walk(folder_path):
                for f in files:
                    if f.lower().endswith(exts):
                        found.append(os.path.join(root, f))
        else:
            self.player.current_track_text = "⚠️ Dossier non trouvé"

        self.root_widget.music_files = found
        self.player.current_track_text = f"🎧 {len(found)} musiques trouvées"

    def play_selected(self, filepath):
        """Joue la musique sélectionnée dans la liste"""
        self.player.load(filepath)
        self.player.play()

    # --- UI updates ---
    def update_ui(self, dt):
        ids = self.root_widget.ids
        if "progress_slider" in ids:
            ids.progress_slider.value = self.player.position
        if "current_track" in ids:
            ids.current_track.text = self.player.current_track_text
        if "elapsed" in ids:
            ids.elapsed.text = "{:02d}:{:02d}".format(
                int(self.player.position)//60, int(self.player.position)%60)
        if "total" in ids:
            ids.total.text = "{:02d}:{:02d}".format(
                int(self.player.duration)//60, int(self.player.duration)%60)
        if "volume_slider" in ids:
            ids.volume_slider.value = self.player.volume

    def toggle_play(self):
        if self.player.playing:
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        self.player.stop()

    def toggle_mute(self):
        self.player.toggle_mute()

    def set_volume(self, value):
        self.player.set_volume(value)


# --------------------------------------------------------------
#  POINT D’ENTRÉE
# --------------------------------------------------------------
if __name__ == "__main__":
    AudioPlayerApp().run()
