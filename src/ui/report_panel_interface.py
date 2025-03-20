"""
report_panel_interface.py

Description: Interface-based implementation of the Report Panel
Usage:
    from src.ui.report_panel_interface import ReportPanelInterface
    report_panel = ReportPanelInterface(service_factory)
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import logging

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QDateEdit,
    QTabWidget,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QRadioButton,
)
from PySide6.QtCore import QDate
from PySide6.QtGui import QFont, QTextDocument, QTextCursor

from src.interfaces import IServiceFactory, IConfigManager, IDataStore, IValidationService
from src.services.dataframe_store import EventType
from src.models.chest_entry import ChestEntry

# Import standardized EventType
from src.interfaces.events import EventType, EventHandler, EventData

from src.interfaces import (
    IServiceFactory,
    IDataStore,
    IFileService,
    IConfigManager,
    ICorrectionService,
    IValidationService,
)


class ReportPanelInterface(QWidget):
    """
    Interface-based implementation of the Report Panel.

    Provides controls for generating reports on chest entries, corrections,
    and validation results using dependency injection for services.

    Attributes:
        report_generated (Signal): Signal emitted when a report is generated

    Implementation Notes:
        - Uses dependency injection for services
        - Supports different report types
        - Can export reports to files
        - Uses tabbed interface for different report views
    """

    report_generated = Signal(str)  # Report type

    def __init__(self, service_factory: IServiceFactory, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the report panel with dependency injection.

        Args:
            service_factory (IServiceFactory): Factory for obtaining services
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)

        # Store service factory
        self._service_factory = service_factory

        # Get required services
        self._config_manager: IConfigManager = service_factory.get_service(IConfigManager)
        self._data_store: IDataStore = service_factory.get_service(IDataStore)

        # Initialize data
        self._entries: List[ChestEntry] = []
        self._entries_df = None

        # Signal processing flag to prevent recursion
        self._processing_signal = False

        # Setup UI
        self._setup_ui()

        # Connect signals from data store
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(10, 10, 10, 10)
        self._main_layout.setSpacing(10)

        # Report options group
        options_group = QGroupBox("Report Options")
        options_layout = QFormLayout(options_group)

        # Report type selection
        self._report_type_combo = QComboBox()
        self._report_type_combo.addItem("Summary Report", "summary")
        self._report_type_combo.addItem("Corrections Report", "corrections")
        self._report_type_combo.addItem("Validation Report", "validation")
        self._report_type_combo.addItem("Player Stats", "player_stats")
        self._report_type_combo.addItem("Chest Types", "chest_types")
        self._report_type_combo.addItem("Sources", "sources")
        self._report_type_combo.currentIndexChanged.connect(self._update_options)
        options_layout.addRow("Report Type:", self._report_type_combo)

        # Date range
        date_range_layout = QHBoxLayout()

        # From date
        self._from_date = QDateEdit()
        self._from_date.setDate(QDate.currentDate().addDays(-30))  # Last 30 days
        self._from_date.setCalendarPopup(True)
        date_range_layout.addWidget(self._from_date)

        # To date
        date_range_layout.addWidget(QLabel("to"))
        self._to_date = QDateEdit()
        self._to_date.setDate(QDate.currentDate())  # Today
        self._to_date.setCalendarPopup(True)
        date_range_layout.addWidget(self._to_date)

        options_layout.addRow("Date Range:", date_range_layout)

        # Include options
        self._include_corrections_checkbox = QCheckBox("Include corrections")
        self._include_corrections_checkbox.setChecked(True)
        options_layout.addRow("", self._include_corrections_checkbox)

        self._include_validation_checkbox = QCheckBox("Include validation results")
        self._include_validation_checkbox.setChecked(True)
        options_layout.addRow("", self._include_validation_checkbox)

        # Export format
        self._export_format_combo = QComboBox()
        self._export_format_combo.addItem("Text File (.txt)", "txt")
        self._export_format_combo.addItem("CSV File (.csv)", "csv")
        self._export_format_combo.addItem("HTML File (.html)", "html")
        options_layout.addRow("Export Format:", self._export_format_combo)

        # Add to main layout
        self._main_layout.addWidget(options_group)

        # Actions layout
        actions_layout = QHBoxLayout()

        # Generate button
        self._generate_button = QPushButton("Generate Report")
        self._generate_button.clicked.connect(self._generate_report)
        actions_layout.addWidget(self._generate_button)

        # Export button
        self._export_button = QPushButton("Export Report")
        self._export_button.clicked.connect(self._export_report)
        self._export_button.setEnabled(False)  # Disabled until a report is generated
        actions_layout.addWidget(self._export_button)

        # Add to main layout
        self._main_layout.addLayout(actions_layout)

        # Report tabs
        self._report_tabs = QTabWidget()

        # Text report tab
        self._text_report_tab = QWidget()
        text_report_layout = QVBoxLayout(self._text_report_tab)
        self._text_report = QTextEdit()
        self._text_report.setReadOnly(True)
        text_report_layout.addWidget(self._text_report)
        self._report_tabs.addTab(self._text_report_tab, "Text Report")

        # Table report tab
        self._table_report_tab = QWidget()
        table_report_layout = QVBoxLayout(self._table_report_tab)
        self._table_report = QTableWidget()
        table_report_layout.addWidget(self._table_report)
        self._report_tabs.addTab(self._table_report_tab, "Table Report")

        # Add tabs to main layout
        self._main_layout.addWidget(self._report_tabs)

    def _connect_signals(self) -> None:
        """Connect signals from data store and services."""
        # Connect to data store entry changes
        self._data_store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_changed)

        # We'll get validation list updates from DataFrameStore instead
        self._data_store.subscribe(
            EventType.VALIDATION_LISTS_UPDATED, self._on_validation_lists_updated
        )

    @Slot()
    def _update_options(self) -> None:
        """Update options based on the selected report type."""
        report_type = self._report_type_combo.currentData()

        # Enable/disable date range based on report type
        date_range_enabled = report_type in ["summary", "corrections", "validation"]
        self._from_date.setEnabled(date_range_enabled)
        self._to_date.setEnabled(date_range_enabled)

        # Enable/disable include options based on report type
        corrections_enabled = report_type in ["summary", "player_stats", "chest_types", "sources"]
        validation_enabled = report_type in ["summary", "player_stats", "chest_types", "sources"]

        self._include_corrections_checkbox.setEnabled(corrections_enabled)
        self._include_validation_checkbox.setEnabled(validation_enabled)

    @Slot(object)
    def _on_entries_changed(self, entries_df) -> None:
        """
        Handle entries changed event from data store.

        Args:
            entries_df: DataFrame containing entries
        """
        # Clear any existing report
        self._text_report.clear()
        self._table_report.clear()
        self._export_button.setEnabled(False)

        # Convert DataFrame entries to ChestEntry objects
        if entries_df is not None and not entries_df.empty:
            # This would typically be handled by a proper adapter
            # For now, just storing the dataframe
            self._entries_df = entries_df
            logging.info(f"ReportPanelInterface: Received {len(entries_df)} entries")
        else:
            self._entries_df = None
            logging.info("ReportPanelInterface: Received empty entries dataframe")

    @Slot(dict)
    def _on_validation_lists_updated(self, validation_lists) -> None:
        """
        Handle validation lists updated event.

        Args:
            validation_lists: Dictionary of validation lists
        """
        # Signal loop protection
        if hasattr(self, "_processing_signal") and self._processing_signal:
            logging.warning(
                "ReportPanelInterface: Signal loop detected in _on_validation_lists_updated"
            )
            return

        if not validation_lists:
            logging.warning("ReportPanelInterface: Empty validation lists received")
            return

        try:
            self._processing_signal = True
            logging.info(f"ReportPanelInterface: Received validation lists update")

            # Store validation lists for report generation
            self._validation_lists = validation_lists
        except Exception as e:
            logging.error(f"ReportPanelInterface: Error in _on_validation_lists_updated: {e}")
        finally:
            self._processing_signal = False

    @Slot()
    def _generate_report(self) -> None:
        """Generate a report based on the current entries."""
        if self._entries_df is None or self._entries_df.empty:
            QMessageBox.warning(
                self,
                "No Data",
                "No entries available for generating a report. Please load entries first.",
            )
            return

        try:
            report_type = self._report_type_combo.currentData()

            # Generate appropriate report based on type
            if report_type == "summary":
                self._generate_summary_report()
            elif report_type == "corrections":
                self._generate_corrections_report()
            elif report_type == "validation":
                self._generate_validation_report()
            elif report_type == "player_stats":
                self._generate_player_stats_report()
            elif report_type == "chest_types":
                self._generate_chest_types_report()
            elif report_type == "sources":
                self._generate_sources_report()
            else:
                logging.error(f"Unknown report type: {report_type}")
                return

            # Enable export button
            self._export_button.setEnabled(True)

            # Emit signal indicating report was generated
            self.report_generated.emit(report_type)

        except Exception as e:
            logging.error(f"Error generating report: {e}")
            QMessageBox.critical(
                self,
                "Report Generation Error",
                f"An error occurred while generating the report: {str(e)}",
            )

    def _generate_summary_report(self) -> None:
        """Generate a summary report."""
        if self._entries_df is None or self._entries_df.empty:
            return

        # Clear existing report content
        self._text_report.clear()

        # Prepare report text
        report_text = []
        report_text.append("# Chest Tracker Summary Report")
        report_text.append("")
        report_text.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_text.append("")
        report_text.append(f"Total entries: {len(self._entries_df)}")

        # Count unique players
        if "player" in self._entries_df.columns:
            unique_players = self._entries_df["player"].nunique()
            report_text.append(f"Unique players: {unique_players}")

        # Count unique chest types
        if "chest_type" in self._entries_df.columns:
            unique_chest_types = self._entries_df["chest_type"].nunique()
            report_text.append(f"Unique chest types: {unique_chest_types}")

        # Count unique sources
        if "source" in self._entries_df.columns:
            unique_sources = self._entries_df["source"].nunique()
            report_text.append(f"Unique sources: {unique_sources}")

        # Add to text report
        self._text_report.setPlainText("\n".join(report_text))

        # Populate table report
        self._populate_summary_table()

    def _populate_summary_table(self) -> None:
        """Populate the table with summary data."""
        if self._entries_df is None or self._entries_df.empty:
            return

        # Clear existing table
        self._table_report.clear()
        self._table_report.setRowCount(0)
        self._table_report.setColumnCount(3)

        # Set headers
        self._table_report.setHorizontalHeaderLabels(["Category", "Count", "Percentage"])

        # Add chest types summary
        if "chest_type" in self._entries_df.columns:
            chest_types = self._entries_df["chest_type"].value_counts()
            total_entries = len(self._entries_df)

            # Add rows for each chest type
            for i, (chest_type, count) in enumerate(chest_types.items()):
                self._table_report.insertRow(i)
                percentage = (count / total_entries) * 100

                # Add items to table
                self._table_report.setItem(i, 0, QTableWidgetItem(str(chest_type)))
                self._table_report.setItem(i, 1, QTableWidgetItem(str(count)))
                self._table_report.setItem(i, 2, QTableWidgetItem(f"{percentage:.2f}%"))

        # Resize columns to content
        self._table_report.resizeColumnsToContents()

    def _generate_player_stats_report(self) -> None:
        """Generate a player statistics report."""
        if self._entries_df is None or self._entries_df.empty:
            return

        # Clear existing report content
        self._text_report.clear()

        # Prepare report text
        report_text = []
        report_text.append("# Player Statistics Report")
        report_text.append("")
        report_text.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_text.append("")

        # Count chests by player
        if "player" in self._entries_df.columns:
            player_counts = self._entries_df["player"].value_counts()
            report_text.append(f"## Player Chest Counts")
            report_text.append("")

            for player, count in player_counts.items():
                report_text.append(f"{player}: {count} chests")

        # Add to text report
        self._text_report.setPlainText("\n".join(report_text))

        # Populate table report
        self._populate_player_stats_table()

    def _populate_player_stats_table(self) -> None:
        """Populate the table with player statistics."""
        if self._entries_df is None or self._entries_df.empty:
            return

        # Clear existing table
        self._table_report.clear()
        self._table_report.setRowCount(0)
        self._table_report.setColumnCount(2)

        # Set headers
        self._table_report.setHorizontalHeaderLabels(["Player", "Chest Count"])

        # Add player statistics
        if "player" in self._entries_df.columns:
            player_counts = self._entries_df["player"].value_counts()

            # Add rows for each player
            for i, (player, count) in enumerate(player_counts.items()):
                self._table_report.insertRow(i)

                # Add items to table
                self._table_report.setItem(i, 0, QTableWidgetItem(str(player)))
                self._table_report.setItem(i, 1, QTableWidgetItem(str(count)))

        # Resize columns to content
        self._table_report.resizeColumnsToContents()

    # Other report generation methods would be implemented similarly
    def _generate_corrections_report(self) -> None:
        """Generate a corrections report."""
        # Placeholder for corrections report
        self._text_report.setPlainText("Corrections report functionality coming soon...")

    def _generate_validation_report(self) -> None:
        """Generate a validation report."""
        # Placeholder for validation report
        self._text_report.setPlainText("Validation report functionality coming soon...")

    def _generate_chest_types_report(self) -> None:
        """Generate a chest types report."""
        # Placeholder for chest types report
        self._text_report.setPlainText("Chest types report functionality coming soon...")

    def _generate_sources_report(self) -> None:
        """Generate a sources report."""
        # Placeholder for sources report
        self._text_report.setPlainText("Sources report functionality coming soon...")

    @Slot()
    def _export_report(self) -> None:
        """Export the generated report to a file."""
        if self._text_report.toPlainText().strip() == "":
            QMessageBox.warning(
                self, "No Report", "No report to export. Please generate a report first."
            )
            return

        try:
            # Get export format
            export_format = self._export_format_combo.currentData()

            # Determine file extension and filter
            if export_format == "txt":
                file_ext = "Text Files (*.txt)"
                default_suffix = ".txt"
            elif export_format == "csv":
                file_ext = "CSV Files (*.csv)"
                default_suffix = ".csv"
            elif export_format == "html":
                file_ext = "HTML Files (*.html)"
                default_suffix = ".html"
            else:
                file_ext = "All Files (*.*)"
                default_suffix = ""

            # Get report type for filename suggestion
            report_type = self._report_type_combo.currentData()

            # Suggest filename based on report type and date
            date_str = datetime.now().strftime("%Y%m%d")
            suggested_name = f"report_{report_type}_{date_str}{default_suffix}"

            # Get path from config if available
            report_dir = self._config_manager.get_path("reports_directory", Path.cwd())

            # Ensure directory exists
            report_dir.mkdir(parents=True, exist_ok=True)

            # Get save filename from dialog
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Export Report", str(report_dir / suggested_name), file_ext
            )

            if not file_name:
                return  # User cancelled

            # Save the path for future use
            self._config_manager.set_path("reports_directory", Path(file_name).parent)

            # Export based on format
            if export_format == "txt":
                self._export_text_report(file_name)
            elif export_format == "csv":
                self._export_csv_report(file_name)
            elif export_format == "html":
                self._export_html_report(file_name)
            else:
                self._export_text_report(file_name)

            # Show success message
            QMessageBox.information(
                self, "Export Successful", f"Report successfully exported to {file_name}"
            )

        except Exception as e:
            logging.error(f"Error exporting report: {e}")
            QMessageBox.critical(
                self, "Export Error", f"An error occurred while exporting the report: {str(e)}"
            )

    def _export_text_report(self, file_name: str) -> None:
        """
        Export the report as a text file.

        Args:
            file_name (str): Path to save the file
        """
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self._text_report.toPlainText())

    def _export_csv_report(self, file_name: str) -> None:
        """
        Export the report as a CSV file.

        Args:
            file_name (str): Path to save the file
        """
        # This is a simplified version - in a real implementation,
        # we would convert the table data to CSV
        with open(file_name, "w", encoding="utf-8") as f:
            # Write header
            headers = []
            for col in range(self._table_report.columnCount()):
                header = self._table_report.horizontalHeaderItem(col)
                headers.append(header.text() if header else f"Column {col}")
            f.write(",".join(headers) + "\n")

            # Write data
            for row in range(self._table_report.rowCount()):
                row_data = []
                for col in range(self._table_report.columnCount()):
                    item = self._table_report.item(row, col)
                    row_data.append(item.text() if item else "")
                f.write(",".join(row_data) + "\n")

    def _export_html_report(self, file_name: str) -> None:
        """
        Export the report as an HTML file.

        Args:
            file_name (str): Path to save the file
        """
        # Convert plain text to HTML
        text = self._text_report.toPlainText()

        # Basic HTML conversion (could be more sophisticated)
        html_parts = ["<!DOCTYPE html>\n<html>\n<head>\n<title>Chest Tracker Report</title>\n"]
        html_parts.append("<style>\n")
        html_parts.append("body { font-family: Arial, sans-serif; margin: 40px; }\n")
        html_parts.append("h1, h2 { color: #333; }\n")
        html_parts.append("table { border-collapse: collapse; width: 100%; }\n")
        html_parts.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n")
        html_parts.append("th { background-color: #f2f2f2; }\n")
        html_parts.append("</style>\n</head>\n<body>\n")

        # Convert markdown-like headers
        for line in text.split("\n"):
            if line.startswith("# "):
                html_parts.append(f"<h1>{line[2:]}</h1>\n")
            elif line.startswith("## "):
                html_parts.append(f"<h2>{line[3:]}</h2>\n")
            elif line.strip() == "":
                html_parts.append("<p></p>\n")
            else:
                html_parts.append(f"<p>{line}</p>\n")

        # Add table if available
        if self._table_report.rowCount() > 0 and self._table_report.columnCount() > 0:
            html_parts.append("<h2>Tabular Data</h2>\n")
            html_parts.append("<table>\n<tr>\n")

            # Add headers
            for col in range(self._table_report.columnCount()):
                header = self._table_report.horizontalHeaderItem(col)
                header_text = header.text() if header else f"Column {col}"
                html_parts.append(f"<th>{header_text}</th>\n")
            html_parts.append("</tr>\n")

            # Add rows
            for row in range(self._table_report.rowCount()):
                html_parts.append("<tr>\n")
                for col in range(self._table_report.columnCount()):
                    item = self._table_report.item(row, col)
                    cell_text = item.text() if item else ""
                    html_parts.append(f"<td>{cell_text}</td>\n")
                html_parts.append("</tr>\n")

            html_parts.append("</table>\n")

        html_parts.append("</body>\n</html>")

        # Write to file
        with open(file_name, "w", encoding="utf-8") as f:
            f.write("".join(html_parts))
