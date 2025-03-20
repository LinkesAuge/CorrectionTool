# Product Context: Chest Tracker Correction Tool

## Problem Statement
Players of the browser game "Total Battle" collect various types of chests during gameplay. The game doesn't provide a native way to export this data, so players use OCR (Optical Character Recognition) to extract the chest information from screenshots. This OCR process introduces errors such as:

- Incorrect character recognition (e.g., "VV" instead of "W")
- Unicode character confusion (e.g., Cyrillic characters mistaken for Latin)
- Inconsistent name formats
- Missing apostrophes or special characters
- Case sensitivity issues

Without correction, these errors make it difficult to:
- Track player contributions accurately
- Maintain consistent records
- Generate reliable statistics
- Identify patterns in chest distribution

## User Needs
Players and clan leaders need a tool that allows them to:
1. Quickly process OCR-extracted chest data
2. Correct common OCR errors automatically
3. Validate the data against known valid values
4. Manage player names, chest types, and source locations
5. Export clean, corrected data for further analysis

## User Experience Goals
- **Efficiency**: Users should be able to process large batches of chest data with minimal manual intervention
- **Clarity**: Error highlighting and validation should be intuitive and visible
- **Flexibility**: Support for both automatic and manual corrections
- **Reliability**: Consistent correction of known errors
- **Extensibility**: Easy addition of new correction rules and validation lists

## Data Flow
1. User captures chest data from the game using screenshots
2. An external OCR tool converts these screenshots to text
3. The text file is imported into the Chest Tracker Correction Tool
4. The tool applies correction rules to fix known OCR errors
5. The tool validates the entries against known valid values
6. The user can manually correct any remaining errors
7. The corrected data is exported for use in spreadsheets or other tracking tools

## Typical Entry Format
Each chest entry in the raw OCR output follows a specific pattern:

```
Chest Type
From: Player Name
Source: Location
```

For example:
```
Cobra Chest
From: Engelchen
Source: Level 15 Crypt
```

## Correction Process
1. **Loading**: The raw OCR text file is parsed into structured entries
2. **Validation**: Each entry is checked against validation lists for players, chest types, and sources
3. **Correction**: Known error patterns are replaced according to the correction rules
4. **Fuzzy Matching**: For entries that don't exactly match validation lists, fuzzy matching suggests the closest valid values
5. **Manual Editing**: Users can edit entries directly in the table view
6. **Exporting**: The corrected data is written back to a text file preserving the original format

## User Profiles
- **Clan Leaders**: Track contributions from all clan members, manage correction rules
- **Record Keepers**: Maintain documentation of chest sources and types
- **Regular Players**: Correct their own chest data before submitting to clan leaders

## Integration Context
This tool is part of a larger chest tracking ecosystem that may include:
- OCR screenshot tools for initial data extraction
- Spreadsheets for long-term tracking and analysis
- Discord bots for sharing statistics with clan members

The Chest Tracker Correction Tool specifically addresses the gap between raw OCR output and clean data suitable for analysis. 