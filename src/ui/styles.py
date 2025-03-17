"""
styles.py

Description: Application-wide styles and color definitions
Usage:
    from src.ui.styles import get_stylesheet, COLORS
    app.setStyleSheet(get_stylesheet())
"""

from typing import Dict

# Color palette
COLORS = {
    # Base colors
    "primary_dark": "#0f1a2c",  # Dark blue (background)
    "primary": "#1e2f4d",  # Medium blue (components)
    "primary_light": "#2a4270",  # Light blue (hover states)
    # Accent colors
    "accent": "#f0c040",  # Gold (primary accent)
    "accent_dark": "#d4a520",  # Dark gold (hover for accent elements)
    "accent_light": "#ffdc7a",  # Light gold (highlights)
    # Semantic colors
    "success": "#4caf50",
    "warning": "#ff9800",
    "error": "#f44336",
    "info": "#2196f3",
    # Text colors
    "text_primary": "#ffffff",
    "text_secondary": "#b0bec5",
    "text_disabled": "#78909c",
    # Border colors
    "border": "#3f5178",
    "border_light": "#546e7a",
    # Special elements
    "sidebar": "#15263e",
    "card": "#1e2f4d",
    "tooltip": "#15263e",
}


def get_stylesheet() -> str:
    """
    Get the application-wide stylesheet.

    Returns:
        The complete CSS stylesheet as a string
    """
    return f"""
    /* Global */
    QWidget {{
        background-color: {COLORS["primary_dark"]};
        color: {COLORS["text_primary"]};
        font-family: "Segoe UI", "Arial", sans-serif;
        font-size: 10pt;
    }}
    
    /* Main window */
    QMainWindow {{
        background-color: {COLORS["primary_dark"]};
    }}

    /* Sidebar */
    #sidebar {{
        background-color: {COLORS["sidebar"]};
        min-width: 200px;
        max-width: 300px;
        padding: 0px;
        margin: 0px;
        border-right: 1px solid {COLORS["border"]};
    }}
    
    #sidebar QPushButton {{
        background-color: transparent;
        border: none;
        color: {COLORS["text_primary"]};
        text-align: left;
        padding: 10px 15px;
        font-size: 11pt;
        font-weight: normal;
    }}
    
    #sidebar QPushButton:hover {{
        background-color: {COLORS["primary_light"]};
    }}
    
    #sidebar QPushButton:checked {{
        background-color: {COLORS["primary"]};
        border-left: 3px solid {COLORS["accent"]};
        font-weight: bold;
    }}
    
    #sidebarHeader {{
        background-color: {COLORS["primary"]};
        color: {COLORS["accent"]};
        padding: 15px;
        font-size: 14pt;
        font-weight: bold;
    }}
    
    /* Panels & Groups */
    QGroupBox {{
        background-color: {COLORS["primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding-top: 20px;
        margin-top: 10px;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 5px 10px;
        font-weight: bold;
        color: {COLORS["accent"]};
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {COLORS["primary"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS["primary_light"]};
        border-color: {COLORS["accent"]};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS["primary_dark"]};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS["primary_dark"]};
        color: {COLORS["text_disabled"]};
        border-color: {COLORS["border"]};
    }}
    
    QPushButton#accentButton {{
        background-color: {COLORS["accent"]};
        color: {COLORS["primary_dark"]};
        border-color: {COLORS["accent_dark"]};
    }}
    
    QPushButton#accentButton:hover {{
        background-color: {COLORS["accent_light"]};
    }}
    
    QPushButton#accentButton:pressed {{
        background-color: {COLORS["accent_dark"]};
    }}
    
    /* Tool buttons */
    QToolButton {{
        background-color: {COLORS["primary"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 4px;
    }}
    
    QToolButton:hover {{
        background-color: {COLORS["primary_light"]};
        border-color: {COLORS["accent"]};
    }}
    
    QToolButton:pressed {{
        background-color: {COLORS["primary_dark"]};
    }}
    
    QToolButton:disabled {{
        background-color: {COLORS["primary_dark"]};
        color: {COLORS["text_disabled"]};
        border-color: {COLORS["border"]};
    }}
    
    /* Input fields */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {COLORS["primary_dark"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 5px;
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {COLORS["accent"]};
    }}
    
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
        background-color: {COLORS["primary_dark"]};
        color: {COLORS["text_disabled"]};
        border-color: {COLORS["border"]};
    }}
    
    /* Combo box */
    QComboBox {{
        background-color: {COLORS["primary"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 5px;
        min-height: 20px;
    }}
    
    QComboBox:hover {{
        border-color: {COLORS["accent"]};
    }}
    
    QComboBox:focus {{
        border-color: {COLORS["accent"]};
    }}
    
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 20px;
        border-left: 1px solid {COLORS["border"]};
    }}
    
    QComboBox::down-arrow {{
        width: 12px;
        height: 12px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS["primary"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        selection-background-color: {COLORS["primary_light"]};
    }}
    
    /* Check box */
    QCheckBox {{
        color: {COLORS["text_primary"]};
        spacing: 5px;
    }}
    
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLORS["border"]};
        border-radius: 3px;
        background-color: {COLORS["primary_dark"]};
    }}
    
    QCheckBox::indicator:unchecked:hover {{
        border-color: {COLORS["accent"]};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {COLORS["accent"]};
        border-color: {COLORS["accent"]};
    }}
    
    /* Radio button */
    QRadioButton {{
        color: {COLORS["text_primary"]};
        spacing: 5px;
    }}
    
    QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        background-color: {COLORS["primary_dark"]};
    }}
    
    QRadioButton::indicator:unchecked:hover {{
        border-color: {COLORS["accent"]};
    }}
    
    QRadioButton::indicator:checked {{
        background-color: {COLORS["primary_dark"]};
        border: 2px solid {COLORS["accent"]};
    }}
    
    QRadioButton::indicator:checked::after {{
        content: "";
        display: block;
        width: 8px;
        height: 8px;
        border-radius: 4px;
        background-color: {COLORS["accent"]};
        margin: 4px;
    }}
    
    /* Tables */
    QTableView {{
        background-color: {COLORS["primary_dark"]};
        alternate-background-color: {COLORS["primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        gridline-color: {COLORS["border"]};
    }}
    
    QHeaderView::section {{
        background-color: {COLORS["primary"]};
        color: {COLORS["accent"]};
        padding: 5px;
        border: 1px solid {COLORS["border"]};
        font-weight: bold;
    }}
    
    QTableView::item {{
        padding: 5px;
    }}
    
    QTableView::item:selected {{
        background-color: {COLORS["primary_light"]};
        color: {COLORS["text_primary"]};
    }}
    
    /* List view */
    QListView {{
        background-color: {COLORS["primary_dark"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
    }}
    
    QListView::item {{
        padding: 5px;
    }}
    
    QListView::item:selected {{
        background-color: {COLORS["primary_light"]};
        color: {COLORS["text_primary"]};
    }}
    
    QListView::item:hover {{
        background-color: {COLORS["primary"]};
    }}
    
    /* Tabs */
    QTabWidget::pane {{
        border: 1px solid {COLORS["border"]};
        border-top: 0px;
        border-radius: 0px 0px 4px 4px;
    }}
    
    QTabBar::tab {{
        background-color: {COLORS["primary_dark"]};
        color: {COLORS["text_secondary"]};
        padding: 8px 16px;
        border: 1px solid {COLORS["border"]};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {COLORS["primary"]};
        color: {COLORS["accent"]};
        border-bottom: 2px solid {COLORS["accent"]};
    }}
    
    QTabBar::tab:!selected:hover {{
        background-color: {COLORS["primary"]};
        color: {COLORS["text_primary"]};
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        background: {COLORS["primary_dark"]};
        width: 10px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {COLORS["primary_light"]};
        border-radius: 5px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {COLORS["accent"]};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background: {COLORS["primary_dark"]};
        height: 10px;
        margin: 0px;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {COLORS["primary_light"]};
        border-radius: 5px;
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS["accent"]};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* Progress bar */
    QProgressBar {{
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        background-color: {COLORS["primary_dark"]};
        text-align: center;
        color: {COLORS["text_primary"]};
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS["accent"]};
        width: 10px;
        margin: 0.5px;
    }}
    
    /* Sliders */
    QSlider::groove:horizontal {{
        border: 1px solid {COLORS["border"]};
        background: {COLORS["primary_dark"]};
        height: 8px;
        border-radius: 4px;
    }}
    
    QSlider::handle:horizontal {{
        background: {COLORS["accent"]};
        border: 1px solid {COLORS["accent_dark"]};
        width: 18px;
        margin: -2px 0;
        border-radius: 9px;
    }}
    
    QSlider::handle:horizontal:hover {{
        background: {COLORS["accent_light"]};
    }}
    
    /* Spinbox */
    QSpinBox, QDoubleSpinBox {{
        background-color: {COLORS["primary_dark"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 5px;
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {COLORS["accent"]};
    }}
    
    /* Menu */
    QMenu {{
        background-color: {COLORS["primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
    }}
    
    QMenu::item {{
        padding: 5px 20px 5px 20px;
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS["primary_light"]};
        color: {COLORS["accent"]};
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {COLORS["border"]};
        margin: 5px 0px 5px 0px;
    }}
    
    /* Status bar */
    QStatusBar {{
        background-color: {COLORS["primary"]};
        color: {COLORS["text_secondary"]};
        border-top: 1px solid {COLORS["border"]};
    }}
    
    QStatusBar::item {{
        border: None;
    }}
    
    /* Labels */
    QLabel#title {{
        color: {COLORS["accent"]};
        font-size: 14pt;
        font-weight: bold;
    }}
    
    QLabel#subtitle {{
        color: {COLORS["text_secondary"]};
        font-size: 11pt;
        font-weight: bold;
    }}
    
    /* Dialog */
    QDialog {{
        background-color: {COLORS["primary_dark"]};
    }}
    
    QDialog QLabel {{
        color: {COLORS["text_primary"]};
    }}
    
    /* Message box */
    QMessageBox {{
        background-color: {COLORS["primary_dark"]};
    }}
    
    QMessageBox QLabel {{
        color: {COLORS["text_primary"]};
    }}
    
    QMessageBox QPushButton {{
        min-width: 80px;
    }}
    
    /* Tooltips */
    QToolTip {{
        background-color: {COLORS["tooltip"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 5px;
    }}
    
    /* Splitter */
    QSplitter::handle {{
        background-color: {COLORS["border"]};
    }}
    
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    
    QSplitter::handle:hover {{
        background-color: {COLORS["accent"]};
    }}
    
    /* Specific widget customizations */
    #fileImportWidget, #statisticsWidget, #validationStatusIndicator, #actionButtonGroup {{
        background-color: {COLORS["primary"]};
        border-radius: 4px;
        padding: 10px;
    }}
    
    QTabWidget#contentStack {{
        background-color: {COLORS["primary_dark"]};
    }}
    """


# Additional specific widget styles
SIDEBAR_STYLE = f"""
    QWidget#sidebar {{
        background-color: {COLORS["sidebar"]};
    }}
"""

ACCENT_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS["accent"]};
        color: {COLORS["primary_dark"]};
        border-color: {COLORS["accent_dark"]};
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS["accent_light"]};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS["accent_dark"]};
    }}
"""
