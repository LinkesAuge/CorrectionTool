"""
report_panel.py

Description: Panel for generating and displaying reports
Usage:
    from src.ui.report_panel import ReportPanel
    report_panel = ReportPanel(parent=self)
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QTextEdit,
    QDateEdit, QTabWidget, QScrollArea, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import QDate
from PySide6.QtGui import QFont, QTextDocument, QTextCursor

from src.models.chest_entry import ChestEntry
from src.models.validation_list import ValidationList
from src.services.config_manager import ConfigManager


class ReportPanel(QWidget):
    """
    Panel for generating and displaying reports.
    
    Provides controls for generating reports on chest entries, corrections,
    and validation results.
    
    Attributes:
        report_generated (Signal): Signal emitted when a report is generated
        
    Implementation Notes:
        - Supports different report types
        - Can export reports to files
        - Uses tabbed interface for different report views
    """
    
    report_generated = Signal(str)  # Report type
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the report panel.
        
        Args:
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        
        # Initialize data
        self._config = ConfigManager()
        self._entries: List[ChestEntry] = []
        self._validation_lists: Dict[str, ValidationList] = {}
        
        # Setup UI
        self._setup_ui()
    
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
    
    @Slot(list)
    def set_entries(self, entries: List[ChestEntry]) -> None:
        """
        Set entries for reporting.
        
        Args:
            entries (List[ChestEntry]): The entries to report on
        """
        self._entries = entries
        self._export_button.setEnabled(False)  # Reset export button
    
    def set_validation_lists(self, validation_lists: Dict[str, ValidationList]) -> None:
        """
        Set the validation lists.
        
        Args:
            validation_lists (Dict[str, ValidationList]): The validation lists
        """
        self._validation_lists = validation_lists
    
    @Slot()
    def _generate_report(self) -> None:
        """Generate the selected report."""
        if not self._entries:
            self._text_report.setPlainText("No entries available for reporting.")
            return
        
        # Get report type
        report_type = self._report_type_combo.currentData()
        
        # Generate the appropriate report
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
        
        # Enable export button
        self._export_button.setEnabled(True)
        
        # Emit signal
        self.report_generated.emit(report_type)
    
    def _generate_summary_report(self) -> None:
        """Generate a summary report."""
        # Clear existing report
        self._text_report.clear()
        
        # Statistics
        total_entries = len(self._entries)
        corrected_entries = sum(1 for entry in self._entries if entry.has_corrections())
        validation_errors = sum(1 for entry in self._entries if entry.has_validation_errors())
        valid_entries = total_entries - corrected_entries - validation_errors
        
        # Count corrections by type
        correction_counts = {}
        for entry in self._entries:
            for field, _, _ in entry.corrections:
                if field not in correction_counts:
                    correction_counts[field] = 0
                correction_counts[field] += 1
        
        # Build report
        report = "# Summary Report\n\n"
        report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"## Entry Statistics\n\n"
        report += f"- Total entries: {total_entries}\n"
        report += f"- Valid entries: {valid_entries}\n"
        report += f"- Corrected entries: {corrected_entries}\n"
        report += f"- Entries with validation errors: {validation_errors}\n\n"
        
        report += f"## Correction Statistics\n\n"
        for field, count in correction_counts.items():
            report += f"- {field.capitalize()} corrections: {count}\n"
        
        report += f"\n## Validation List Statistics\n\n"
        for list_type, validation_list in self._validation_lists.items():
            report += f"- {list_type.capitalize()} list entries: {validation_list.count()}\n"
        
        # Set report text
        self._text_report.setPlainText(report)
        
        # Update table report
        self._table_report.clear()
        self._table_report.setRowCount(0)
        self._table_report.setColumnCount(2)
        self._table_report.setHorizontalHeaderLabels(["Statistic", "Value"])
        
        # Add rows
        self._add_table_row("Total entries", str(total_entries))
        self._add_table_row("Valid entries", str(valid_entries))
        self._add_table_row("Corrected entries", str(corrected_entries))
        self._add_table_row("Entries with validation errors", str(validation_errors))
        
        for field, count in correction_counts.items():
            self._add_table_row(f"{field.capitalize()} corrections", str(count))
        
        for list_type, validation_list in self._validation_lists.items():
            self._add_table_row(f"{list_type.capitalize()} list entries", str(validation_list.count()))
        
        # Resize columns to content
        self._table_report.resizeColumnsToContents()
    
    def _generate_corrections_report(self) -> None:
        """Generate a corrections report."""
        # Clear existing report
        self._text_report.clear()
        
        # Get corrected entries
        corrected_entries = [entry for entry in self._entries if entry.has_corrections()]
        
        # Build report
        report = "# Corrections Report\n\n"
        report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"Total corrected entries: {len(corrected_entries)}\n\n"
        
        # Update table report
        self._table_report.clear()
        self._table_report.setRowCount(0)
        self._table_report.setColumnCount(4)
        self._table_report.setHorizontalHeaderLabels(["Field", "Original", "Corrected", "Entry"])
        
        if not corrected_entries:
            report += "No corrections found.\n"
            self._text_report.setPlainText(report)
            return
        
        for i, entry in enumerate(corrected_entries):
            report += f"## Entry {i+1}\n\n"
            
            # Original entry
            report += f"Original:\n"
            if entry.original_chest_type:
                report += f"- Chest Type: {entry.original_chest_type}\n"
            if entry.original_player:
                report += f"- Player: {entry.original_player}\n"
            if entry.original_source:
                report += f"- Source: {entry.original_source}\n"
            
            # Corrected entry
            report += f"\nCorrected:\n"
            report += f"- Chest Type: {entry.chest_type}\n"
            report += f"- Player: {entry.player}\n"
            report += f"- Source: {entry.source}\n"
            
            # Corrections
            report += f"\nCorrections:\n"
            for field, from_val, to_val in entry.corrections:
                report += f"- {field.capitalize()}: {from_val} -> {to_val}\n"
                
                # Add to table
                self._add_table_row(
                    field.capitalize(),
                    from_val,
                    to_val,
                    f"{entry.chest_type} / {entry.player} / {entry.source}"
                )
            
            report += "\n" + "-" * 40 + "\n\n"
        
        # Set report text
        self._text_report.setPlainText(report)
        
        # Resize columns to content
        self._table_report.resizeColumnsToContents()
    
    def _generate_validation_report(self) -> None:
        """Generate a validation report."""
        # Clear existing report
        self._text_report.clear()
        
        # Get entries with validation errors
        invalid_entries = [entry for entry in self._entries if entry.has_validation_errors()]
        
        # Build report
        report = "# Validation Report\n\n"
        report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"Total entries with validation errors: {len(invalid_entries)}\n\n"
        
        # Update table report
        self._table_report.clear()
        self._table_report.setRowCount(0)
        self._table_report.setColumnCount(3)
        self._table_report.setHorizontalHeaderLabels(["Entry", "Validation Errors", "Corrections"])
        
        if not invalid_entries:
            report += "No validation errors found.\n"
            self._text_report.setPlainText(report)
            return
        
        for i, entry in enumerate(invalid_entries):
            report += f"## Entry {i+1}\n\n"
            
            # Entry details
            report += f"Chest Type: {entry.chest_type}\n"
            report += f"Player: {entry.player}\n"
            report += f"Source: {entry.source}\n\n"
            
            # Validation errors
            report += f"Validation Errors:\n"
            for error in entry.validation_errors:
                report += f"- {error}\n"
            
            # Has corrections?
            has_corrections = entry.has_corrections()
            report += f"\nHas corrections: {has_corrections}\n"
            
            if has_corrections:
                report += f"Corrections:\n"
                for field, from_val, to_val in entry.corrections:
                    report += f"- {field.capitalize()}: {from_val} -> {to_val}\n"
            
            # Add to table
            self._add_table_row(
                f"{entry.chest_type} / {entry.player} / {entry.source}",
                "\n".join(entry.validation_errors),
                "\n".join([f"{field}: {from_val} -> {to_val}" for field, from_val, to_val in entry.corrections]) if has_corrections else "None"
            )
            
            report += "\n" + "-" * 40 + "\n\n"
        
        # Set report text
        self._text_report.setPlainText(report)
        
        # Resize columns to content
        self._table_report.resizeColumnsToContents()
    
    def _generate_player_stats_report(self) -> None:
        """Generate a player statistics report."""
        # Clear existing report
        self._text_report.clear()
        
        # Count chests by player
        player_stats = {}
        for entry in self._entries:
            player = entry.player
            if player not in player_stats:
                player_stats[player] = {
                    "total": 0,
                    "corrected": 0,
                    "validation_errors": 0,
                    "chest_types": {},
                    "sources": {}
                }
            
            player_stats[player]["total"] += 1
            
            if entry.has_corrections():
                player_stats[player]["corrected"] += 1
            
            if entry.has_validation_errors():
                player_stats[player]["validation_errors"] += 1
            
            # Count chest types
            chest_type = entry.chest_type
            if chest_type not in player_stats[player]["chest_types"]:
                player_stats[player]["chest_types"][chest_type] = 0
            player_stats[player]["chest_types"][chest_type] += 1
            
            # Count sources
            source = entry.source
            if source not in player_stats[player]["sources"]:
                player_stats[player]["sources"][source] = 0
            player_stats[player]["sources"][source] += 1
        
        # Build report
        report = "# Player Statistics Report\n\n"
        report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"Total players: {len(player_stats)}\n\n"
        
        # Update table report
        self._table_report.clear()
        self._table_report.setRowCount(0)
        self._table_report.setColumnCount(4)
        self._table_report.setHorizontalHeaderLabels(["Player", "Total Chests", "Corrected", "Validation Errors"])
        
        if not player_stats:
            report += "No player data available.\n"
            self._text_report.setPlainText(report)
            return
        
        # Sort players by total chests
        sorted_players = sorted(
            player_stats.items(),
            key=lambda x: x[1]["total"],
            reverse=True
        )
        
        for player, stats in sorted_players:
            report += f"## {player}\n\n"
            report += f"- Total chests: {stats['total']}\n"
            report += f"- Corrected entries: {stats['corrected']}\n"
            report += f"- Entries with validation errors: {stats['validation_errors']}\n\n"
            
            # Add to table
            self._add_table_row(
                player,
                str(stats["total"]),
                str(stats["corrected"]),
                str(stats["validation_errors"])
            )
            
            # Most common chest types
            report += f"### Most Common Chest Types\n\n"
            sorted_chest_types = sorted(
                stats["chest_types"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for chest_type, count in sorted_chest_types[:5]:  # Top 5
                report += f"- {chest_type}: {count}\n"
            
            report += "\n"
            
            # Most common sources
            report += f"### Most Common Sources\n\n"
            sorted_sources = sorted(
                stats["sources"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for source, count in sorted_sources[:5]:  # Top 5
                report += f"- {source}: {count}\n"
            
            report += "\n" + "-" * 40 + "\n\n"
        
        # Set report text
        self._text_report.setPlainText(report)
        
        # Resize columns to content
        self._table_report.resizeColumnsToContents()
    
    def _generate_chest_types_report(self) -> None:
        """Generate a chest types report."""
        # Clear existing report
        self._text_report.clear()
        
        # Count entries by chest type
        chest_stats = {}
        for entry in self._entries:
            chest_type = entry.chest_type
            if chest_type not in chest_stats:
                chest_stats[chest_type] = {
                    "total": 0,
                    "corrected": 0,
                    "validation_errors": 0,
                    "players": {},
                    "sources": {}
                }
            
            chest_stats[chest_type]["total"] += 1
            
            if entry.has_corrections():
                chest_stats[chest_type]["corrected"] += 1
            
            if entry.has_validation_errors():
                chest_stats[chest_type]["validation_errors"] += 1
            
            # Count players
            player = entry.player
            if player not in chest_stats[chest_type]["players"]:
                chest_stats[chest_type]["players"][player] = 0
            chest_stats[chest_type]["players"][player] += 1
            
            # Count sources
            source = entry.source
            if source not in chest_stats[chest_type]["sources"]:
                chest_stats[chest_type]["sources"][source] = 0
            chest_stats[chest_type]["sources"][source] += 1
        
        # Build report
        report = "# Chest Types Report\n\n"
        report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"Total chest types: {len(chest_stats)}\n\n"
        
        # Update table report
        self._table_report.clear()
        self._table_report.setRowCount(0)
        self._table_report.setColumnCount(4)
        self._table_report.setHorizontalHeaderLabels(["Chest Type", "Total", "Corrected", "Validation Errors"])
        
        if not chest_stats:
            report += "No chest type data available.\n"
            self._text_report.setPlainText(report)
            return
        
        # Sort chest types by total
        sorted_chest_types = sorted(
            chest_stats.items(),
            key=lambda x: x[1]["total"],
            reverse=True
        )
        
        for chest_type, stats in sorted_chest_types:
            report += f"## {chest_type}\n\n"
            report += f"- Total entries: {stats['total']}\n"
            report += f"- Corrected entries: {stats['corrected']}\n"
            report += f"- Entries with validation errors: {stats['validation_errors']}\n\n"
            
            # Add to table
            self._add_table_row(
                chest_type,
                str(stats["total"]),
                str(stats["corrected"]),
                str(stats["validation_errors"])
            )
            
            # Most common players
            report += f"### Most Common Players\n\n"
            sorted_players = sorted(
                stats["players"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for player, count in sorted_players[:5]:  # Top 5
                report += f"- {player}: {count}\n"
            
            report += "\n"
            
            # Most common sources
            report += f"### Most Common Sources\n\n"
            sorted_sources = sorted(
                stats["sources"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for source, count in sorted_sources[:5]:  # Top 5
                report += f"- {source}: {count}\n"
            
            report += "\n" + "-" * 40 + "\n\n"
        
        # Set report text
        self._text_report.setPlainText(report)
        
        # Resize columns to content
        self._table_report.resizeColumnsToContents()
    
    def _generate_sources_report(self) -> None:
        """Generate a sources report."""
        # Clear existing report
        self._text_report.clear()
        
        # Count entries by source
        source_stats = {}
        for entry in self._entries:
            source = entry.source
            if source not in source_stats:
                source_stats[source] = {
                    "total": 0,
                    "corrected": 0,
                    "validation_errors": 0,
                    "players": {},
                    "chest_types": {}
                }
            
            source_stats[source]["total"] += 1
            
            if entry.has_corrections():
                source_stats[source]["corrected"] += 1
            
            if entry.has_validation_errors():
                source_stats[source]["validation_errors"] += 1
            
            # Count players
            player = entry.player
            if player not in source_stats[source]["players"]:
                source_stats[source]["players"][player] = 0
            source_stats[source]["players"][player] += 1
            
            # Count chest types
            chest_type = entry.chest_type
            if chest_type not in source_stats[source]["chest_types"]:
                source_stats[source]["chest_types"][chest_type] = 0
            source_stats[source]["chest_types"][chest_type] += 1
        
        # Build report
        report = "# Sources Report\n\n"
        report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"Total sources: {len(source_stats)}\n\n"
        
        # Update table report
        self._table_report.clear()
        self._table_report.setRowCount(0)
        self._table_report.setColumnCount(4)
        self._table_report.setHorizontalHeaderLabels(["Source", "Total", "Corrected", "Validation Errors"])
        
        if not source_stats:
            report += "No source data available.\n"
            self._text_report.setPlainText(report)
            return
        
        # Sort sources by total
        sorted_sources = sorted(
            source_stats.items(),
            key=lambda x: x[1]["total"],
            reverse=True
        )
        
        for source, stats in sorted_sources:
            report += f"## {source}\n\n"
            report += f"- Total entries: {stats['total']}\n"
            report += f"- Corrected entries: {stats['corrected']}\n"
            report += f"- Entries with validation errors: {stats['validation_errors']}\n\n"
            
            # Add to table
            self._add_table_row(
                source,
                str(stats["total"]),
                str(stats["corrected"]),
                str(stats["validation_errors"])
            )
            
            # Most common players
            report += f"### Most Common Players\n\n"
            sorted_players = sorted(
                stats["players"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for player, count in sorted_players[:5]:  # Top 5
                report += f"- {player}: {count}\n"
            
            report += "\n"
            
            # Most common chest types
            report += f"### Most Common Chest Types\n\n"
            sorted_chest_types = sorted(
                stats["chest_types"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for chest_type, count in sorted_chest_types[:5]:  # Top 5
                report += f"- {chest_type}: {count}\n"
            
            report += "\n" + "-" * 40 + "\n\n"
        
        # Set report text
        self._text_report.setPlainText(report)
        
        # Resize columns to content
        self._table_report.resizeColumnsToContents()
    
    def _add_table_row(self, *args) -> None:
        """
        Add a row to the table report.
        
        Args:
            *args: Column values for the row
        """
        row = self._table_report.rowCount()
        self._table_report.insertRow(row)
        
        for col, value in enumerate(args):
            item = QTableWidgetItem(value)
            self._table_report.setItem(row, col, item)
    
    @Slot()
    def _export_report(self) -> None:
        """Export the current report to a file."""
        # Get export format
        export_format = self._export_format_combo.currentData()
        
        # Get default output directory
        default_dir = self._config.get("Files", "default_output_dir", fallback="data/output")
        
        # Get report type
        report_type = self._report_type_combo.currentData()
        
        # Create default filename based on report type and date
        date_str = datetime.now().strftime("%Y-%m-%d")
        default_filename = f"{report_type}_report_{date_str}.{export_format}"
        
        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Report", str(Path(default_dir) / default_filename),
            f"Text Files (*.{export_format})"
        )
        
        if not file_path:
            return
        
        try:
            # Export based on format
            if export_format == "txt":
                with open(file_path, "w") as f:
                    f.write(self._text_report.toPlainText())
            elif export_format == "csv":
                self._export_as_csv(file_path)
            elif export_format == "html":
                with open(file_path, "w") as f:
                    f.write(self._text_report.toHtml())
            
            # Save the directory
            self._config.set("Files", "default_output_dir", str(Path(file_path).parent))
            self._config.save()
        except Exception as e:
            # Show error message
            print(f"Error exporting report: {e}")
    
    def _export_as_csv(self, file_path: str) -> None:
        """
        Export the current report as a CSV file.
        
        Args:
            file_path (str): Path to save the CSV file
        """
        import csv
        
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Write headers
            headers = []
            for col in range(self._table_report.columnCount()):
                headers.append(self._table_report.horizontalHeaderItem(col).text())
            writer.writerow(headers)
            
            # Write data
            for row in range(self._table_report.rowCount()):
                row_data = []
                for col in range(self._table_report.columnCount()):
                    item = self._table_report.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                writer.writerow(row_data) 