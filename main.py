import os
# Настройка фонового воспроизведения для Kivy
os.environ['KIVY_AUDIO'] = 'ffpyplayer' 

from kivy.lang import Builder
from kivy.core.audio import SoundLoader
from kivymd.app import MDApp
from kivymd.uix.button import MDFloatingActionButton, MDRaisedButton
import threading
import yt_dlp

# KV-разметка интерфейса
KV = '''
MDScreen:
    md_bg_color: 0.1, 0.1, 0.1, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "20dp"
        spacing: "20dp"

        MDLabel:
            text: "My Vibe Player"
            font_style: "H4"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1

        MDTextField:
            id: search_input
            hint_text: "Введите 'Исполнитель - Трек'"
            mode: "rectangle"
            text_color_normal: 1, 1, 1, 1
            hint_text_color_normal: 0.7, 0.7, 0.7, 1

        MDRaisedButton:
            text: "Найти и включить"
            pos_hint: {"center_x": .5}
            on_release: app.start_play_thread()

        MDLabel:
            id: status_label
            text: "Статус: Ожидание..."
            halign: "center"
            theme_text_color: "Custom"
            text_color: 0.8, 0.8, 0.8, 1

        MDBoxLayout:
            orientation: 'horizontal'
            spacing: "30dp"
            adaptive_size: True
            pos_hint: {"center_x": .5}

            MDFloatingActionButton:
                icon: "play"
                on_release: app.play_audio()

            MDFloatingActionButton:
                icon: "pause"
                on_release: app.pause_audio()

            MDFloatingActionButton:
                icon: "stop"
                on_release: app.stop_audio()
'''

class VibePlayerApp(MDApp):
    sound = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        return Builder.load_string(KV)

    def start_play_thread(self):
        query = self.root.ids.search_input.text
        if not query:
            self.root.ids.status_label.text = "Введите название!"
            return
        
        self.root.ids.status_label.text = "Ищем поток на YouTube..."
        # Запускаем поиск в отдельном потоке, чтобы UI не зависал
        threading.Thread(target=self.fetch_and_play, args=(query,), daemon=True).start()

    def fetch_and_play(self, query):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if 'entries' in info and len(info['entries']) > 0:
                    stream_url = info['entries'][0]['url']
                    title = info['entries'][0]['title']
                    
                    self.root.ids.status_label.text = f"Играет: {title[:30]}..."
                    self.play_stream(stream_url)
                else:
                    self.root.ids.status_label.text = "Ничего не найдено :-("
        except Exception as e:
            self.root.ids.status_label.text = f"Ошибка: {str(e)[:30]}"

    def play_stream(self, url):
        if self.sound:
            self.sound.stop()
        
        self.sound = SoundLoader.load(url)
        if self.sound:
            self.sound.play()

    def play_audio(self):
        if self.sound:
            self.sound.play()

    def pause_audio(self):
        if self.sound and self.sound.state == 'play':
            self.sound.stop() # В Kivy базовый SoundLoader ставит стоп при паузе

    def stop_audio(self):
        if self.sound:
            self.sound.stop()
            self.root.ids.status_label.text = "Остановлено"

if __name__ == '__main__':
    VibePlayerApp().run()