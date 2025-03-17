"""
help_panel.py

Description: Panel for displaying help content
Usage:
    from src.ui.help_panel import HelpPanel
    help_panel = HelpPanel(parent=self)
"""

from typing import Optional, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QTextBrowser,
)


class HelpPanel(QWidget):
    """
    Panel for displaying help content.

    Provides a tree-based navigation for help topics and content display.

    Attributes:
        _topics (Dict[str, QTreeWidgetItem]): Dictionary of topic items

    Implementation Notes:
        - Uses QTreeWidget for topic navigation
        - Uses QTextBrowser for content display
        - Uses QSplitter for adjustable layout
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the help panel.

        Args:
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)

        # Initialize attributes
        self._topics: Dict[str, QTreeWidgetItem] = {}

        # Initialize UI
        self._setup_ui()

        # Populate help content
        self._populate_help_content()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create splitter for topics and content
        self._splitter = QSplitter(Qt.Horizontal)

        # Topics tree
        self._topics_tree = QTreeWidget()
        self._topics_tree.setHeaderLabel("Help Topics")
        self._topics_tree.setMinimumWidth(200)
        self._topics_tree.setMaximumWidth(300)
        self._topics_tree.setIndentation(15)
        self._topics_tree.itemClicked.connect(self._on_topic_selected)

        # Content area
        self._content_area = QTextBrowser()
        self._content_area.setOpenExternalLinks(True)

        # Add widgets to splitter
        self._splitter.addWidget(self._topics_tree)
        self._splitter.addWidget(self._content_area)

        # Set initial splitter sizes (25/75 split)
        self._splitter.setSizes([200, 600])

        # Add splitter to layout
        layout.addWidget(self._splitter)

    def _populate_help_content(self) -> None:
        """Populate the help content with topics and content."""
        # Add main topics
        getting_started = self._add_topic("Getting Started", None)
        file_panel = self._add_topic("File Panel", None)
        validation = self._add_topic("Validation", None)
        corrector = self._add_topic("Corrector", None)
        reports = self._add_topic("Reports", None)
        settings = self._add_topic("Settings", None)

        # Add subtopics
        self._add_topic("Application Overview", getting_started)
        self._add_topic("User Interface", getting_started)

        self._add_topic("Loading Files", file_panel)
        self._add_topic("File Formats", file_panel)

        self._add_topic("Validation Lists", validation)
        self._add_topic("Managing Lists", validation)

        self._add_topic("Correction Rules", corrector)
        self._add_topic("Applying Corrections", corrector)
        self._add_topic("Filtering Entries", corrector)

        self._add_topic("Generating Reports", reports)
        self._add_topic("Exporting Reports", reports)

        self._add_topic("Application Settings", settings)

        # Expand top-level items
        self._topics_tree.expandAll()

        # Select first topic
        self._topics_tree.setCurrentItem(getting_started)
        self._show_topic_content("Getting Started")

    def _add_topic(self, name: str, parent: Optional[QTreeWidgetItem]) -> QTreeWidgetItem:
        """
        Add a topic to the tree.

        Args:
            name (str): Topic name
            parent (Optional[QTreeWidgetItem]): Parent topic or None for top-level

        Returns:
            QTreeWidgetItem: The created topic item
        """
        if parent is None:
            item = QTreeWidgetItem(self._topics_tree, [name])
        else:
            item = QTreeWidgetItem(parent, [name])

        # Store in topics dictionary for easy access
        self._topics[name] = item

        return item

    def _on_topic_selected(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handle topic selection.

        Args:
            item (QTreeWidgetItem): Selected topic item
            column (int): Selected column
        """
        topic_name = item.text(0)
        self._show_topic_content(topic_name)

    def _show_topic_content(self, topic_name: str) -> None:
        """
        Show content for a topic.

        Args:
            topic_name (str): Topic name
        """
        content = self._get_topic_content(topic_name)
        self._content_area.setHtml(content)

    def _get_topic_content(self, topic_name: str) -> str:
        """
        Get the HTML content for a topic.

        Args:
            topic_name (str): Topic name

        Returns:
            str: HTML content
        """
        # Base CSS for styling
        css = """
        <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 10px 20px;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            font-size: 24px;
        }
        h2 {
            color: #3498db;
            font-size: 20px;
            margin-top: 25px;
        }
        ul, ol {
            margin-bottom: 20px;
        }
        li {
            margin-bottom: 8px;
        }
        code {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 3px;
            font-family: monospace;
            padding: 2px 4px;
        }
        .tip {
            background-color: #e8f4fd;
            border-left: 4px solid #3498db;
            padding: 10px;
            margin: 15px 0;
        }
        .warning {
            background-color: #fff8e6;
            border-left: 4px solid #f39c12;
            padding: 10px;
            margin: 15px 0;
        }
        </style>
        """

        # Content for each topic
        if topic_name == "Getting Started":
            return (
                css
                + """
            <h1>Getting Started</h1>
            <p>Welcome to the Chest Tracker Correction Tool! This help section will guide you through the features and functionality of the application.</p>
            
            <h2>About This Tool</h2>
            <p>The Chest Tracker Correction Tool is designed to help validate and correct chest entries from video game data. It provides tools for:</p>
            <ul>
                <li>Loading chest entry data from various file formats</li>
                <li>Validating entries against known good values</li>
                <li>Correcting entries automatically or manually</li>
                <li>Generating reports and statistics</li>
                <li>Exporting corrected data</li>
            </ul>
            
            <h2>Main Features</h2>
            <ul>
                <li><strong>File Management</strong>: Import and export chest entry data</li>
                <li><strong>Validation</strong>: Create and manage validation lists for different fields</li>
                <li><strong>Correction</strong>: Apply automatic or manual corrections to entries</li>
                <li><strong>Reports</strong>: Generate and export reports on entries, corrections, and validation</li>
            </ul>
            
            <p class="tip">Tip: Start by loading a data file and creating validation lists for the data fields you want to check.</p>
            """
            )

        elif topic_name == "User Interface":
            return (
                css
                + """
            <h1>User Interface</h1>
            <p>The application is divided into several main areas:</p>
            
            <h2>Navigation Panel</h2>
            <p>The left sidebar contains navigation buttons for the main sections of the application:</p>
            <ul>
                <li><strong>Dashboard</strong>: Overview of the data and quick access to main functions</li>
                <li><strong>Correction Manager</strong>: Tools for managing corrections and validation</li>
                <li><strong>Reports</strong>: Generate reports and statistics</li>
                <li><strong>Settings</strong>: Configure application preferences</li>
                <li><strong>Help</strong>: Access this help documentation</li>
            </ul>
            
            <h2>Content Area</h2>
            <p>The main content area displays the active section:</p>
            <ul>
                <li><strong>Dashboard</strong>: Displays the file panel and corrector panel side by side</li>
                <li><strong>Correction Manager</strong>: Provides tools for validation list management</li>
                <li><strong>Reports</strong>: Shows statistics and allows report generation</li>
                <li><strong>Settings</strong>: Contains configuration options</li>
            </ul>
            
            <h2>Status Bar</h2>
            <p>The status bar at the bottom of the window shows:</p>
            <ul>
                <li>Current status of operations</li>
                <li>Count of loaded entries</li>
                <li>Count of corrected entries</li>
            </ul>
            
            <p class="tip">Tip: You can resize most panels by dragging the splitter bars between them.</p>
            """
            )

        elif topic_name == "File Panel":
            return (
                css
                + """
            <h1>File Panel</h1>
            <p>The File Panel is the primary interface for managing chest entry data files.</p>
            
            <h2>Main Functions</h2>
            <ul>
                <li>Import data from various file formats</li>
                <li>Export corrected data</li>
                <li>View basic statistics about the loaded data</li>
                <li>Filter entries by different criteria</li>
            </ul>
            
            <h2>Controls</h2>
            <ul>
                <li><strong>Import Button</strong>: Load data from a file</li>
                <li><strong>Export Button</strong>: Save corrected data to a file</li>
                <li><strong>Filter</strong>: Filter entries by type, player, or source</li>
                <li><strong>Statistics</strong>: View counts of total, valid, and corrected entries</li>
            </ul>
            
            <p class="tip">Tip: The File Panel appears in both the Dashboard and the File Management tab.</p>
            """
            )

        elif topic_name == "Loading Files":
            return (
                css
                + """
            <h1>Loading Files</h1>
            <p>You can load data from different file formats into the application.</p>
            
            <h2>Supported File Formats</h2>
            <ul>
                <li><strong>CSV (.csv)</strong>: Comma-separated values</li>
                <li><strong>Text (.txt)</strong>: Tab or comma-delimited text</li>
                <li><strong>JSON (.json)</strong>: JSON-formatted data</li>
            </ul>
            
            <h2>How to Load Files</h2>
            <ol>
                <li>Click the "Import" button in the File Panel</li>
                <li>Browse to the location of your data file</li>
                <li>Select the file and click "Open"</li>
                <li>If the file format is ambiguous, you may be prompted to select the format</li>
                <li>The data will be loaded and displayed in the table</li>
            </ol>
            
            <h2>File Format Requirements</h2>
            <p>The application expects the following columns in your data:</p>
            <ul>
                <li><strong>ID</strong>: Unique identifier for each entry</li>
                <li><strong>Name</strong>: The chest item name</li>
                <li><strong>Chest Type</strong>: The type of chest</li>
                <li><strong>Player</strong>: The player who found the chest</li>
                <li><strong>Source</strong>: The source or location of the chest</li>
            </ul>
            
            <p class="warning">Warning: If your file is missing required columns, the import may fail or data may be incomplete.</p>
            """
            )

        elif topic_name == "File Formats":
            return (
                css
                + """
            <h1>File Formats</h1>
            <p>The application supports several file formats for import and export.</p>
            
            <h2>CSV Format</h2>
            <p>CSV files should have a header row with column names, followed by data rows:</p>
            <code>
            ID,Name,ChestType,Player,Source<br>
            1,"Gold Coins","Common Chest","PlayerOne","Dungeon"<br>
            2,"Rare Sword","Rare Chest","PlayerTwo","Forest"
            </code>
            
            <h2>Text Format</h2>
            <p>Text files can be tab-delimited or comma-delimited:</p>
            <code>
            ID\tName\tChestType\tPlayer\tSource<br>
            1\tGold Coins\tCommon Chest\tPlayerOne\tDungeon<br>
            2\tRare Sword\tRare Chest\tPlayerTwo\tForest
            </code>
            
            <h2>JSON Format</h2>
            <p>JSON files should contain an array of objects with the required fields:</p>
            <code>
            [<br>
            &nbsp;&nbsp;{<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"ID": "1",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"Name": "Gold Coins",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"ChestType": "Common Chest",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"Player": "PlayerOne",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"Source": "Dungeon"<br>
            &nbsp;&nbsp;},<br>
            &nbsp;&nbsp;{<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"ID": "2",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"Name": "Rare Sword",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"ChestType": "Rare Chest",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"Player": "PlayerTwo",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"Source": "Forest"<br>
            &nbsp;&nbsp;}<br>
            ]
            </code>
            
            <h2>Export Formats</h2>
            <p>When exporting, you can choose the same formats as for import. The export will include any corrections that have been applied to the data.</p>
            
            <p class="tip">Tip: CSV is the most widely compatible format and is recommended for most uses.</p>
            """
            )

        elif topic_name == "Validation":
            return (
                css
                + """
            <h1>Validation</h1>
            <p>Validation helps ensure your chest entry data is consistent and accurate.</p>
            
            <h2>What Gets Validated</h2>
            <p>The application can validate several fields in your chest entries:</p>
            <ul>
                <li><strong>Chest Type</strong>: Ensures chest types match your defined list</li>
                <li><strong>Player</strong>: Validates player names against your player list</li>
                <li><strong>Source</strong>: Checks sources against your source list</li>
            </ul>
            
            <h2>Validation Process</h2>
            <ol>
                <li>Load or create validation lists for each field you want to validate</li>
                <li>Load your chest entry data</li>
                <li>Click "Apply Validation" to check entries against your lists</li>
                <li>Entries that don't match will be marked for correction</li>
                <li>You can apply automatic corrections or fix entries manually</li>
            </ol>
            
            <h2>Validation Modes</h2>
            <ul>
                <li><strong>Strict</strong>: Requires exact matches (case-sensitive)</li>
                <li><strong>Normal</strong>: Case-insensitive matching</li>
                <li><strong>Lenient</strong>: Enables fuzzy matching for close matches</li>
            </ul>
            
            <p class="tip">Tip: Start with a small set of known-good values in your validation lists and expand as needed.</p>
            """
            )

        elif topic_name == "Validation Lists":
            return (
                css
                + """
            <h1>Validation Lists</h1>
            <p>Validation lists contain the valid values for different fields in your data.</p>
            
            <h2>Types of Validation Lists</h2>
            <ul>
                <li><strong>Chest Type Lists</strong>: Valid chest types (e.g., Common, Rare, Epic, Legendary)</li>
                <li><strong>Player Lists</strong>: Valid player names</li>
                <li><strong>Source Lists</strong>: Valid sources or locations</li>
            </ul>
            
            <h2>Creating Validation Lists</h2>
            <p>You can create validation lists in several ways:</p>
            <ol>
                <li>Import from a text file with one value per line</li>
                <li>Add values manually in the Validation panel</li>
                <li>Extract unique values from your loaded data</li>
            </ol>
            
            <h2>Managing Lists</h2>
            <p>In the Validation panel, you can:</p>
            <ul>
                <li>Create new lists</li>
                <li>Edit existing lists</li>
                <li>Delete lists</li>
                <li>Export lists to files</li>
                <li>Enable or disable individual lists</li>
            </ul>
            
            <p class="warning">Warning: Changes to validation lists are not automatically saved. Use the export function to save your lists.</p>
            """
            )

        elif topic_name == "Managing Lists":
            return (
                css
                + """
            <h1>Managing Lists</h1>
            <p>The Validation panel provides tools for managing your validation lists.</p>
            
            <h2>Creating a New List</h2>
            <ol>
                <li>Go to the Validation tab</li>
                <li>Select the type of list (Chest Type, Player, or Source)</li>
                <li>Click "New List"</li>
                <li>Enter a name for the list</li>
                <li>Add entries using "Add Entry" or import from a file</li>
            </ol>
            
            <h2>Importing Lists</h2>
            <ol>
                <li>Click "Import List" in the Validation panel</li>
                <li>Browse to your list file (one value per line)</li>
                <li>Select the file and click "Open"</li>
                <li>Choose the list type if prompted</li>
            </ol>
            
            <h2>Exporting Lists</h2>
            <ol>
                <li>Select the list you want to export</li>
                <li>Click "Export List"</li>
                <li>Choose a location and filename</li>
                <li>Click "Save"</li>
            </ol>
            
            <h2>Enabling/Disabling Lists</h2>
            <p>Each list has a checkbox that enables or disables it for validation. Only enabled lists are used when validating entries.</p>
            
            <p class="tip">Tip: You can have multiple lists of the same type. This is useful for managing different sets of valid values.</p>
            """
            )

        elif topic_name == "Corrector":
            return (
                css
                + """
            <h1>Corrector</h1>
            <p>The Corrector panel allows you to view, filter, and correct chest entries.</p>
            
            <h2>Features</h2>
            <ul>
                <li>View all loaded entries in a sortable table</li>
                <li>Filter entries by various criteria</li>
                <li>Apply automatic corrections based on validation lists</li>
                <li>Make manual corrections to individual entries</li>
                <li>View correction statistics</li>
            </ul>
            
            <h2>Table View</h2>
            <p>The table displays all loaded entries with the following columns:</p>
            <ul>
                <li><strong>ID</strong>: Entry identifier</li>
                <li><strong>Name</strong>: Item name</li>
                <li><strong>Chest Type</strong>: Type of chest</li>
                <li><strong>Player</strong>: Player name</li>
                <li><strong>Source</strong>: Source or location</li>
                <li><strong>Status</strong>: Indicates if the entry is valid, corrected, or has errors</li>
            </ul>
            
            <h2>Correction Process</h2>
            <ol>
                <li>Load your chest entry data</li>
                <li>Load or create validation lists</li>
                <li>Apply validation to identify entries that need correction</li>
                <li>Use automatic correction or manually edit entries</li>
                <li>Review corrections</li>
                <li>Export the corrected data</li>
            </ol>
            
            <p class="tip">Tip: You can click on column headers to sort the table by that column.</p>
            """
            )

        elif topic_name == "Correction Rules":
            return (
                css
                + """
            <h1>Correction Rules</h1>
            <p>Correction rules determine how entries are corrected when they don't match validation lists.</p>
            
            <h2>Automatic Correction</h2>
            <p>When using automatic correction, the system:</p>
            <ol>
                <li>Compares each entry field to the validation lists</li>
                <li>For fields that don't match, tries to find the closest valid value</li>
                <li>Applies corrections if a match is found above the threshold</li>
                <li>Marks entries that couldn't be corrected automatically</li>
            </ol>
            
            <h2>Matching Methods</h2>
            <p>The application uses several methods to match values:</p>
            <ul>
                <li><strong>Exact Match</strong>: The value exactly matches a valid value</li>
                <li><strong>Case-Insensitive Match</strong>: The value matches when ignoring case</li>
                <li><strong>Fuzzy Match</strong>: The value is similar to a valid value (based on edit distance)</li>
            </ul>
            
            <h2>Fuzzy Matching</h2>
            <p>Fuzzy matching uses algorithms to find similar strings:</p>
            <ul>
                <li>Compares strings based on how many characters need to be changed</li>
                <li>Uses a threshold to determine if a match is close enough</li>
                <li>Higher thresholds require closer matches</li>
                <li>You can adjust the threshold in settings</li>
            </ul>
            
            <p class="warning">Warning: Fuzzy matching may suggest incorrect values if the threshold is too low or if valid values are too similar.</p>
            """
            )

        elif topic_name == "Applying Corrections":
            return (
                css
                + """
            <h1>Applying Corrections</h1>
            <p>You can apply corrections to entries in several ways.</p>
            
            <h2>Automatic Correction</h2>
            <ol>
                <li>Load your data and validation lists</li>
                <li>Click "Auto-Correct All" in the Corrector panel</li>
                <li>The system will attempt to correct all entries based on validation lists</li>
                <li>Entries that can be corrected will show their new values</li>
                <li>Entries that can't be corrected will be marked with errors</li>
            </ol>
            
            <h2>Manual Correction</h2>
            <ol>
                <li>Select an entry in the table</li>
                <li>The entry details will appear in the side panel</li>
                <li>Edit the values as needed</li>
                <li>Click "Apply Changes" to save the corrections</li>
            </ol>
            
            <h2>Exporting Corrections</h2>
            <ol>
                <li>After applying corrections, click "Export Corrected" in the Corrector panel</li>
                <li>Choose a location and format for the exported file</li>
                <li>The exported file will contain all entries with corrections applied</li>
            </ol>
            
            <p class="tip">Tip: You can use filters to focus on entries that need correction.</p>
            """
            )

        elif topic_name == "Filtering Entries":
            return (
                css
                + """
            <h1>Filtering Entries</h1>
            <p>The Corrector panel provides several filtering options to help you focus on specific entries.</p>
            
            <h2>Filter Controls</h2>
            <ul>
                <li><strong>Type Filter</strong>: Filter by chest type</li>
                <li><strong>Player Filter</strong>: Filter by player name</li>
                <li><strong>Source Filter</strong>: Filter by source or location</li>
                <li><strong>Search Filter</strong>: Filter by text in any field</li>
            </ul>
            
            <h2>Using Filters</h2>
            <p>To filter entries:</p>
            <ol>
                <li>Select a value from the drop-down filter or enter text in the search box</li>
                <li>The table will update to show only matching entries</li>
                <li>Multiple filters can be combined (all conditions must match)</li>
                <li>Clear filters to return to the full entry list</li>
            </ol>
            
            <h2>Filter by Status</h2>
            <p>You can also filter entries by their validation status:</p>
            <ul>
                <li><strong>All</strong>: Show all entries</li>
                <li><strong>Valid</strong>: Show only entries that pass validation</li>
                <li><strong>Corrected</strong>: Show only entries that have been corrected</li>
                <li><strong>Error</strong>: Show only entries that failed validation and couldn't be corrected</li>
            </ul>
            
            <p class="tip">Tip: Filtering is useful when working with large datasets to focus on specific subsets of entries.</p>
            """
            )

        elif topic_name == "Reports":
            return (
                css
                + """
            <h1>Reports</h1>
            <p>The Reports panel allows you to generate statistics and reports about your chest entries.</p>
            
            <h2>Available Reports</h2>
            <ul>
                <li><strong>Summary Report</strong>: Overview of all entries, corrections, and issues</li>
                <li><strong>Correction Report</strong>: Detailed list of all corrections made</li>
                <li><strong>Validation Report</strong>: Analysis of validation errors and issues</li>
                <li><strong>Player Report</strong>: Statistics broken down by player</li>
                <li><strong>Chest Type Report</strong>: Statistics broken down by chest type</li>
                <li><strong>Source Report</strong>: Statistics broken down by source</li>
            </ul>
            
            <h2>Generating Reports</h2>
            <ol>
                <li>Go to the Reports tab</li>
                <li>Select the type of report you want to generate</li>
                <li>Click "Generate Report"</li>
                <li>The report will be displayed in the panel</li>
                <li>You can export the report to a file if needed</li>
            </ol>
            
            <h2>Report Visualizations</h2>
            <p>Some reports include visualizations such as:</p>
            <ul>
                <li>Bar charts showing distributions</li>
                <li>Pie charts showing proportions</li>
                <li>Tables with statistics</li>
            </ul>
            
            <p class="tip">Tip: Reports are a great way to get insights about your data and the corrections that were made.</p>
            """
            )

        elif topic_name == "Generating Reports":
            return (
                css
                + """
            <h1>Generating Reports</h1>
            <p>You can generate various reports to analyze your chest entry data.</p>
            
            <h2>Report Types</h2>
            <ul>
                <li><strong>Summary Report</strong>: Overall statistics about entries and corrections</li>
                <li><strong>Correction Report</strong>: Details of all corrections made</li>
                <li><strong>Validation Report</strong>: Analysis of validation issues</li>
                <li><strong>Player Report</strong>: Statistics by player</li>
                <li><strong>Chest Type Report</strong>: Statistics by chest type</li>
                <li><strong>Source Report</strong>: Statistics by source</li>
            </ul>
            
            <h2>Generating a Report</h2>
            <ol>
                <li>Go to the Reports tab</li>
                <li>Select a report type from the dropdown</li>
                <li>Click "Generate Report"</li>
                <li>The report will appear in the display area</li>
            </ol>
            
            <h2>Report Contents</h2>
            <p>Reports typically include:</p>
            <ul>
                <li>A title and generation timestamp</li>
                <li>Summary statistics</li>
                <li>Detailed breakdowns in tables</li>
                <li>Charts and visualizations (where applicable)</li>
                <li>Analysis of trends or issues</li>
            </ul>
            
            <p class="warning">Warning: Reports are generated from the currently loaded data. Make sure you have applied all corrections before generating reports.</p>
            """
            )

        elif topic_name == "Exporting Reports":
            return (
                css
                + """
            <h1>Exporting Reports</h1>
            <p>After generating a report, you can export it in various formats.</p>
            
            <h2>Export Formats</h2>
            <ul>
                <li><strong>PDF</strong>: Portable Document Format (best for printing)</li>
                <li><strong>HTML</strong>: Web page format (can be viewed in browsers)</li>
                <li><strong>CSV</strong>: Comma-separated values (for data analysis)</li>
                <li><strong>PNG</strong>: Image format (for charts and visualizations)</li>
            </ul>
            
            <h2>Exporting a Report</h2>
            <ol>
                <li>Generate the report you want to export</li>
                <li>Click "Export Report" in the Reports panel</li>
                <li>Select the export format from the dropdown</li>
                <li>Choose a location and filename</li>
                <li>Click "Save"</li>
            </ol>
            
            <h2>Batch Exporting</h2>
            <p>You can also export all report types at once:</p>
            <ol>
                <li>Click "Export All Reports" in the Reports panel</li>
                <li>Select a directory to save the reports</li>
                <li>Choose the export format</li>
                <li>All report types will be generated and saved</li>
            </ol>
            
            <p class="tip">Tip: PDF format is best for sharing reports with others, while CSV is useful if you want to do further analysis in a spreadsheet program.</p>
            """
            )

        elif topic_name == "Settings":
            return (
                css
                + """
            <h1>Settings</h1>
            <p>The Settings panel allows you to configure various aspects of the application.</p>
            
            <h2>Settings Categories</h2>
            <ul>
                <li><strong>General</strong>: Basic application settings</li>
                <li><strong>File Paths</strong>: Default directories and file formats</li>
                <li><strong>Validation</strong>: Settings for validation behavior</li>
                <li><strong>User Interface</strong>: Appearance and layout settings</li>
            </ul>
            
            <h2>Saving Settings</h2>
            <p>Changes to settings are not applied until you click "Save Settings". All settings are saved to a configuration file for future use.</p>
            
            <h2>Resetting to Defaults</h2>
            <p>If you want to restore the default settings, click "Reset to Defaults" in the Settings panel.</p>
            
            <h2>Settings Location</h2>
            <p>Your settings are stored in a configuration file in the application data directory, which varies by operating system:</p>
            <ul>
                <li><strong>Windows</strong>: %APPDATA%\ChestTrackerCorrector\config.ini</li>
                <li><strong>macOS</strong>: ~/Library/Application Support/ChestTrackerCorrector/config.ini</li>
                <li><strong>Linux</strong>: ~/.config/ChestTrackerCorrector/config.ini</li>
            </ul>
            
            <p class="warning">Warning: Manually editing the configuration file is not recommended and may cause the application to behave unexpectedly.</p>
            """
            )

        elif topic_name == "Application Settings":
            return (
                css
                + """
            <h1>Application Settings</h1>
            <p>Here's a detailed breakdown of available application settings:</p>
            
            <h2>General Settings</h2>
            <ul>
                <li><strong>Theme</strong>: Choose between light and dark themes</li>
                <li><strong>Auto-save Settings</strong>: Automatically save settings on change</li>
                <li><strong>Remember Window Size</strong>: Save window size and position between sessions</li>
            </ul>
            
            <h2>File Path Settings</h2>
            <ul>
                <li><strong>Default Directories</strong>: Set default locations for various file types</li>
                <li><strong>Default File Extensions</strong>: Set preferred file formats for import/export</li>
            </ul>
            
            <h2>Validation Settings</h2>
            <ul>
                <li><strong>Auto-validate on Load</strong>: Automatically validate entries when loaded</li>
                <li><strong>Validation Strictness</strong>: Set the matching strictness level</li>
                <li><strong>Validation Lists</strong>: Choose which fields to validate</li>
                <li><strong>Fuzzy Matching</strong>: Configure fuzzy matching settings</li>
            </ul>
            
            <h2>UI Settings</h2>
            <ul>
                <li><strong>Table Settings</strong>: Configure table appearance</li>
                <li><strong>Font Size</strong>: Set text size throughout the application</li>
                <li><strong>Layout Settings</strong>: Adjust panel proportions</li>
            </ul>
            
            <p class="tip">Tip: Experiment with different settings to find the configuration that works best for your workflow.</p>
            """
            )

        else:
            return (
                css
                + """
            <h1>Topic Not Found</h1>
            <p>Sorry, the help content for this topic has not been created yet.</p>
            <p>Please check back later or refer to other help topics.</p>
            """
            )
