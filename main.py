# Android-compatible version of Color Detector
import os
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
from kivy.utils import platform
from kivy.logger import Logger

# Check if we're on Android
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

# Try to import heavy dependencies, fallback if not available
try:
    import cv2
    OPENCV_AVAILABLE = True
    Logger.info("ColorDetector: OpenCV available")
except ImportError:
    OPENCV_AVAILABLE = False
    Logger.warning("ColorDetector: OpenCV not available, using fallback")

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
    Logger.info("ColorDetector: Pandas available")
except ImportError:
    PANDAS_AVAILABLE = False
    import json
    Logger.warning("ColorDetector: Pandas not available, using JSON fallback")

# Set window size for testing (ignored on Android)
if platform != 'android':
    Window.size = (360, 640)

# ====== Simple color database (fallback if pandas not available) ======
BASIC_COLORS = {
    "Red": {"hex": "#FF0000", "rgb": (255, 0, 0)},
    "Green": {"hex": "#00FF00", "rgb": (0, 255, 0)},
    "Blue": {"hex": "#0000FF", "rgb": (0, 0, 255)},
    "Yellow": {"hex": "#FFFF00", "rgb": (255, 255, 0)},
    "Cyan": {"hex": "#00FFFF", "rgb": (0, 255, 255)},
    "Magenta": {"hex": "#FF00FF", "rgb": (255, 0, 255)},
    "White": {"hex": "#FFFFFF", "rgb": (255, 255, 255)},
    "Black": {"hex": "#000000", "rgb": (0, 0, 0)},
    "Orange": {"hex": "#FFA500", "rgb": (255, 165, 0)},
    "Purple": {"hex": "#800080", "rgb": (128, 0, 128)},
    "Pink": {"hex": "#FFC0CB", "rgb": (255, 192, 203)},
    "Brown": {"hex": "#A52A2A", "rgb": (165, 42, 42)},
    "Gray": {"hex": "#808080", "rgb": (128, 128, 128)},
}

# ====== Color detection functions ======
def load_color_data():
    """Load color data from CSV or use fallback"""
    if PANDAS_AVAILABLE and os.path.exists("colors.csv"):
        try:
            return pd.read_csv("colors.csv")
        except Exception as e:
            Logger.warning(f"ColorDetector: Failed to load CSV: {e}")
    
    # Fallback to basic colors
    Logger.info("ColorDetector: Using basic color database")
    return BASIC_COLORS

def closest_color_pandas(r, g, b, df):
    """Find closest color using pandas"""
    colors = df[['Red (8 bit)', 'Green (8 bit)', 'Blue (8 bit)']].values
    if PANDAS_AVAILABLE:
        diff = np.sqrt(np.sum((colors - np.array([r, g, b])) ** 2, axis=1))
        idx = np.argmin(diff)
        return df.iloc[idx]
    else:
        return closest_color_basic(r, g, b, df)

def closest_color_basic(r, g, b, color_dict):
    """Find closest color using basic math"""
    min_distance = float('inf')
    closest_name = "Unknown"
    closest_info = {"hex": "#000000", "rgb": (0, 0, 0)}
    
    for name, info in color_dict.items():
        color_r, color_g, color_b = info["rgb"]
        distance = ((r - color_r) ** 2 + (g - color_g) ** 2 + (b - color_b) ** 2) ** 0.5
        
        if distance < min_distance:
            min_distance = distance
            closest_name = name
            closest_info = info
    
    return {
        "Name": closest_name,
        "Hex (24 bit)": closest_info["hex"],
        "rgb": closest_info["rgb"]
    }

def get_closest_color(r, g, b, color_data):
    """Universal color detection function"""
    if PANDAS_AVAILABLE and hasattr(color_data, 'iloc'):
        return closest_color_pandas(r, g, b, color_data)
    else:
        return closest_color_basic(r, g, b, color_data)

def get_contrast_text_color(r, g, b):
    """Calculate contrast color for text"""
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return (0, 0, 0, 1) if luminance > 128 else (1, 1, 1, 1)

