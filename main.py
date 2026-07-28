import os
import json
import random
import threading
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.button import MDFloatingActionButton, MDRaisedButton, MDIconButton
from kivymd.uix.list import OneLineIconListItem, IconLeftWidget
import yt_dlp

KV = '''
MDScreen:
    # Фоновая гифка (файл background.gif должен лежать рядом с main.py)
    FitImage:
        source: "background.gif"
        opacity: 0.35

    MDBoxLayout:
        orientation: 'vertical'
        padding: "15dp"
        spacing: "10dp"

        # Шапка с кастомом темы
        MDBoxLayout:
            adaptive_height: True
            MDLabel:
                text: "⚡ Vibe Player"
                font_style: "H5"
                bold: True
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
            
            MDIconButton:
                icon: "palette"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release: app.change_theme()

        # Поиск
        MDBoxLayout:
            adaptive_height: True
            spacing: "10dp"
            MDTextField:
                id: search_input
                hint_text: "Исполнитель и трек..."
                mode: "rectangle"
                text_color_normal: 1, 1, 1, 1
                hint_text_color_normal: 0.8, 0.8, 0.8, 1
            
            MDRaisedButton:
                text: "Искать"
                on_release: app.start_play_thread(search_input.text)

        # Статус
        MDLabel:
            id: status_label
            text: "Готов к музыке 🎧"
            halign: "center"
            adaptive_height: True
            theme_text_color: "Custom"
            text_color: 0.9, 0.9, 0.9, 1

        # Визуализатор
        VisualizerWidget:
            id: visualizer
            size_hint_y: None
            height: "50dp"

        # Плеер управление
        MDBoxLayout:
            adaptive_size: True
            pos_hint: {"center_x": .5}
            spacing: "15dp"

            MDFloatingActionButton:
                icon: "play"
                on_release: app.play_audio()

            MDFloatingActionButton:
                icon: "pause"
                on_release: app.pause_audio()

            MDFloatingActionButton:
                icon: "stop"
                on_release: app.stop_audio()

        # Создание плейлистов
        MDBoxLayout:
            adaptive_height: True
            spacing: "10dp"
            MDTextField:
                id: playlist_input
                hint_text: "Имя плейлиста..."
                mode: "rectangle"
                text_color_normal: 1, 1, 1, 1
                size_hint_x: 0.7
            
            MDRaisedButton:
                text: "+ в плейлист"
                size_hint_x: 0.3
                on_release: app.add_to_playlist(playlist_input.text)

        MDLabel:
            id: playlist_title
            text: "📂 Твои плейлисты:"
            font_style: "Subtitle2"
            adaptive_height: True
            theme_text_color: "Custom"
            text_color: 0.8, 0.8, 0.8, 1

        # Список треков по папкам
        MDScrollView:
            MDList:
                id: favorites_list
'''

class VisualizerWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bars = []
        self.anim_event = None
        self.is_active = False
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.6, 0.2, 0.9, 0.8)
            bar_width = self.width / 12
            self.bars = []
            for i in range(10):
                x = self.x + i * (bar_width + 4)
                h = random.randint(5, int(self.height)) if self.is_active else 5
                rect = Rectangle(pos=(x, self.y), size=(bar_width, h))
                self.bars.append(rect)

    def start_anim(self):
        self.is_active = True
        if not self.anim_event:
            self.anim_event = Clock.schedule_interval(self._animate_bars, 0.1)

    def stop_anim(self):
        self.is_active = False
        if self.anim_event:
            self.anim_event.cancel()
            self.anim_event = None
        self.update_canvas()

    def _animate_bars(self, dt):
        for rect in self.bars:
            rect.size = (rect.size[0], random.randint(5, int(self.height)))

