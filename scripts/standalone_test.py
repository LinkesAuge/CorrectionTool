"""
standalone_test.py

Description: Standalone test script for the DataFrameStore and UI adapters
Usage:
    python standalone_test.py
"""

import sys
import logging
import pandas as pd
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableView,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QLabel,
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class SimpleDataModel(QAbstractTableModel):
    """Simple table model for displaying pandas DataFrame."""

    def __init__(self, data=None):
        super().__init__()
        self._data = pd.DataFrame() if data is None else data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data.columns)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self._data.columns[section])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(self._data.index[section])
        return None

    def update_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()


class SimpleMainWindow(QMainWindow):
    """Simple main window for testing."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple DataFrame Test")
        self.resize(800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)

        # Create table view
        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        # Create model
        self.model = SimpleDataModel()
        self.table_view.setModel(self.model)

        # Create buttons
        button_layout = QHBoxLayout()

        self.load_data_btn = QPushButton("Load Test Data")
        self.load_data_btn.clicked.connect(self.load_test_data)
        button_layout.addWidget(self.load_data_btn)

        self.apply_corrections_btn = QPushButton("Apply Corrections")
        self.apply_corrections_btn.clicked.connect(self.apply_corrections)
        button_layout.addWidget(self.apply_corrections_btn)

        layout.addLayout(button_layout)

        # Create status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Initialize with test data
        self.load_test_data()

    def load_test_data(self):
        """Load test data into the model."""
        # Create test data
        data = {
            "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "chest_type": ["Gold", "Silver", "Bronze"],
            "player": ["Player1", "Player2", "Player3"],
            "source": ["Source1", "Source2", "Source3"],
            "status": ["Pending", "Pending", "Pending"],
        }
        df = pd.DataFrame(data)

        # Update model
        self.model.update_data(df)

        # Update status
        self.status_label.setText(f"Loaded {len(df)} entries")
        logger.info(f"Loaded test data with {len(df)} entries")

    def apply_corrections(self):
        """Apply test corrections to the data."""
        # Get current data
        df = self.model._data.copy()

        # Apply corrections
        df.loc[df["chest_type"] == "Gold", "chest_type"] = "Gold Chest"
        df.loc[df["chest_type"] == "Silver", "chest_type"] = "Silver Chest"
        df["status"] = "Valid"

        # Update model
        self.model.update_data(df)

        # Update status
        self.status_label.setText("Applied corrections")
        logger.info("Applied test corrections")


def main():
    """Main function."""
    app = QApplication(sys.argv)
    window = SimpleMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