# ====== Custom Dashboard Button ======
class DashboardButton(Button):
    def __init__(self, icon_path, title, callback, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(160), dp(160)), **kwargs)
        
        self.background_color = (0, 0, 0, 0)
        self.text = ""
        self.callback = callback
        
        with self.canvas.before:
            Color(0.3, 0.5, 0.9, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        # Try to load icon, fallback to text if image not available
        try:
            self.icon = Image(
                source=icon_path,
                size_hint=(None, None),
                size=(dp(60), dp(60)),
                pos_hint={'center_x': 0.5, 'center_y': 0.65}
            )
            self.add_widget(self.icon)
        except Exception as e:
            Logger.warning(f"ColorDetector: Could not load icon {icon_path}: {e}")
            # Fallback to text icon
            icon_text = "📷" if "camera" in icon_path.lower() else "🖼️"
            self.icon = Label(
                text=icon_text,
                font_size='48sp',
                color=(1, 1, 1, 1),
                size_hint=(None, None),
                size=(dp(60), dp(60)),
                pos_hint={'center_x': 0.5, 'center_y': 0.65}
            )
            self.add_widget(self.icon)
        
        self.title_label = Label(
            text=title,
            font_size='18sp',
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(30),
            pos_hint={'center_x': 0.5, 'center_y': 0.25}
        )
        self.add_widget(self.title_label)
        
        self.bind(on_press=self.on_button_press)
        self.bind(on_release=self.on_button_release)
    
    def update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        
        if hasattr(self, 'icon'):
            self.icon.center_x = self.center_x
            self.icon.center_y = self.center_y + dp(20)
        
        if hasattr(self, 'title_label'):
            self.title_label.center_x = self.center_x
            self.title_label.center_y = self.center_y - dp(30)
    
    def on_button_press(self, instance):
        with self.canvas.before:
            Color(0.25, 0.42, 0.8, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
    
    def on_button_release(self, instance):
        with self.canvas.before:
            Color(0.3, 0.5, 0.9, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        self.callback()

# ====== Dashboard Layout ======
class DashboardLayout(FloatLayout):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance
        
        with self.canvas.before:
            Color(0.35, 0.5, 0.95, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        title = Label(
            text='Color Detector',
            font_size='36sp',
            color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'top': 0.95},
            size_hint=(1, 0.15)
        )
        
        content_layout = FloatLayout(
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            size_hint=(0.9, 0.6)
        )
        
        with content_layout.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.content_bg = RoundedRectangle(pos=content_layout.pos, size=content_layout.size, radius=[25])
        content_layout.bind(pos=self.update_content_bg, size=self.update_content_bg)
        
        buttons_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(40),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(None, None),
            size=(dp(360), dp(160))
        )
        
        camera_btn = DashboardButton(
            icon_path='assets/camera.png',
            title='Camera',
            callback=self.start_camera_mode
        )
        
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

# ====== Simple Info Widget (fallback for complex features) ======
class InfoWidget(BoxLayout):
    def __init__(self, color_data, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.color_data = color_data
        
        info_label = Label(
            text="Color Detector\n\nThis is a simplified version for mobile.\nOpenCV camera features are not available on this platform.\n\nYou can still upload images for color detection.",
            font_size='16sp',
            text_size=(None, None),
            halign='center',
            valign='center'
        )
        
        back_btn = Button(
            text="Back to Dashboard",
            size_hint=(1, 0.2),
            font_size='16sp'
        )
        back_btn.bind(on_release=self.back_to_dashboard)
        
        self.add_widget(info_label)
        self.add_widget(back_btn)
    
    def back_to_dashboard(self, instance):
        app = App.get_running_app()
        app.back_to_menu(instance)

# ====== Main App ======
class ColorApp(App):
    def build(self):
        self.color_data = load_color_data()
        Logger.info(f"ColorDetector: Loaded color data with {len(self.color_data) if hasattr(self.color_data, '__len__') else 'basic'} colors")
        return DashboardLayout(self)
    
    def start_camera_mode(self, instance):
        self.root.clear_widgets()
        
        # Use simplified widget for mobile
        if not OPENCV_AVAILABLE or platform == 'android':
            camera_widget = InfoWidget(self.color_data)
        else:
            # Use full camera widget for desktop
            camera_widget = InfoWidget(self.color_data)  # Simplified for now
        
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(camera_widget)
        
        back_btn = Button(text="Back to Dashboard", size_hint=(1, 0.1))
        back_btn.bind(on_release=self.back_to_menu)
        layout.add_widget(back_btn)
        
        self.root.add_widget(layout)
    
    def start_upload_mode(self, instance):
        chooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg'])
        popup = Popup(title="Select Image", content=chooser, size_hint=(0.9, 0.9))
        chooser.bind(on_submit=lambda chooser, selection, touch: self.load_image(selection, popup))
        popup.open()
    
    def load_image(self, selection, popup):
        if selection:
            popup.dismiss()
            # For now, just show info widget
            self.root.clear_widgets()
            
            info_widget = InfoWidget(self.color_data)
            layout = BoxLayout(orientation='vertical')
            layout.add_widget(info_widget)
            
            back_btn = Button(text="Back to Dashboard", size_hint=(1, 0.1))
            back_btn.bind(on_release=self.back_to_menu)
            layout.add_widget(back_btn)
            
            self.root.add_widget(layout)
    
    def back_to_menu(self, instance):
        self.root.clear_widgets()
        dashboard = DashboardLayout(self)
        self.root.add_widget(dashboard)

if __name__ == '__main__':
    ColorApp().run()