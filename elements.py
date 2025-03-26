from PyQt5.QtWidgets import QPushButton, QApplication
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QRect, QSize
from PyQt5.QtGui import QIcon

class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None, **kwargs):
        super().__init__(text, parent)

        # Default properties
        self._color = kwargs.get("color", "#D91656")  # Default button color
        self._hover_color = kwargs.get("hover_color", "#640D5F")  # Hover color
        self._pressed_color = kwargs.get("pressed_color", "#4A0A4A")  # Pressed color
        self._text_color = kwargs.get("text_color", "white")  # Text color
        self._hover_text_color = kwargs.get("hover_text_color", "white")  # Hover text color
        self._pressed_text_color = kwargs.get("pressed_text_color", "white")  # Pressed text color
        self._border_radius = kwargs.get("border_radius", 5)  # Border radius
        self._border_color = kwargs.get("border_color", "transparent")  # Border color
        self._hover_border_color = kwargs.get("hover_border_color", "transparent")  # Hover border color
        self._pressed_border_color = kwargs.get("pressed_border_color", "transparent")  # Pressed border color
        self._font_size = kwargs.get("font_size", 14)  # Font size
        self._font_family = kwargs.get("font_family", "Arial")  # Font family
        self._icon = kwargs.get("icon", None)  # Optional icon
        self._icon_size = kwargs.get("icon_size", QSize(24, 24))  # Icon size
        self._animation_duration = kwargs.get("animation_duration", 300)  # Animation duration

        # Store the original geometry of the button
        self._original_geometry = self.geometry()

        # Animation for hover effect
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(self._animation_duration)
        self._animation.setEasingCurve(QEasingCurve.OutCirc)

        # Flag to track hover state
        self._is_hovered = False

        # Apply initial styles
        self._update_styles()

        # Set icon if provided
        if self._icon:
            self.setIcon(QIcon(self._icon))
            self.setIconSize(self._icon_size)

    def _update_styles(self):
        """Update the button's stylesheet based on current properties."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                color: {self._text_color};
                padding: 10px 20px;
                font-size: {self._font_size}px;
                font-family: {self._font_family};
                border-radius: {self._border_radius}px;
                border: 2px solid {self._border_color};
            }}
            QPushButton:hover {{
                background-color: {self._hover_color};
                color: {self._hover_text_color};
                border-color: {self._hover_border_color};
            }}
            QPushButton:pressed {{
                background-color: {self._pressed_color};
                color: {self._pressed_text_color};
                border-color: {self._pressed_border_color};
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #888888;
                border-color: #999999;
            }}
        """)

    def enterEvent(self, a0):
        """Triggered when the mouse enters the button area."""
        self._is_hovered = True
        self._animation.stop()  # Stop any ongoing animation
        self._animation.setStartValue(self.geometry())
        # Calculate target geometry (grow slightly)
        target_geometry = QRect(
            self.x() - 10,  # Move left by 10px
            self.y() - 5,   # Move up by 5px
            self.width() + 20,  # Increase width by 20px
            self.height() + 10   # Increase height by 10px
        )
        self._animation.setEndValue(target_geometry)
        self._animation.start()
        super().enterEvent(a0)

    def leaveEvent(self, a0):
        """Triggered when the mouse leaves the button area."""
        self._is_hovered = False
        self._animation.stop()  # Stop any ongoing animation
        self._animation.setStartValue(self.geometry())
        self._animation.setEndValue(self._original_geometry)  # Return to original geometry
        self._animation.start()
        super().leaveEvent(a0)

    def resizeEvent(self, a0):
        """Update the original geometry when the button is resized."""
        self._original_geometry = self.geometry()
        super().resizeEvent(a0)

    # Dynamic property setters
    def set_color(self, color):
        self._color = color
        self._update_styles()

    def set_hover_color(self, hover_color):
        self._hover_color = hover_color
        self._update_styles()

    def set_pressed_color(self, pressed_color):
        self._pressed_color = pressed_color
        self._update_styles()

    def set_text_color(self, text_color):
        self._text_color = text_color
        self._update_styles()

    def set_hover_text_color(self, hover_text_color):
        self._hover_text_color = hover_text_color
        self._update_styles()

    def set_pressed_text_color(self, pressed_text_color):
        self._pressed_text_color = pressed_text_color
        self._update_styles()

    def set_border_radius(self, border_radius):
        self._border_radius = border_radius
        self._update_styles()

    def set_border_color(self, border_color):
        self._border_color = border_color
        self._update_styles()

    def set_hover_border_color(self, hover_border_color):
        self._hover_border_color = hover_border_color
        self._update_styles()

    def set_pressed_border_color(self, pressed_border_color):
        self._pressed_border_color = pressed_border_color
        self._update_styles()

    def set_font_size(self, font_size):
        self._font_size = font_size
        self._update_styles()

    def set_font_family(self, font_family):
        self._font_family = font_family
        self._update_styles()

    def set_icon(self, icon_path):
        self._icon = icon_path
        self.setIcon(QIcon(self._icon))

    def set_icon_size(self, icon_size):
        self._icon_size = icon_size
        self.setIconSize(self._icon_size)

    def set_animation_duration(self, duration):
        self._animation_duration = duration
        self._animation.setDuration(duration)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # Create a button with custom properties
    button = AnimatedButton(
        text="Click Me",
        color="#007BFF",
        hover_color="#0056b3",
        pressed_color="#004080",
        text_color="white",
        hover_text_color="white",
        pressed_text_color="white",
        border_radius=10,
        border_color="#007BFF",
        hover_border_color="#0056b3",
        pressed_border_color="#004080",
        font_size=16,
        font_family="Arial",
        icon="path/to/icon.png",
        icon_size=QSize(32, 32),
        animation_duration=200
    )

    button.show()
    sys.exit(app.exec_())