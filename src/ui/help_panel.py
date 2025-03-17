"""
help_panel.py

Description: Provides a help panel with documentation for the application features
Usage:
    help_panel = HelpPanel(parent)
    layout.addWidget(help_panel)
"""
from typing import Optional, Dict, List
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QTextBrowser, QTreeWidget, QTreeWidgetItem, 
    QSplitter, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon

class HelpPanel(QWidget):
    """
    A panel that displays help documentation for the application.
    
    Attributes:
        _tree_widget (QTreeWidget): Navigation tree for help topics
        _content_browser (QTextBrowser): Browser to display help content
        
    Implementation Notes:
        - Uses a tree structure for navigating help topics
        - Uses a text browser to display formatted HTML content
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the help panel.
        
        Args:
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self._setup_ui()
        self._populate_help_content()
        
    def _setup_ui(self):
        """Set up the user interface components."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create splitter for navigation and content
        splitter = QSplitter(Qt.Horizontal)
        
        # Setup navigation tree
        self._tree_widget = QTreeWidget()
        self._tree_widget.setHeaderLabel("Help Topics")
        self._tree_widget.setMinimumWidth(200)
        self._tree_widget.itemClicked.connect(self._on_topic_selected)
        
        # Setup content browser
        self._content_browser = QTextBrowser()
        self._content_browser.setOpenExternalLinks(True)
        self._content_browser.setMinimumWidth(400)
        
        # Add widgets to splitter
        splitter.addWidget(self._tree_widget)
        splitter.addWidget(self._content_browser)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
    
    def _populate_help_content(self):
        """Populate the help content with topics and content."""
        # Add main topics
        getting_started = self._add_topic("Getting Started", None)
        file_panel = self._add_topic("File Panel", None)
        validation = self._add_topic("Validation", None)
        corrector = self._add_topic("Corrector", None)
        preview = self._add_topic("Preview", None)
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
        
        self._add_topic("Using Preview Mode", preview)
        
        self._add_topic("Generating Reports", reports)
        self._add_topic("Exporting Reports", reports)
        
        self._add_topic("Application Settings", settings)
        
        # Select the first item by default
        self._tree_widget.setCurrentItem(getting_started)
        self._on_topic_selected(getting_started, 0)
    
    def _add_topic(self, name: str, parent: Optional[QTreeWidgetItem]) -> QTreeWidgetItem:
        """
        Add a topic to the help tree.
        
        Args:
            name (str): Topic name
            parent (QTreeWidgetItem, optional): Parent topic
            
        Returns:
            QTreeWidgetItem: The created topic item
        """
        if parent is None:
            item = QTreeWidgetItem(self._tree_widget, [name])
        else:
            item = QTreeWidgetItem(parent, [name])
        
        item.setData(0, Qt.UserRole, name)
        return item
    
    def _on_topic_selected(self, item: QTreeWidgetItem, column: int):
        """
        Handle selection of a help topic.
        
        Args:
            item (QTreeWidgetItem): Selected item
            column (int): Selected column
        """
        topic_name = item.data(0, Qt.UserRole)
        self._show_topic_content(topic_name)
    
    def _show_topic_content(self, topic_name: str):
        """
        Show the content for the selected topic.
        
        Args:
            topic_name (str): Name of the selected topic
        """
        html_content = self._get_topic_content(topic_name)
        self._content_browser.setHtml(html_content)
    
    def _get_topic_content(self, topic_name: str) -> str:
        """
        Get the HTML content for a specific topic.
        
        Args:
            topic_name (str): Name of the topic
            
        Returns:
            str: HTML content for the topic
        """
        # Common CSS for all pages
        css = """
            body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
            h1 { color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
            h2 { color: #3498db; margin-top: 20px; }
            h3 { color: #2c3e50; }
            p { line-height: 1.6; }
            ul, ol { line-height: 1.6; }
            .note { background-color: #f8f9fa; padding: 15px; border-left: 5px solid #3498db; margin: 15px 0; }
            .warning { background-color: #fff3cd; padding: 15px; border-left: 5px solid #ffc107; margin: 15px 0; }
            .tip { background-color: #d4edda; padding: 15px; border-left: 5px solid #28a745; margin: 15px 0; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            code { background-color: #f8f9fa; padding: 2px 5px; border-radius: 3px; font-family: monospace; }
        """
        
        # Define content for each topic
        if topic_name == "Getting Started":
            content = f"""
            <h1>Getting Started</h1>
            <p>Welcome to the Chest Tracker Correction Tool! This application helps you correct OCR-recognized text from the Total Battle game by providing tools to load, validate, and correct chest entries.</p>
            
            <h2>Main Features</h2>
            <ul>
                <li><strong>File Loading</strong>: Load text files with chest entries and CSV files with correction rules</li>
                <li><strong>Validation</strong>: Create and manage validation lists for chest types, player names, and sources</li>
                <li><strong>Correction</strong>: Apply corrections to entries based on rules or manual edits</li>
                <li><strong>Preview</strong>: Compare original and corrected entries side by side</li>
                <li><strong>Reports</strong>: Generate reports on entries, corrections, and validation</li>
                <li><strong>Settings</strong>: Customize application behavior and appearance</li>
            </ul>
            
            <h2>Quick Start</h2>
            <ol>
                <li>Go to the <strong>Files</strong> tab to load your text file with chest entries</li>
                <li>Load a CSV file with correction rules if available</li>
                <li>Switch to the <strong>Corrector</strong> tab to view and correct entries</li>
                <li>Use the <strong>Validation</strong> tab to create validation lists if needed</li>
                <li>Apply corrections automatically or manually</li>
                <li>Export the corrected entries when finished</li>
            </ol>
            
            <p class="tip">Tip: You can save your validation lists and correction rules for future use.</p>
            """
        elif topic_name == "Application Overview":
            content = f"""
            <h1>Application Overview</h1>
            <p>The Chest Tracker Correction Tool is designed to help players of Total Battle correct OCR-recognized text entries for chest tracking. It provides a comprehensive set of tools for managing, validating, and correcting chest entries.</p>
            
            <h2>Application Workflow</h2>
            <p>The typical workflow in the application follows these steps:</p>
            <ol>
                <li><strong>Load Data</strong>: Import text files with chest entries and CSV files with correction rules</li>
                <li><strong>Validate</strong>: Check entries against validation lists to identify potential errors</li>
                <li><strong>Correct</strong>: Apply automatic corrections based on rules or make manual corrections</li>
                <li><strong>Preview</strong>: Compare original and corrected entries to verify changes</li>
                <li><strong>Report</strong>: Generate reports on entries, corrections, and validation</li>
                <li><strong>Export</strong>: Save the corrected entries in the original format</li>
            </ol>
            
            <h2>Data Structure</h2>
            <p>The application works with chest entries that have the following structure:</p>
            <ul>
                <li><strong>Chest Type</strong>: The type of chest (e.g., "Cobra Chest", "Elegant Chest")</li>
                <li><strong>Player</strong>: The player who obtained the chest (prefixed with "From:")</li>
                <li><strong>Source</strong>: Where the chest was obtained from (prefixed with "Source:")</li>
            </ul>
            
            <p class="note">Note: The application preserves the original format of the text file when exporting corrected entries.</p>
            """
        elif topic_name == "User Interface":
            content = f"""
            <h1>User Interface</h1>
            <p>The application interface is organized into several tabs, each providing different functionality:</p>
            
            <h2>Navigation Bar</h2>
            <p>The navigation bar on the left side allows you to switch between the main application tabs:</p>
            <ul>
                <li><strong>Files</strong>: Load and manage input files and correction rules</li>
                <li><strong>Validation</strong>: Create and manage validation lists</li>
                <li><strong>Corrector</strong>: View and correct entries</li>
                <li><strong>Reports</strong>: Generate and export reports</li>
                <li><strong>Settings</strong>: Configure application settings</li>
                <li><strong>Help</strong>: Access this help documentation</li>
            </ul>
            
            <h2>Files Tab</h2>
            <p>The Files tab is where you load input data:</p>
            <ul>
                <li>Load text files with chest entries</li>
                <li>Load CSV files with correction rules</li>
                <li>View file statistics</li>
            </ul>
            
            <h2>Validation Tab</h2>
            <p>The Validation tab allows you to create and manage validation lists:</p>
            <ul>
                <li>Create lists for chest types, player names, and sources</li>
                <li>Add, edit, and remove items from lists</li>
                <li>Import and export validation lists</li>
            </ul>
            
            <h2>Corrector Tab</h2>
            <p>The Corrector tab is the main workspace for viewing and correcting entries:</p>
            <ul>
                <li>View entries in a table</li>
                <li>Filter and sort entries</li>
                <li>Apply corrections manually or automatically</li>
                <li>Toggle preview mode</li>
            </ul>
            
            <h2>Reports Tab</h2>
            <p>The Reports tab provides tools for generating reports:</p>
            <ul>
                <li>Generate summary reports</li>
                <li>View correction statistics</li>
                <li>Export reports in various formats</li>
            </ul>
            
            <h2>Settings Tab</h2>
            <p>The Settings tab allows you to customize the application:</p>
            <ul>
                <li>Configure UI preferences</li>
                <li>Set file handling options</li>
                <li>Customize validation settings</li>
                <li>Configure general application behavior</li>
            </ul>
            
            <p class="tip">Tip: You can resize panels by dragging the splitters between them.</p>
            """
        elif topic_name == "Loading Files":
            content = f"""
            <h1>Loading Files</h1>
            <p>The File Panel allows you to load text files with chest entries and CSV files with correction rules. This is typically the first step in the correction workflow.</p>
            
            <h2>Loading Chest Entries</h2>
            <p>To load a text file containing chest entries:</p>
            <ol>
                <li>Click the <strong>Load Entries</strong> button</li>
                <li>Select a text file in the file dialog</li>
                <li>The application will parse the file and display statistics about the loaded entries</li>
            </ol>
            
            <h3>Entry Format</h3>
            <p>The text file should contain chest entries in the following format:</p>
            <pre><code>Chest Type
From: Player Name
Source: Location
</code></pre>
            <p>For example:</p>
            <pre><code>Cobra Chest
From: Engelchen
Source: Level 25 Crypt
</code></pre>
            
            <p class="note">Note: Entries are separated by blank lines. The "Source:" line is optional.</p>
            
            <h2>Loading Correction Rules</h2>
            <p>To load a CSV file with correction rules:</p>
            <ol>
                <li>Click the <strong>Load Rules</strong> button</li>
                <li>Select a CSV file in the file dialog</li>
                <li>The application will parse the file and display statistics about the loaded rules</li>
            </ol>
            
            <h3>CSV Format</h3>
            <p>The CSV file should contain correction rules with "From" and "To" columns:</p>
            <table>
                <tr>
                    <th>From</th>
                    <th>To</th>
                </tr>
                <tr>
                    <td>VVarrior's Chest</td>
                    <td>Warrior's Chest</td>
                </tr>
                <tr>
                    <td>Clan vvealth</td>
                    <td>Clan wealth</td>
                </tr>
            </table>
            
            <p>The "From" column contains the text to be replaced, and the "To" column contains the corrected text.</p>
            
            <p class="warning">Warning: Make sure your CSV file uses semicolons (;) as separators and has proper header row.</p>
            
            <h2>File Statistics</h2>
            <p>After loading files, the File Panel displays statistics about the loaded data:</p>
            <ul>
                <li>Number of entries in the text file</li>
                <li>Number of correction rules in the CSV file</li>
                <li>Number of entries with a source field</li>
                <li>Number of unique chest types, player names, and sources</li>
            </ul>
            
            <p class="tip">Tip: You can reload files at any time by clicking the respective load buttons again.</p>
            """
        elif topic_name == "File Formats":
            content = f"""
            <h1>File Formats</h1>
            <p>The Chest Tracker Correction Tool works with specific file formats for input data and correction rules.</p>
            
            <h2>Text File Format (Chest Entries)</h2>
            <p>The application expects text files with chest entries in a specific format:</p>
            
            <pre><code>Chest Type 1
From: Player 1
Source: Location 1

Chest Type 2
From: Player 2
Source: Location 2

Chest Type 3
From: Player 3
</code></pre>
            
            <p>Each entry consists of:</p>
            <ul>
                <li>A line with the chest type (e.g., "Cobra Chest")</li>
                <li>A line with the player name, prefixed with "From:" (e.g., "From: Engelchen")</li>
                <li>An optional line with the source, prefixed with "Source:" (e.g., "Source: Level 25 Crypt")</li>
            </ul>
            
            <p>Entries are separated by blank lines.</p>
            
            <h2>CSV File Format (Correction Rules)</h2>
            <p>Correction rules should be provided in a CSV file with the following format:</p>
            
            <pre><code>From;To
VVarrior's Chest;Warrior's Chest
Clan vvealth;Clan wealth
"Fenrir""s Chest";Fenrir's Chest
</code></pre>
            
            <p>The CSV file should:</p>
            <ul>
                <li>Use semicolons (;) as separators</li>
                <li>Have a header row with "From" and "To" columns</li>
                <li>Enclose text with quotes if it contains semicolons or quotes</li>
                <li>Double quotes to escape quotes within quoted strings</li>
            </ul>
            
            <h2>Validation List Format</h2>
            <p>Validation lists can be exported and imported as text files with one item per line:</p>
            
            <pre><code>Cobra Chest
Elegant Chest
Chest of the Cursed
Bone Chest
Merchant's Chest
</code></pre>
            
            <p class="note">Note: When importing validation lists, empty lines and lines starting with # are ignored.</p>
            
            <h2>Export Format</h2>
            <p>When exporting corrected entries, the application preserves the original format of the text file:</p>
            
            <pre><code>Cobra Chest
From: Engelchen
Source: Level 25 Crypt

Elegant Chest
From: Moony
Source: Level 25 Crypt
</code></pre>
            
            <p class="tip">Tip: The application automatically detects and preserves the structure of your input files.</p>
            """
        elif topic_name == "Validation Lists":
            content = f"""
            <h1>Validation Lists</h1>
            <p>Validation lists help you identify potential errors in chest entries by comparing them against known valid values.</p>
            
            <h2>Types of Validation Lists</h2>
            <p>The application supports three types of validation lists:</p>
            <ul>
                <li><strong>Chest Types</strong>: Valid chest type names (e.g., "Cobra Chest", "Elegant Chest")</li>
                <li><strong>Player Names</strong>: Valid player names (e.g., "Engelchen", "Sir Met")</li>
                <li><strong>Sources</strong>: Valid source locations (e.g., "Level 25 Crypt", "Mercenary Exchange")</li>
            </ul>
            
            <h2>Creating Validation Lists</h2>
            <p>To create a validation list:</p>
            <ol>
                <li>Go to the <strong>Validation</strong> tab</li>
                <li>Select the type of list you want to create (Chest Types, Player Names, or Sources)</li>
                <li>Click the <strong>Create List</strong> button</li>
                <li>Enter a name for the list</li>
                <li>Add items to the list</li>
                <li>Click <strong>Save</strong> to save the list</li>
            </ol>
            
            <h2>Adding Items to Lists</h2>
            <p>You can add items to a validation list in several ways:</p>
            <ul>
                <li>Enter items manually in the item editor</li>
                <li>Import items from a text file</li>
                <li>Add current entries from the loaded text file</li>
                <li>Add one or more selected entries from the table</li>
            </ul>
            
            <h2>Using Validation Lists</h2>
            <p>When validation lists are active, the application highlights entries that do not match any item in the corresponding list:</p>
            <ul>
                <li>Valid entries are displayed normally</li>
                <li>Invalid entries are highlighted with a background color</li>
                <li>Hovering over an invalid entry shows a tooltip with the validation error</li>
            </ul>
            
            <p class="tip">Tip: You can toggle validation on and off for each type of list independently.</p>
            """
        elif topic_name == "Managing Lists":
            content = f"""
            <h1>Managing Validation Lists</h1>
            <p>The Validation Panel provides tools for creating, editing, importing, and exporting validation lists.</p>
            
            <h2>List Management</h2>
            <p>To manage validation lists:</p>
            <ul>
                <li><strong>Create</strong>: Click the "Create List" button to create a new list</li>
                <li><strong>Rename</strong>: Click the "Rename List" button to rename an existing list</li>
                <li><strong>Delete</strong>: Click the "Delete List" button to delete a list</li>
                <li><strong>Clone</strong>: Click the "Clone List" button to create a copy of a list</li>
            </ul>
            
            <h2>Item Management</h2>
            <p>To manage items in a validation list:</p>
            <ul>
                <li><strong>Add</strong>: Enter an item in the text field and click "Add Item"</li>
                <li><strong>Remove</strong>: Select an item and click "Remove Item"</li>
                <li><strong>Edit</strong>: Double-click an item to edit it directly</li>
                <li><strong>Import</strong>: Click "Import Items" to import items from a text file</li>
                <li><strong>Export</strong>: Click "Export List" to save the list to a text file</li>
            </ul>
            
            <h2>Auto-population</h2>
            <p>You can automatically populate validation lists from loaded entries:</p>
            <ol>
                <li>Load a text file with chest entries</li>
                <li>Go to the Validation Panel</li>
                <li>Select or create a validation list</li>
                <li>Click "Add Current Entries" to add all unique values from the loaded file</li>
            </ol>
            
            <p class="note">Note: You can also add selected entries from the Corrector Panel to a validation list.</p>
            
            <h2>Activating Lists</h2>
            <p>To activate a validation list for validation:</p>
            <ol>
                <li>Select the list from the dropdown menu</li>
                <li>Check the "Active" checkbox</li>
            </ol>
            
            <p>When a list is active, entries that do not match any item in the list will be highlighted in the Corrector Panel.</p>
            
            <p class="tip">Tip: You can have multiple validation lists but only one list of each type can be active at a time.</p>
            """
        elif topic_name == "Correction Rules":
            content = f"""
            <h1>Correction Rules</h1>
            <p>Correction rules specify how to replace text strings in chest entries. They help automate the correction process for common OCR errors.</p>
            
            <h2>Rule Structure</h2>
            <p>Each correction rule consists of two parts:</p>
            <ul>
                <li><strong>From</strong>: The text string to be replaced</li>
                <li><strong>To</strong>: The corrected text string</li>
            </ul>
            
            <p>For example:</p>
            <table>
                <tr>
                    <th>From</th>
                    <th>To</th>
                </tr>
                <tr>
                    <td>VVarrior's Chest</td>
                    <td>Warrior's Chest</td>
                </tr>
                <tr>
                    <td>Clan vvealth</td>
                    <td>Clan wealth</td>
                </tr>
            </table>
            
            <h2>Loading Rules</h2>
            <p>To load correction rules:</p>
            <ol>
                <li>Go to the Files Panel</li>
                <li>Click the "Load Rules" button</li>
                <li>Select a CSV file with correction rules</li>
            </ol>
            
            <h2>Applying Rules</h2>
            <p>To apply correction rules to entries:</p>
            <ol>
                <li>Go to the Corrector Panel</li>
                <li>Click the "Apply Corrections" button</li>
            </ol>
            
            <p>The application will apply all loaded correction rules to the entries and display the corrected values.</p>
            
            <h2>Creating Rules</h2>
            <p>You can create correction rules manually:</p>
            <ol>
                <li>Edit an entry in the Corrector Panel</li>
                <li>The application will ask if you want to add the correction to the rules</li>
                <li>Confirm to add the correction as a new rule</li>
            </ol>
            
            <p class="warning">Warning: Be careful with rules that have overlapping patterns, as they might interfere with each other.</p>
            
            <h2>Exporting Rules</h2>
            <p>To export correction rules:</p>
            <ol>
                <li>Go to the Files Panel</li>
                <li>Click the "Export Rules" button</li>
                <li>Choose a location and filename for the CSV file</li>
            </ol>
            
            <p class="tip">Tip: You can build up a library of correction rules over time to handle common OCR errors in your game.</p>
            """
        elif topic_name == "Applying Corrections":
            content = f"""
            <h1>Applying Corrections</h1>
            <p>The Chest Tracker Correction Tool provides several methods for correcting entries, both automatically and manually.</p>
            
            <h2>Automatic Corrections</h2>
            <p>To apply automatic corrections based on loaded rules:</p>
            <ol>
                <li>Ensure you have loaded a CSV file with correction rules</li>
                <li>Go to the Corrector Panel</li>
                <li>Click the "Apply Corrections" button</li>
            </ol>
            
            <p>The application will apply all loaded correction rules to the entries and update the display.</p>
            
            <h2>Manual Corrections</h2>
            <p>To manually correct an entry:</p>
            <ol>
                <li>In the Corrector Panel, double-click the cell you want to edit</li>
                <li>Enter the corrected text</li>
                <li>Press Enter or click outside the cell to confirm</li>
            </ol>
            
            <p>After making a manual correction, the application will ask if you want to add it to the correction rules.</p>
            
            <h2>Batch Corrections</h2>
            <p>To apply the same correction to multiple entries:</p>
            <ol>
                <li>Select multiple entries in the table (using Ctrl+click or Shift+click)</li>
                <li>Right-click and select "Edit Selected" from the context menu</li>
                <li>Enter the corrected value in the dialog</li>
                <li>Confirm to apply the correction to all selected entries</li>
            </ol>
            
            <h2>Validation-Based Corrections</h2>
            <p>You can use validation lists to identify entries that need correction:</p>
            <ol>
                <li>Activate validation lists for chest types, player names, and/or sources</li>
                <li>Look for entries highlighted as invalid in the table</li>
                <li>Correct these entries manually or with rules</li>
            </ol>
            
            <h2>Preview Corrections</h2>
            <p>To preview corrections before applying them:</p>
            <ol>
                <li>In the Corrector Panel, check the "Show Preview" checkbox</li>
                <li>Select an entry in the table</li>
                <li>The preview panel will show the original and corrected values side by side</li>
            </ol>
            
            <p class="tip">Tip: Use the preview mode to verify corrections before exporting the final result.</p>
            """
        elif topic_name == "Filtering Entries":
            content = f"""
            <h1>Filtering Entries</h1>
            <p>The Corrector Panel provides tools for filtering and sorting entries to help you focus on specific subsets of data.</p>
            
            <h2>Basic Filtering</h2>
            <p>To filter entries by text:</p>
            <ol>
                <li>Enter a search term in the filter text field</li>
                <li>Select which columns to search in (Chest Type, Player, Source, or All)</li>
                <li>The table will update to show only entries that match the filter</li>
            </ol>
            
            <h2>Advanced Filtering</h2>
            <p>The application supports several advanced filtering options:</p>
            <ul>
                <li><strong>Show Unique Only</strong>: Display only unique entries (removes duplicates)</li>
                <li><strong>Show Valid Only</strong>: Display only entries that pass validation</li>
                <li><strong>Show Invalid Only</strong>: Display only entries that fail validation</li>
                <li><strong>Show Corrected Only</strong>: Display only entries that have been corrected</li>
            </ul>
            
            <p>These filters can be combined with text filters for more precise control.</p>
            
            <h2>Sorting</h2>
            <p>To sort entries:</p>
            <ol>
                <li>Click on a column header to sort by that column</li>
                <li>Click again to toggle between ascending and descending order</li>
            </ol>
            
            <h2>Grouping</h2>
            <p>You can group entries by different criteria:</p>
            <ul>
                <li><strong>Group by Chest Type</strong>: Organize entries by chest type</li>
                <li><strong>Group by Player</strong>: Organize entries by player name</li>
                <li><strong>Group by Source</strong>: Organize entries by source location</li>
            </ul>
            
            <p>When grouping is active, the table displays a hierarchical view with expandable groups.</p>
            
            <h2>Selection</h2>
            <p>You can select entries in several ways:</p>
            <ul>
                <li>Click on an entry to select it</li>
                <li>Ctrl+click to select multiple individual entries</li>
                <li>Shift+click to select a range of entries</li>
                <li>Ctrl+A to select all visible entries</li>
            </ul>
            
            <p class="note">Note: Filtering affects export operations. Only visible entries will be included in exports.</p>
            
            <p class="tip">Tip: Use filtering to isolate specific entries that need correction, then batch process them.</p>
            """
        elif topic_name == "Using Preview Mode":
            content = f"""
            <h1>Using Preview Mode</h1>
            <p>The Preview Mode allows you to compare original and corrected entries side by side, making it easier to verify changes.</p>
            
            <h2>Enabling Preview Mode</h2>
            <p>To enable the preview mode:</p>
            <ol>
                <li>Go to the Corrector Panel</li>
                <li>Check the "Show Preview" checkbox</li>
            </ol>
            
            <p>When enabled, the Corrector Panel splits into two parts: the entry table on the left and the preview panel on the right.</p>
            
            <h2>Viewing Changes</h2>
            <p>To view changes for an entry:</p>
            <ol>
                <li>Select an entry in the table</li>
                <li>The preview panel will show:</li>
                <ul>
                    <li>The original entry on the left</li>
                    <li>The corrected entry on the right</li>
                    <li>Highlighted changes to make them easy to spot</li>
                </ul>
            </ol>
            
            <h2>Navigating Entries</h2>
            <p>The preview panel provides navigation buttons to move between entries:</p>
            <ul>
                <li><strong>Previous</strong>: Move to the previous entry</li>
                <li><strong>Next</strong>: Move to the next entry</li>
            </ul>
            
            <p>You can also click on entries in the table to select them for preview.</p>
            
            <h2>Change Details</h2>
            <p>The preview panel shows details about the changes made to an entry:</p>
            <ul>
                <li>Which fields were changed (Chest Type, Player, Source)</li>
                <li>The original and corrected values for each changed field</li>
                <li>Which correction rules were applied</li>
            </ul>
            
            <h2>Resizing the Preview</h2>
            <p>You can resize the preview panel by dragging the splitter between the table and the preview panel.</p>
            
            <p class="tip">Tip: Use the preview mode to quickly check all corrections before exporting the final result.</p>
            """
        elif topic_name == "Generating Reports":
            content = f"""
            <h1>Generating Reports</h1>
            <p>The Reports Panel allows you to generate various reports on your chest entries, corrections, and validation status.</p>
            
            <h2>Report Types</h2>
            <p>The application supports several types of reports:</p>
            <ul>
                <li><strong>Summary Report</strong>: Overall statistics about entries and corrections</li>
                <li><strong>Correction Report</strong>: Details on which entries were corrected and how</li>
                <li><strong>Validation Report</strong>: Information about validation failures</li>
                <li><strong>Player Statistics</strong>: Breakdown of chests by player</li>
                <li><strong>Chest Type Statistics</strong>: Distribution of different chest types</li>
                <li><strong>Source Statistics</strong>: Analysis of chest sources</li>
            </ul>
            
            <h2>Generating a Report</h2>
            <p>To generate a report:</p>
            <ol>
                <li>Go to the Reports Panel</li>
                <li>Select the type of report from the dropdown menu</li>
                <li>Configure any report-specific options</li>
                <li>Click the "Generate Report" button</li>
            </ol>
            
            <p>The report will be displayed in the report viewer.</p>
            
            <h2>Viewing Reports</h2>
            <p>Reports can be viewed in different formats:</p>
            <ul>
                <li><strong>Text View</strong>: Plain text format</li>
                <li><strong>Table View</strong>: Structured table format</li>
                <li><strong>Chart View</strong>: Graphical representation (for statistical reports)</li>
            </ul>
            
            <p>You can switch between these views using the tabs at the bottom of the report viewer.</p>
            
            <h2>Report Filters</h2>
            <p>You can filter the data included in reports:</p>
            <ul>
                <li><strong>Include All Entries</strong>: Generate report for all entries</li>
                <li><strong>Include Filtered Entries Only</strong>: Generate report only for entries currently visible in the Corrector Panel</li>
                <li><strong>Include Selected Entries Only</strong>: Generate report only for entries selected in the Corrector Panel</li>
            </ul>
            
            <p class="note">Note: Report filters are applied before the report is generated. Changing filters requires regenerating the report.</p>
            
            <h2>Report Parameters</h2>
            <p>Some reports have configurable parameters:</p>
            <ul>
                <li><strong>Summary Report</strong>: Level of detail (basic or detailed)</li>
                <li><strong>Correction Report</strong>: Include unchanged entries (yes/no)</li>
                <li><strong>Validation Report</strong>: Validation types to include (chest types, player names, sources)</li>
            </ul>
            
            <p class="tip">Tip: Experiment with different report parameters to get the information you need.</p>
            """
            
        elif topic_name == "Exporting Reports":
            content = f"""
            <h1>Exporting Reports</h1>
            <p>The Reports Panel allows you to export reports in various formats for sharing or further analysis.</p>
            
            <h2>Export Formats</h2>
            <p>Reports can be exported in several formats:</p>
            <ul>
                <li><strong>Text (.txt)</strong>: Plain text format</li>
                <li><strong>CSV (.csv)</strong>: Comma-separated values for spreadsheet applications</li>
                <li><strong>HTML (.html)</strong>: Formatted HTML for viewing in web browsers</li>
                <li><strong>PDF (.pdf)</strong>: Portable Document Format for printing and sharing</li>
            </ul>
            
            <h2>Exporting a Report</h2>
            <p>To export a report:</p>
            <ol>
                <li>Generate the report you want to export</li>
                <li>Click the "Export" button</li>
                <li>Select the export format from the dropdown menu</li>
                <li>Choose a location and filename for the exported report</li>
                <li>Click "Save"</li>
            </ol>
            
            <h2>Export Settings</h2>
            <p>When exporting, you can configure various settings:</p>
            <ul>
                <li><strong>Text Format</strong>: Character encoding and line ending style</li>
                <li><strong>CSV Format</strong>: Delimiter character and include/exclude headers</li>
                <li><strong>HTML Format</strong>: Include styling and formatting options</li>
                <li><strong>PDF Format</strong>: Page size, orientation, and font settings</li>
            </ul>
            
            <p>These settings can be configured in the export dialog or in the application settings.</p>
            
            <h2>Clipboard Operations</h2>
            <p>You can also copy report content to the clipboard:</p>
            <ol>
                <li>Generate the report you want to copy</li>
                <li>Click the "Copy to Clipboard" button</li>
                <li>The report content will be copied in the format corresponding to the current view (text, table, or chart)</li>
            </ol>
            
            <p class="note">Note: When copying chart data, the application will copy the underlying data rather than the visual chart.</p>
            
            <h2>Batch Export</h2>
            <p>To export multiple reports at once:</p>
            <ol>
                <li>Generate each report you want to export</li>
                <li>Click the "Batch Export" button</li>
                <li>Select which reports to include in the batch</li>
                <li>Choose a format and destination folder</li>
                <li>Click "Export All"</li>
            </ol>
            
            <p class="tip">Tip: Use the HTML format for reports you want to share electronically with formatting preserved.</p>
            """
            
        elif topic_name == "Application Settings":
            content = f"""
            <h1>Application Settings</h1>
            <p>The Settings Panel allows you to customize various aspects of the application to suit your preferences.</p>
            
            <h2>Accessing Settings</h2>
            <p>To access the application settings:</p>
            <ol>
                <li>Click on the "Settings" tab in the navigation panel</li>
                <li>The Settings Panel will display various categories of settings</li>
            </ol>
            
            <h2>UI Settings</h2>
            <p>UI settings control the appearance and behavior of the user interface:</p>
            <ul>
                <li><strong>Theme</strong>: Light or dark mode</li>
                <li><strong>Font Size</strong>: Text size in the application</li>
                <li><strong>Table Row Height</strong>: Height of rows in tables</li>
                <li><strong>Show Tooltips</strong>: Enable or disable tooltips</li>
                <li><strong>Highlight Colors</strong>: Colors used for highlighting in the application</li>
            </ul>
            
            <h2>File Settings</h2>
            <p>File settings control how the application handles files:</p>
            <ul>
                <li><strong>Default Directories</strong>: Where the application looks for files by default</li>
                <li><strong>File Encoding</strong>: Character encoding for text files</li>
                <li><strong>CSV Delimiter</strong>: Character used to separate values in CSV files</li>
                <li><strong>Auto-load Previous Files</strong>: Whether to automatically load the last used files on startup</li>
            </ul>
            
            <h2>Validation Settings</h2>
            <p>Validation settings control how validation works:</p>
            <ul>
                <li><strong>Case Sensitivity</strong>: Whether validation is case-sensitive</li>
                <li><strong>Auto-activate Lists</strong>: Whether validation lists are automatically activated</li>
                <li><strong>Validation Colors</strong>: Colors used for valid and invalid entries</li>
                <li><strong>Default Validation Mode</strong>: The default validation mode for new lists</li>
            </ul>
            
            <h2>Correction Settings</h2>
            <p>Correction settings control how corrections are applied:</p>
            <ul>
                <li><strong>Auto-suggest Corrections</strong>: Whether to automatically suggest corrections</li>
                <li><strong>Prompt to Add Corrections</strong>: Whether to ask before adding manual corrections to rules</li>
                <li><strong>Preserve Case</strong>: Whether to preserve case when applying corrections</li>
                <li><strong>Apply to Selected Only</strong>: Whether to apply corrections to selected entries only by default</li>
            </ul>
            
            <h2>Report Settings</h2>
            <p>Report settings control how reports are generated and displayed:</p>
            <ul>
                <li><strong>Default Report Type</strong>: The default report type to generate</li>
                <li><strong>Include Details</strong>: Whether to include detailed information by default</li>
                <li><strong>Default Export Format</strong>: The default format for exporting reports</li>
                <li><strong>Chart Type</strong>: The default chart type for statistical reports</li>
            </ul>
            
            <h2>Saving Settings</h2>
            <p>To save your settings:</p>
            <ol>
                <li>Make the desired changes to the settings</li>
                <li>Click the "Save" button at the bottom of the Settings Panel</li>
            </ol>
            
            <p>Settings are automatically saved when you close the application.</p>
            
            <h2>Resetting Settings</h2>
            <p>To reset settings to their default values:</p>
            <ol>
                <li>Click the "Reset" button in the Settings Panel</li>
                <li>Confirm that you want to reset all settings</li>
            </ol>
            
            <p class="warning">Warning: Resetting settings cannot be undone.</p>
            
            <p class="tip">Tip: You can reset individual categories of settings by clicking the "Reset" button in each category section.</p>
            """
        
        else:
            # Placeholder for other topics
            content = f"""
            <h1>{topic_name}</h1>
            <p>Documentation for {topic_name} will be available soon.</p>
            <p class="note">Note: This section is under development.</p>
            """
        
        # Wrap content in HTML document
        html_content = f"""
        <html>
        <head>
            <style>
                {css}
            </style>
        </head>
        <body>
            {content}
        </body>
        </html>
        """
        
        return html_content 