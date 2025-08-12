import cv2
import pandas as pd
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import RoundedRectangle
from kivy.metrics import dp


# ====== Fungsi untuk mencari warna terdekat ======
def closest_color(r, g, b, df):
    colors = df[['Red (8 bit)', 'Green (8 bit)', 'Blue (8 bit)']].values
    diff = np.sqrt(np.sum((colors - np.array([r, g, b])) ** 2, axis=1))
    idx = np.argmin(diff)
    return df.iloc[idx]


# ====== Widget Kamera dengan lingkaran di tengah ======
def get_contrast_text_color(r, g, b):
    # Hitung luminance (0 = gelap, 255 = terang)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return (0, 0, 0, 1) if luminance > 128 else (1, 1, 1, 1)  # Hitam jika terang, putih jika gelap

class CameraWidget(BoxLayout):
    def __init__(self, color_data, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.color_data = color_data
        self.img_widget = Image()
        self.label = Label(size_hint=(1, 0.1))
        self.add_widget(self.img_widget)
        self.add_widget(self.label)

        self.capture = cv2.VideoCapture(0)
        self.update()

    def update(self):
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.flip(frame, 0)
            h, w, _ = frame.shape
            cx, cy = w // 2, h // 2
            b, g, r = frame[cy, cx]
            color_info = closest_color(r, g, b, self.color_data)

            # Gambar lingkaran hijau di titik tengah
            cv2.circle(frame, (cx, cy), 10, (0, 255, 0), 2)

            # Update label di layar
            text_color = get_contrast_text_color(r, g, b)
            self.label.color = text_color
            self.label.text = f"{color_info['Name']} | {color_info['Hex (24 bit)']} | RGB: ({r},{g},{b})"
            self.label.canvas.before.clear()
            with self.label.canvas.before:
                Color(r/255, g/255, b/255, 1)  # background sesuai warna terdeteksi
                Rectangle(pos=self.label.pos, size=self.label.size)

            # Kirim frame ke Kivy
            buf = frame.tobytes()
            texture = Texture.create(size=(w, h), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.img_widget.texture = texture

        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.update(), 1/30)


# ====== Widget Upload Gambar ======
class ImageClickWidget(Image):
    def __init__(self, color_data, img_path, **kwargs):
        super().__init__(**kwargs)
        self.color_data = color_data
        self.img_path = img_path
        self.cv_img = cv2.imread(img_path)  # Menyimpan gambar asli
        self.cv_image = self.cv_img.copy()  # Working copy untuk manipulasi
        self.texture = self.cv2_texture(self.cv_img)
        
        # Tambahkan label untuk menampilkan informasi warna
        self.label = Label(size_hint=(1, 0.1), text="Klik pada gambar untuk mendeteksi warna")

    def cv2_texture(self, cv_img):
        h, w, _ = cv_img.shape
        buf = cv2.flip(cv_img, 0).tobytes()
        texture = Texture.create(size=(w, h), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        return texture

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            widget_x, widget_y = self.pos
            widget_w, widget_h = self.size

            # hitung koordinat relatif klik
            rel_x = (touch.x - widget_x) / widget_w
            rel_y = (touch.y - widget_y) / widget_h

            img_h, img_w, _ = self.cv_image.shape

            px = int(rel_x * img_w)
            py = int((1 - rel_y) * img_h)

            if 0 <= px < img_w and 0 <= py < img_h:
                b, g, r = self.cv_image[py, px]
                detected_color = (r, g, b)
                color_info = closest_color(r, g, b, self.color_data)
                
                print(f"Klik di ({px}, {py}) → {color_info['Name']} {detected_color}")

                # Buat salinan baru untuk menggambar lingkaran
                display_img = self.cv_image.copy()
                cv2.circle(display_img, (px, py), 5, (0, 255, 0), -1)
                self.texture = self.cv2_texture(display_img)

            return True
        return super().on_touch_down(touch)


# ====== Container untuk Image dan Label ======
class ImageContainer(BoxLayout):
    def __init__(self, color_data, img_path, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        self.image_widget = ImageClickWidget(color_data, img_path)
        self.label = Label(size_hint=(1, 0.1), text="Klik pada gambar untuk mendeteksi warna")
        
        self.add_widget(self.image_widget)
        self.add_widget(self.label)
        
        # Bind event untuk update label
        self.image_widget.bind(on_touch_down=self.update_color_info)
    
    def update_color_info(self, instance, touch):
        if instance.collide_point(*touch.pos):
            widget_x, widget_y = instance.pos
            widget_w, widget_h = instance.size

            rel_x = (touch.x - widget_x) / widget_w
            rel_y = (touch.y - widget_y) / widget_h

            img_h, img_w, _ = instance.cv_image.shape
            px = int(rel_x * img_w)
            py = int((1 - rel_y) * img_h)

            if 0 <= px < img_w and 0 <= py < img_h:
                b, g, r = instance.cv_image[py, px]
                color_info = closest_color(r, g, b, instance.color_data)
                
                # Update label
                self.label.text = f"{color_info['Name']} | {color_info['Hex (24 bit)']} | RGB: ({r},{g},{b})"
                
                # Update background color label
                self.label.canvas.before.clear()
                with self.label.canvas.before:
                    Color(r/255, g/255, b/255, 1)
                    Rectangle(pos=self.label.pos, size=self.label.size)
                
                # Set text color for contrast
                text_color = get_contrast_text_color(r, g, b)
                self.label.color = text_color


# ====== Custom Dashboard Button ======
class DashboardButton(Button):
    def __init__(self, icon_path, title, callback, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(160), dp(160)), **kwargs)
        
        # Set transparent background for custom drawing
        self.background_color = (0, 0, 0, 0)
        self.text = ""  # No text for Button
        
        # Store callback
        self.callback = callback
        
        # Create custom background
        with self.canvas.before:
            Color(0.3, 0.5, 0.9, 1)  # Blue color
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        # Add icon image
        self.icon = Image(
            source=icon_path,
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            pos_hint={'center_x': 0.5, 'center_y': 0.65}
        )
        
        # Add title label
        self.title_label = Label(
            text=title,
            font_size='18sp',
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(30),
            pos_hint={'center_x': 0.5, 'center_y': 0.25}
        )
        
        # Add widgets
        self.add_widget(self.icon)
        self.add_widget(self.title_label)
        
        # Bind press events
        self.bind(on_press=self.on_button_press)
        self.bind(on_release=self.on_button_release)
    
    def update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        
        # Update icon position
        self.icon.center_x = self.center_x
        self.icon.center_y = self.center_y + dp(20)
        
        # Update title position  
        self.title_label.center_x = self.center_x
        self.title_label.center_y = self.center_y - dp(30)
    
    def on_button_press(self, instance):
        # Darker color when pressed
        with self.canvas.before:
            Color(0.25, 0.42, 0.8, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
    
    def on_button_release(self, instance):
        # Reset to original color
        with self.canvas.before:
            Color(0.3, 0.5, 0.9, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        
        # Execute callback
        self.callback()


# ====== Dashboard Layout ======
class DashboardLayout(FloatLayout):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance
        
        # Background color
        with self.canvas.before:
            Color(0.35, 0.5, 0.95, 1)  # Light blue background
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        # Title
        title = Label(
            text='Dashboard',
            font_size='36sp',
            color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'top': 0.95},
            size_hint=(1, 0.15)
        )
        
        # Container for dashboard content
        content_layout = FloatLayout(
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            size_hint=(0.9, 0.6)
        )
        
        # Add white rounded background for content
        with content_layout.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # Light gray background
            self.content_bg = RoundedRectangle(pos=content_layout.pos, size=content_layout.size, radius=[25])
        content_layout.bind(pos=self.update_content_bg, size=self.update_content_bg)
        
        # Buttons container
        buttons_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(40),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(None, None),
            size=(dp(360), dp(160))
        )
        
        # Camera button
        camera_btn = DashboardButton(
            icon_path='assets/camera.png',
            title='Camera',
            callback=self.start_camera_mode
        )
        
        # Upload button  
        upload_btn = DashboardButton(
            icon_path='assets/upload.png',
            title='Upload',
            callback=self.start_upload_mode
        )
        
        buttons_layout.add_widget(camera_btn)
        buttons_layout.add_widget(upload_btn)
        content_layout.add_widget(buttons_layout)
        
        self.add_widget(title)
        self.add_widget(content_layout)
    
    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def update_content_bg(self, instance, *args):
        self.content_bg.pos = instance.pos
        self.content_bg.size = instance.size
    
    def start_camera_mode(self):
        self.app.start_camera_mode(None)
    
    def start_upload_mode(self):
        self.app.start_upload_mode(None)


# ====== Layout Utama ======
class ColorApp(App):
    def build(self):
        self.color_data = pd.read_csv("colors.csv")
        return DashboardLayout(self)

    def start_camera_mode(self, instance):
        self.root.clear_widgets()
        camera_widget = CameraWidget(self.color_data)
        
        # Tambahkan tombol kembali
        back_btn = Button(text="Kembali ke Menu", size_hint=(1, 0.1))
        back_btn.bind(on_release=self.back_to_menu)
        
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(camera_widget)
        layout.add_widget(back_btn)
        
        self.root.add_widget(layout)

    def start_upload_mode(self, instance):
        chooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg'])
        popup = Popup(title="Pilih Gambar", content=chooser, size_hint=(0.9, 0.9))
        chooser.bind(on_submit=lambda chooser, selection, touch: self.load_image(selection, popup))
        popup.open()

    def load_image(self, selection, popup):
        if selection:
            img_path = selection[0]
            self.root.clear_widgets()
            
            # Buat container dengan tombol kembali
            main_layout = BoxLayout(orientation='vertical')
            image_container = ImageContainer(self.color_data, img_path)
            back_btn = Button(text="Kembali ke Menu", size_hint=(1, 0.1))
            back_btn.bind(on_release=self.back_to_menu)
            
            main_layout.add_widget(image_container)
            main_layout.add_widget(back_btn)
            
            self.root.add_widget(main_layout)
            popup.dismiss()

    def back_to_menu(self, instance):
        # Bersihkan widget dan kembali ke dashboard
        self.root.clear_widgets()
        dashboard = DashboardLayout(self)
        self.root.add_widget(dashboard)


if __name__ == '__main__':
    ColorApp().run()