"""
generate_puml_diagrams.py

Description: Generates PNG and SVG files from PlantUML source files.
Requires the PlantUML jar file to be downloaded. The script will download
it automatically if not found.

Usage:
    python scripts/generate_puml_diagrams.py [--format png|svg] [--output-dir docs/diagrams/images]
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import urllib.request
import platform
import shutil

# Default settings
PLANTUML_JAR_URL = "https://sourceforge.net/projects/plantuml/files/plantuml.jar/download"
DEFAULT_JAR_PATH = "scripts/lib/plantuml.jar"
DEFAULT_OUTPUT_DIR = "docs/diagrams/images"


def ensure_plantuml_jar(jar_path):
    """
    Ensure that the PlantUML jar file exists, downloading it if necessary.

    Args:
        jar_path: Path where the jar file should be located

    Returns:
        Path to the PlantUML jar file
    """
    jar_path = Path(jar_path)

    if not jar_path.exists():
        print(f"PlantUML jar not found at {jar_path}. Downloading...")

        # Create directories if they don't exist
        jar_path.parent.mkdir(parents=True, exist_ok=True)

        # Download the jar file
        try:
            urllib.request.urlretrieve(PLANTUML_JAR_URL, jar_path)
            print(f"PlantUML jar downloaded to {jar_path}")
        except Exception as e:
            print(f"Error downloading PlantUML jar: {e}")
            print("Please download it manually from: https://plantuml.com/download")
            sys.exit(1)

    return jar_path


def find_puml_files():
    """
    Find all .puml files in the diagrams directory.

    Returns:
        List of paths to .puml files
    """
    diagrams_dir = Path("docs/diagrams")
    puml_files = []

    for subdir in ["class", "sequence", "component", "di", "events"]:
        subdir_path = diagrams_dir / subdir
        if subdir_path.exists():
            puml_files.extend(list(subdir_path.glob("*.puml")))

    return puml_files


def check_java_installation():
    """
    Check if Java is installed and available in the PATH.

    Returns:
        bool: True if Java is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode == 0:
            print("Java is installed and available.")
            return True
        else:
            print("Java check failed with return code:", result.returncode)
            return False
    except Exception as e:
        print(f"Error checking Java installation: {e}")
        return False


def generate_diagram(puml_file, output_dir, format="png", jar_path=DEFAULT_JAR_PATH):
    """
    Generate a diagram from a PlantUML file.

    Args:
        puml_file: Path to the PlantUML file
        output_dir: Directory where the output should be saved
        format: Output format (png or svg)
        jar_path: Path to the PlantUML jar file

    Returns:
        Path to the generated diagram file
    """
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine output file path
    rel_path = Path(puml_file).relative_to(Path("docs/diagrams"))
    output_subdir = output_dir / rel_path.parent
    output_subdir.mkdir(parents=True, exist_ok=True)

    output_file = output_subdir / f"{rel_path.stem}.{format}"

    # Convert jar_path and puml_file to absolute paths
    abs_jar_path = Path(jar_path).absolute()
    abs_puml_file = Path(puml_file).absolute()
    abs_output_dir = output_subdir.absolute()

    # Command to generate the diagram
    cmd = [
        "java",
        "-jar",
        str(abs_jar_path),
        "-t" + format,
        "-output",
        str(abs_output_dir),
        str(abs_puml_file),
    ]

    print(f"Generating {format} for {puml_file}...")
    print(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Command output: {result.stdout}")
        if result.stderr:
            print(f"Command error: {result.stderr}")

        # Check if the output file was created
        if output_file.exists():
            print(f"  Generated: {output_file}")
            return output_file
        else:
            print(f"  Error: Output file not created at {output_file}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"  Error running PlantUML command: {e}")
        if e.stdout:
            print(f"  Command output: {e.stdout}")
        if e.stderr:
            print(f"  Command error: {e.stderr}")
        return None
    except Exception as e:
        print(f"  Error generating diagram: {e}")
        return None


def main():
    """
    Main function to generate diagrams from PlantUML files.
    """
    parser = argparse.ArgumentParser(description="Generate diagrams from PlantUML files")
    parser.add_argument(
        "--format", choices=["png", "svg"], default="png", help="Output format (default: png)"
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--jar-path",
        default=DEFAULT_JAR_PATH,
        help=f"Path to PlantUML jar (default: {DEFAULT_JAR_PATH})",
    )

    args = parser.parse_args()

    # Check if Java is installed
    if not check_java_installation():
        print(
            "Java is required to run PlantUML. Please install Java and make sure it's in your PATH."
        )
        return 1

    # Make sure we have the PlantUML jar
    jar_path = ensure_plantuml_jar(args.jar_path)

    # Find all .puml files
    puml_files = find_puml_files()

    if not puml_files:
        print("No .puml files found in the diagrams directory.")
        return 1

    print(f"Found {len(puml_files)} .puml files.")

    # Generate diagrams
    success_count = 0
    for puml_file in puml_files:
        output_file = generate_diagram(
            puml_file, args.output_dir, format=args.format, jar_path=jar_path
        )
        if output_file:
            success_count += 1

    print(
        f"Diagram generation complete. Successfully generated {success_count} of {len(puml_files)} diagrams."
    )
    return 0 if success_count == len(puml_files) else 1


if __name__ == "__main__":
    sys.exit(main())
