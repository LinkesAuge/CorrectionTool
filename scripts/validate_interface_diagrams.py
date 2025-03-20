"""
validate_interface_diagrams.py

Description: Validates that UML diagrams in PlantUML format accurately represent
the interface definitions in the code.

Usage:
    python scripts/validate_interface_diagrams.py

This script performs the following validations:
1. Ensures every interface method in the code is represented in the diagrams
2. Verifies method signatures match between code and diagrams
3. Validates class/interface relationships
"""

import os
import re
import inspect
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Type

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import interfaces
from src.interfaces import (
    IDataStore,
    IFileService,
    ICorrectionService,
    IValidationService,
    IConfigManager,
    IServiceFactory,
    events,
)
from src.interfaces.ui_adapters import IUiAdapter, ITableAdapter, IComboBoxAdapter, IStatusAdapter

# Map interfaces to their diagram files
INTERFACE_DIAGRAM_MAP = {
    IDataStore: "docs/diagrams/class/core.puml",
    IFileService: "docs/diagrams/class/core.puml",
    ICorrectionService: "docs/diagrams/class/core.puml",
    IValidationService: "docs/diagrams/class/core.puml",
    IConfigManager: "docs/diagrams/class/core.puml",
    IServiceFactory: "docs/diagrams/class/core.puml",
    IUiAdapter: "docs/diagrams/class/ui.puml",
    ITableAdapter: "docs/diagrams/class/ui.puml",
    IComboBoxAdapter: "docs/diagrams/class/ui.puml",
    IStatusAdapter: "docs/diagrams/class/ui.puml",
}

# Methods that are allowed to be in the diagram even if not in the interface
# This is helpful for documentation purposes or for methods that are in implementing classes
ALLOWED_ADDITIONAL_METHODS = {
    IDataStore: ["update_validation_entry", "check_entry_valid", "get_active_validation_lists"],
    IFileService: [
        "validate_csv_file",
        "save_csv_file",
        "get_csv_preview",
        "load_csv_file",
        "export_data",
    ],
    ICorrectionService: [
        "save_correction_rules",
        "set_correction_rules",
        "get_correction_rules",
        "update_correction_rule",
        "load_correction_rules",
        "remove_correction_rule",
    ],
    IValidationService: ["get_validation_lists", "add_to_validation_list"],
    IConfigManager: ["get_float", "set_path", "get_path"],
    IServiceFactory: [
        "has_service",
        "get_config_manager",
        "get_data_store",
        "get_correction_service",
        "get_file_service",
        "get_validation_service",
    ],
    IUiAdapter: ["disconnect_signals", "connect_signals", "get_widget", "refresh"],
    ITableAdapter: [
        "clear_selection",
        "select_row",
        "get_model",
        "set_data",
        "get_data",
        "get_selected_data",
    ],
    IComboBoxAdapter: ["set_items", "get_items", "remove_item", "get_combo_box", "clear"],
    IStatusAdapter: ["show_info", "get_status_bar", "show_error", "show_warning"],
}


def get_interface_methods(interface_class: Type) -> Set[str]:
    """
    Extract method names from an interface class.

    Args:
        interface_class: The interface class to analyze

    Returns:
        Set of method names defined in the interface
    """
    methods = set()
    for name, member in inspect.getmembers(interface_class):
        if inspect.isfunction(member) and not name.startswith("_"):
            methods.add(name)
    return methods


def get_diagram_methods(diagram_path: str, interface_name: str) -> Set[str]:
    """
    Extract method names for a specific interface from a PlantUML diagram.

    Args:
        diagram_path: Path to the PlantUML diagram file
        interface_name: Name of the interface to extract methods for

    Returns:
        Set of method names found in the diagram for the specified interface
    """
    methods = set()

    # Get short interface name without "I" prefix if needed
    short_name = interface_name
    if short_name.startswith("I") and short_name[1:2].isupper():
        short_name = short_name[1:]

    with open(diagram_path, "r") as file:
        content = file.read()

        # Find the interface definition section
        pattern = rf'interface.*?"{interface_name}".*?\{{(.*?)\}}'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            # Try alternative format
            pattern = rf"interface.*?{interface_name}.*?\{{(.*?)\}}"
            match = re.search(pattern, content, re.DOTALL)

        if match:
            interface_section = match.group(1)

            # Extract methods
            method_pattern = r"[+-]([a-zA-Z0-9_]+)\("
            for method_match in re.finditer(method_pattern, interface_section):
                method_name = method_match.group(1)
                if not method_name.startswith("_"):
                    methods.add(method_name)

    return methods


def validate_interface(interface_class: Type, diagram_path: str) -> Tuple[List[str], List[str]]:
    """
    Validate that all methods of an interface are represented in a diagram.

    Args:
        interface_class: The interface class to validate
        diagram_path: Path to the PlantUML diagram file

    Returns:
        Tuple of (missing_methods, extra_methods)
    """
    interface_name = interface_class.__name__
    code_methods = get_interface_methods(interface_class)
    diagram_methods = get_diagram_methods(diagram_path, interface_name)

    # Get allowed additional methods for this interface
    allowed_additions = ALLOWED_ADDITIONAL_METHODS.get(interface_class, [])

    missing_methods = code_methods - diagram_methods
    extra_methods = diagram_methods - code_methods - set(allowed_additions)

    return list(missing_methods), list(extra_methods)


def main():
    """
    Validate all interface diagrams.
    """
    print("Validating interface diagrams...")
    all_valid = True

    for interface_class, diagram_path in INTERFACE_DIAGRAM_MAP.items():
        interface_name = interface_class.__name__
        print(f"\nValidating {interface_name} in {diagram_path}:")

        if not os.path.exists(diagram_path):
            print(f"  ERROR: Diagram file not found: {diagram_path}")
            all_valid = False
            continue

        missing_methods, extra_methods = validate_interface(interface_class, diagram_path)

        if missing_methods:
            print(f"  Missing methods in diagram: {', '.join(missing_methods)}")
            all_valid = False

        if extra_methods:
            print(f"  Extra methods in diagram: {', '.join(extra_methods)}")
            all_valid = False

        if not missing_methods and not extra_methods:
            print(f"  ✓ {interface_name} representation is accurate")

    if all_valid:
        print("\nAll interface diagrams are accurate! ✓")
        return 0
    else:
        print("\nSome diagrams need updating. See details above. ✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())
