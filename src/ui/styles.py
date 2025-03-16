"""
styles.py

Description: UI styling and theme definitions
Usage:
    from src.ui.styles import get_stylesheet, ThemeColors
"""

from typing import Dict, Optional

from PySide6.QtGui import QColor

from src.services.config_manager import ConfigManager
from src.utils.constants import UI_THEME_COLORS


class ThemeColors:
    """
    Provides access to current theme colors.
    
    Attributes:
        primary (str): Primary color (dark blueish-purple)
        secondary (str): Secondary color (gold)
        background (str): Background color
        surface (str): Surface color for panels
        text_primary (str): Primary text color
        text_secondary (str): Secondary text color
        error (str): Error color
        warning (str): Warning color
        success (str): Success color
    """
    
    def __init__(self, theme: str = "dark") -> None:
        """
        Initialize theme colors.
        
        Args:
            theme (str): Theme name (dark or light)
        """
        self.theme = theme
        self._colors = UI_THEME_COLORS.get(theme, UI_THEME_COLORS["dark"])
        
        # Set color attributes
        self.primary = self._colors["primary"]
        self.secondary = self._colors["secondary"]
        self.background = self._colors["background"]
        self.surface = self._colors["surface"]
        self.text_primary = self._colors["text_primary"]
        self.text_secondary = self._colors["text_secondary"]
        self.error = self._colors["error"]
        self.warning = self._colors["warning"]
        self.success = self._colors["success"]
    
    @staticmethod
    def from_config() -> 'ThemeColors':
        """
        Create ThemeColors from application configuration.
        
        Returns:
            ThemeColors: Theme colors based on configuration
        """
        config = ConfigManager()
        theme = config.get("General", "default_theme", fallback="dark")
        return ThemeColors(theme)
    
    def to_qcolor(self, color_name: str) -> QColor:
        """
        Convert a theme color to QColor.
        
        Args:
            color_name (str): Name of the color (e.g., 'primary')
            
        Returns:
            QColor: The corresponding QColor
        """
        color_hex = getattr(self, color_name, "#000000")
        return QColor(color_hex)


def get_stylesheet(theme: Optional[str] = None) -> str:
    """
    Generate a stylesheet for the application.
    
    Args:
        theme (Optional[str]): Theme name (dark or light)
        
    Returns:
        str: Qt stylesheet as string
    """
    if theme is None:
        config = ConfigManager()
        theme = config.get("General", "default_theme", fallback="dark")
    
    colors = ThemeColors(theme)
    
    # Base stylesheet
    stylesheet = f"""
    /* Global Styles */
    QMainWindow, QDialog {{
        background-color: {colors.background};
        color: {colors.text_primary};
    }}
    
    QWidget {{
        background-color: transparent;
        color: {colors.text_primary};
    }}
    
    /* Navigation Panel */
    #navigationPanel {{
        background-color: {colors.surface};
        border: none;
        border-right: 1px solid {colors.primary};
        min-width: 200px;
        max-width: 250px;
    }}
    
    #navigationPanel QPushButton {{
        background-color: transparent;
        border: none;
        border-radius: 4px;
        color: {colors.text_primary};
        font-size: 14px;
        padding: 8px 16px;
        text-align: left;
    }}
    
    #navigationPanel QPushButton:hover {{
        background-color: rgba(255, 255, 255, 0.1);
    }}
    
    #navigationPanel QPushButton:checked {{
        background-color: {colors.primary};
        color: white;
    }}
    
    /* Content Panel */
    #contentPanel {{
        background-color: {colors.background};
    }}
    
    #filterPanel {{
        background-color: {colors.surface};
        border: none;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    #dataPanel {{
        background-color: {colors.background};
    }}
    
    /* Headers */
    QHeaderView::section {{
        background-color: {colors.primary};
        color: white;
        padding: 5px;
        border: none;
    }}
    
    /* Tables */
    QTableView {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        gridline-color: rgba(255, 255, 255, 0.1);
        selection-background-color: {colors.primary};
        selection-color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }}
    
    QTableView::item {{
        padding: 5px;
    }}
    
    QTableView::item:selected {{
        background-color: {colors.primary};
    }}
    
    /* Controls */
    QPushButton {{
        background-color: {colors.primary};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
    }}
    
    QPushButton:hover {{
        background-color: #3A2F6E;
    }}
    
    QPushButton:pressed {{
        background-color: #22184A;
    }}
    
    QPushButton:disabled {{
        background-color: #555555;
        color: #AAAAAA;
    }}
    
    QPushButton.accent {{
        background-color: {colors.secondary};
        color: black;
    }}
    
    QPushButton.accent:hover {{
        background-color: #E6C34A;
    }}
    
    QPushButton.accent:pressed {{
        background-color: #C29D33;
    }}
    
    QLineEdit, QComboBox, QSpinBox {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        padding: 6px;
    }}
    
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border: 1px solid {colors.primary};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        selection-background-color: {colors.primary};
        selection-color: white;
    }}
    
    /* Tabs */
    QTabWidget::pane {{
        border: 1px solid rgba(255, 255, 255, 0.1);
        background-color: {colors.surface};
    }}
    
    QTabBar::tab {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        padding: 8px 16px;
        border: none;
        border-bottom: 2px solid transparent;
    }}
    
    QTabBar::tab:selected {{
        border-bottom: 2px solid {colors.secondary};
    }}
    
    QTabBar::tab:hover {{
        background-color: rgba(255, 255, 255, 0.1);
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        background-color: {colors.background};
        width: 12px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors.surface};
        min-height: 20px;
        border-radius: 6px;
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background-color: {colors.background};
        height: 12px;
        margin: 0px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {colors.surface};
        min-width: 20px;
        border-radius: 6px;
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* Highlight styles */
    .error {{
        color: {colors.error};
    }}
    
    .warning {{
        color: {colors.warning};
    }}
    
    .success {{
        color: {colors.success};
    }}
    
    /* Labels */
    QLabel.heading {{
        font-size: 18px;
        font-weight: bold;
    }}
    
    QLabel.subheading {{
        font-size: 16px;
    }}
    
    /* Group boxes */
    QGroupBox {{
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        margin-top: 20px;
        padding-top: 15px;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        color: {colors.text_primary};
    }}
    """
    
    return stylesheet 