class VibePlayerApp(MDApp):
    sound = None
    current_title = ""
    current_url = ""
    playlists = {} 
    # Полная палитра цветов
    themes = ["Red", "Pink", "Purple", "DeepPurple", "Indigo", "Blue", 
              "LightBlue", "Cyan", "Teal", "Green", "LightGreen", "Lime", 
              "Yellow", "Amber", "Orange", "DeepOrange", "Brown", "Gray", "BlueGray"]
    current_theme_idx = 3 # Начинаем с DeepPurple

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = self.themes[self.current_theme_idx]
        self.load_playlists()
        return Builder.load_string(KV)

    def on_start(self):
        self.update_playlists_ui()

    def change_theme(self):
        self.current_theme_idx = (self.current_theme_idx + 1) % len(self.themes)
        self.theme_cls.primary_palette = self.themes[self.current_theme_idx]

    def start_play_thread(self, query):
        if not query:
            self.set_status("Введите запрос!")
            return
        self.set_status("Ищем трек...")
        threading.Thread(target=self.fetch_and_play, args=(query,), daemon=True).start()

    def fetch_and_play(self, query):
        try:
            ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if 'entries' in info and len(info['entries']) > 0:
                    entry = info['entries'][0]
                    stream_url = entry['url']
                    title = entry['title']
                    self.current_title = title
                    self.current_url = stream_url
                    self.set_status(f"🎵 {title[:30]}...")
                    self.play_stream(stream_url)
                else:
                    self.set_status("Ничего не найдено 😔")
        except Exception as e:
            self.set_status(f"Ошибка: {str(e)[:30]}")

    def play_stream(self, url):
        self.stop_audio()
        try:
            from jnius import autoclass
            MediaPlayer = autoclass('android.media.MediaPlayer')
            self.sound = MediaPlayer()
            self.sound.setDataSource(url)
            self.sound.prepare()
            self.sound.start()
        except Exception:
            self.sound = SoundLoader.load(url)
            if self.sound:
                self.sound.play()
        self.root.ids.visualizer.start_anim()

    def play_audio(self):
        if self.sound:
            try: self.sound.start()
            except AttributeError: self.sound.play()
            self.root.ids.visualizer.start_anim()

    def pause_audio(self):
        if self.sound:
            try: self.sound.pause()
            except AttributeError: self.sound.stop()
            self.root.ids.visualizer.stop_anim()

    def stop_audio(self):
        if self.sound:
            try:
                self.sound.stop()
                self.sound.release()
            except Exception:
                self.sound.stop()
            self.sound = None
        self.root.ids.visualizer.stop_anim()

    @mainthread
    def set_status(self, text):
        self.root.ids.status_label.text = text

    def add_to_playlist(self, p_name):
        if not self.current_title:
            self.set_status("Сначала включи трек!")
            return
        
        p_name = p_name.strip()
        if not p_name:
            p_name = "Избранное"
        
        if p_name not in self.playlists:
            self.playlists[p_name] = []
        
        if self.current_title not in self.playlists[p_name]:
            self.playlists[p_name].append(self.current_title)
            self.save_playlists()
            self.update_playlists_ui()
            self.set_status(f"Добавлено в {p_name}!")
        else:
            self.set_status("Уже есть в плейлисте!")

    def load_playlists(self):
        if os.path.exists("playlists.json"):
            try:
                with open("playlists.json", "r", encoding="utf-8") as f:
                    self.playlists = json.load(f)
            except Exception:
                self.playlists = {}

    def save_playlists(self):
        with open("playlists.json", "w", encoding="utf-8") as f:
            json.dump(self.playlists, f, ensure_ascii=False)

    @mainthread
    def update_playlists_ui(self):
        fav_list = self.root.ids.favorites_list
        fav_list.clear_widgets()
        for p_name, tracks in self.playlists.items():
            header = OneLineIconListItem(text=f"📁 Плейлист: {p_name}", theme_text_color="Custom", text_color=(0.5, 0.5, 1, 1))
            header.add_widget(IconLeftWidget(icon="folder-music"))
            fav_list.add_widget(header)
            
            for t in tracks:
                item = OneLineIconListItem(text=f"  ↳ {t[:35]}...", on_release=lambda x, track=t: self.start_play_thread(track))
                fav_list.add_widget(item)

if __name__ == '__main__':
    VibePlayerApp().run()
