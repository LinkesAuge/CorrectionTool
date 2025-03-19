#!/usr/bin/env python3
"""
run_standalone_app.py

Description: A standalone script to run the Chest Tracker Correction Tool with the refactored components
             This script avoids circular imports by using a minimal set of imports and leverages
             the standalone test modules.
Usage:
    python run_standalone_app.py
"""

import logging
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Import PySide6
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
    QMessageBox,
    QTableView,
    QTabWidget,
    QHBoxLayout,
    QHeaderView,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction

# Import from standalone test modules to avoid circular dependencies
from dataframe_store_test import DataFrameStore, EventType
from ui_adapter_test import DataFrameTableModel, EntryTableAdapter, CorrectionRuleTableAdapter


class StandaloneMainWindow(QMainWindow):
    """A standalone main window using the refactored components."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chest Tracker Correction Tool - Standalone Mode")
        self.setMinimumSize(1200, 800)

        # Set up central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create header
        self.header_label = QLabel("Chest Tracker Correction Tool - Refactored Version")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin: 10px;")
        self.layout.addWidget(self.header_label)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Create entries tab
        self.entries_tab = QWidget()
        self.entries_layout = QVBoxLayout(self.entries_tab)
        self.entries_table = QTableView()
        self.entries_layout.addWidget(self.entries_table)
        self.tab_widget.addTab(self.entries_tab, "Entries")

        # Create rules tab
        self.rules_tab = QWidget()
        self.rules_layout = QVBoxLayout(self.rules_tab)
        self.rules_table = QTableView()
        self.rules_layout.addWidget(self.rules_table)
        self.tab_widget.addTab(self.rules_tab, "Correction Rules")

        # Initialize data store and services
        self.initialize_services()

        # Create button row
        self.button_layout = QVBoxLayout()
        self.layout.addLayout(self.button_layout)

        # Add action buttons
        self.action_layout = QHBoxLayout()
        self.button_layout.addLayout(self.action_layout)

        # Load sample data button
        self.load_sample_button = QPushButton("Load Sample Data")
        self.load_sample_button.clicked.connect(self.load_sample_data)
        self.action_layout.addWidget(self.load_sample_button)

        # Load real data button
        self.load_real_button = QPushButton("Load Real Data")
        self.load_real_button.clicked.connect(self.load_real_data)
        self.action_layout.addWidget(self.load_real_button)

        # Load rules button
        self.load_rules_button = QPushButton("Load Correction Rules")
        self.load_rules_button.clicked.connect(self.load_sample_rules)
        self.action_layout.addWidget(self.load_rules_button)

        # Apply corrections button
        self.apply_button = QPushButton("Apply Corrections")
        self.apply_button.clicked.connect(self.apply_corrections)
        self.action_layout.addWidget(self.apply_button)

        # Validate button
        self.validate_button = QPushButton("Validate Entries")
        self.validate_button.clicked.connect(self.validate_entries)
        self.action_layout.addWidget(self.validate_button)

        # Save entries button
        self.save_button = QPushButton("Save Entries")
        self.save_button.clicked.connect(self.save_entries)
        self.action_layout.addWidget(self.save_button)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.button_layout.addWidget(self.status_label)

        # Set up the status bar
        self.statusBar().showMessage("Application initialized")

        # Create menu bar
        self.create_menu_bar()

        logger.info("StandaloneMainWindow initialized")

    def initialize_services(self):
        """Initialize the data store and services."""
        # Initialize DataFrameStore
        self.store = DataFrameStore()
        logger.info("DataFrameStore initialized")

        # Import service classes
        from integration_test import FileService, CorrectionService, ValidationService

        # Create services
        self.file_service = FileService(self.store)
        self.correction_service = CorrectionService(self.store)
        self.validation_service = ValidationService(self.store)
        logger.info("Services initialized")

        # Create UI adapters with the correct parameters
        self.entry_adapter = EntryTableAdapter(self.entries_table, self.store)
        self.rule_adapter = CorrectionRuleTableAdapter(self.rules_table, self.store)
        logger.info("UI adapters initialized")

        # Set up event handling
        self.store.subscribe(EventType.ENTRIES_UPDATED, self.on_entries_updated)
        self.store.subscribe(EventType.CORRECTION_RULES_UPDATED, self.on_rules_updated)
        self.store.subscribe(EventType.CORRECTION_APPLIED, self.on_correction_applied)
        self.store.subscribe(EventType.VALIDATION_COMPLETED, self.on_validation_completed)
        self.store.subscribe(EventType.ERROR_OCCURRED, self.on_error_occurred)
        logger.info("Event handlers registered")

        # Set up validation lists
        self.create_validation_lists()

    def create_validation_lists(self):
        """Create default validation lists."""
        # Sample chest types
        chest_types = [
            "Bronze Chest",
            "Silver Chest",
            "Golden Chest",
            "Magical Chest",
            "Giant Chest",
            "Epic Chest",
            "Legendary Chest",
            "Mega Lightning Chest",
            "Royal Wild Chest",
            "Legendary King's Chest",
            "Overflowing Gold Crate",
            "Gold Crate",
            "Plentiful Gold Crate",
            "Crown Chest",
        ]
        self.store.set_validation_list("chest_types", chest_types)

        # Sample players
        players = [
            "Engelchen",
            "Sir Met",
            "Moony",
            "SkSk",
            "Rumby",
            "Player One",
            "Player Two",
            "Weirdo",
            "MasterBlaster",
        ]
        self.store.set_validation_list("players", players)

        # Sample sources
        sources = [
            "Challenge",
            "Battle",
            "Battle Pass",
            "Shop",
            "Tournament",
            "Quest",
            "War",
            "Special Event",
        ]
        self.store.set_validation_list("sources", sources)

        logger.info("Default validation lists created")

    def create_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        load_sample_action = QAction("Load Sample Data", self)
        load_sample_action.triggered.connect(self.load_sample_data)
        file_menu.addAction(load_sample_action)

        load_real_action = QAction("Load Real Data", self)
        load_real_action.triggered.connect(self.load_real_data)
        file_menu.addAction(load_real_action)

        file_menu.addSeparator()

        save_action = QAction("Save Entries", self)
        save_action.triggered.connect(self.save_entries)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Correction menu
        correction_menu = menu_bar.addMenu("&Corrections")

        load_rules_action = QAction("Load Correction Rules", self)
        load_rules_action.triggered.connect(self.load_sample_rules)
        correction_menu.addAction(load_rules_action)

        apply_action = QAction("Apply Corrections", self)
        apply_action.triggered.connect(self.apply_corrections)
        correction_menu.addAction(apply_action)

        # Validation menu
        validation_menu = menu_bar.addMenu("&Validation")

        validate_action = QAction("Validate Entries", self)
        validate_action.triggered.connect(self.validate_entries)
        validation_menu.addAction(validate_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def load_sample_data(self):
        """Load sample data from the sample_data.txt file."""
        try:
            loaded = self.file_service.load_entries_from_file("sample_data.txt")
            if loaded > 0:
                self.status_label.setText(f"Loaded {loaded} entries from sample data")
                self.statusBar().showMessage(f"Loaded {loaded} entries from sample data")
                # Auto-validate the entries
                self.validate_entries()
            else:
                self.status_label.setText("No entries loaded from sample data")
                self.statusBar().showMessage("No entries loaded from sample data")
        except Exception as e:
            self.show_error(f"Error loading sample data: {str(e)}")

    def load_real_data(self):
        """Load real data from the data/input folder."""
        try:
            data_dir = Path("data/input")
            if not data_dir.exists():
                self.show_error(f"Directory not found: {data_dir}")
                return

            # Find the most recent file
            files = list(data_dir.glob("*.txt"))
            if not files:
                self.show_error("No data files found in data/input")
                return

            # Sort by modification time (newest first)
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_file = files[0]

            loaded = self.file_service.load_entries_from_file(str(latest_file))
            if loaded > 0:
                self.status_label.setText(f"Loaded {loaded} entries from {latest_file.name}")
                self.statusBar().showMessage(f"Loaded {loaded} entries from {latest_file.name}")
                # Auto-validate the entries
                self.validate_entries()
            else:
                self.status_label.setText(f"No entries loaded from {latest_file.name}")
                self.statusBar().showMessage(f"No entries loaded from {latest_file.name}")
        except Exception as e:
            self.show_error(f"Error loading real data: {str(e)}")

    def load_sample_rules(self):
        """Load sample correction rules from the sample_rules.csv file."""
        try:
            loaded = self.file_service.load_correction_rules_from_file("sample_rules.csv")
            if loaded > 0:
                self.status_label.setText(f"Loaded {loaded} correction rules")
                self.statusBar().showMessage(f"Loaded {loaded} correction rules")
            else:
                self.status_label.setText("No correction rules loaded")
                self.statusBar().showMessage("No correction rules loaded")
        except Exception as e:
            self.show_error(f"Error loading correction rules: {str(e)}")

    def apply_corrections(self):
        """Apply corrections to the entries."""
        try:
            corrected = self.correction_service.apply_corrections()
            if corrected > 0:
                self.status_label.setText(f"Applied {corrected} corrections")
                self.statusBar().showMessage(f"Applied {corrected} corrections")
                # Auto-validate the entries
                self.validate_entries()
            else:
                self.status_label.setText("No corrections applied")
                self.statusBar().showMessage("No corrections applied")
        except Exception as e:
            self.show_error(f"Error applying corrections: {str(e)}")

    def validate_entries(self):
        """Validate the entries."""
        try:
            self.validation_service.validate_entries()
            # The status update will be handled by the on_validation_completed event handler
        except Exception as e:
            self.show_error(f"Error validating entries: {str(e)}")

    def save_entries(self):
        """Save the entries to a file."""
        try:
            output_dir = Path("data/output")
            if not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / "saved_entries.txt"
            saved = self.file_service.save_entries_to_file(str(output_file))
            if saved > 0:
                self.status_label.setText(f"Saved {saved} entries to {output_file}")
                self.statusBar().showMessage(f"Saved {saved} entries to {output_file}")
            else:
                self.status_label.setText("No entries saved")
                self.statusBar().showMessage("No entries saved")
        except Exception as e:
            self.show_error(f"Error saving entries: {str(e)}")

    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Chest Tracker Correction Tool",
            "Chest Tracker Correction Tool - Standalone Mode\n\n"
            "A tool for correcting and validating chest entries.\n\n"
            "This is the refactored version using the new data management system.",
        )

    def show_error(self, message):
        """Show an error message."""
        logger.error(message)
        self.status_label.setText(f"Error: {message}")
        self.statusBar().showMessage(f"Error: {message}")
        QMessageBox.critical(self, "Error", message)

    # Event handlers
    def on_entries_updated(self, data):
        """Handle entries updated event."""
        count = len(data.get("entries", []))
        logger.info(f"Entries updated: {count} entries")
        self.status_label.setText(f"Entries updated: {count} entries")
        self.statusBar().showMessage(f"Entries updated: {count} entries")

    def on_rules_updated(self, data):
        """Handle correction rules updated event."""
        count = len(data.get("rules", []))
        logger.info(f"Correction rules updated: {count} rules")
        self.status_label.setText(f"Correction rules updated: {count} rules")
        self.statusBar().showMessage(f"Correction rules updated: {count} rules")

    def on_correction_applied(self, data):
        """Handle correction applied event."""
        correction_count = data.get("correction_count", 0)
        entry_count = data.get("entry_count", 0)
        logger.info(f"Applied {correction_count} corrections to {entry_count} entries")
        self.status_label.setText(
            f"Applied {correction_count} corrections to {entry_count} entries"
        )
        self.statusBar().showMessage(
            f"Applied {correction_count} corrections to {entry_count} entries"
        )

    def on_validation_completed(self, data):
        """Handle validation completed event."""
        valid_count = data.get("valid_count", 0)
        invalid_count = data.get("invalid_count", 0)
        total_count = data.get("total_count", 0)
        logger.info(
            f"Validation completed: {valid_count} valid, {invalid_count} invalid, {total_count} total"
        )
        self.status_label.setText(
            f"Validation: {valid_count} valid, {invalid_count} invalid, {total_count} total"
        )
        self.statusBar().showMessage(f"Validation: {valid_count} valid, {invalid_count} invalid")

    def on_error_occurred(self, data):
        """Handle error occurred event."""
        error_message = data.get("message", "Unknown error")
        self.show_error(error_message)


if __name__ == "__main__":
    try:
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Chest Tracker Correction Tool")
        app.setOrganizationName("ChestTracker")

        # Create and show main window
        main_window = StandaloneMainWindow()
        main_window.show()

        # Start event loop
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}", exc_info=True)
        # Show error in a message box if possible
        try:
            if QApplication.instance():
                QMessageBox.critical(None, "Error", f"Error starting application: {str(e)}")
        except:
            pass
        sys.exit(1)
