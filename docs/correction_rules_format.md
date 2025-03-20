# Correction Rules Format Specification

## Overview
This document specifies the standard format for correction rules used in the Chest Tracker Correction Tool. The correction rules system is designed to correct OCR errors and standardize data entries by applying text string replacements.

## File Format
Correction rules are stored in CSV (Comma-Separated Values) files with the following characteristics:

- UTF-8 encoding
- Standard CSV format with comma (,) as the delimiter
- First row contains column headers

## Standard Columns
The standard format includes the following columns:

| Column Name | Description | Required | Default Value |
|-------------|-------------|----------|--------------|
| From | Text string to be replaced | Yes | - |
| To | Replacement text string | Yes | - |
| Category | Category the rule applies to (chest, player, source, general) | No | "text" |
| Enabled | Whether the rule is enabled (true/false) | No | true |

## Internal Representation
Internally, the application uses the following column naming:

- `from_text` - Text to replace
- `to_text` - Replacement text
- `category` - Category the rule applies to
- `enabled` - Whether the rule is enabled

The system automatically handles the conversion between the user-friendly format ("From", "To") and the internal format during import and export operations.

## Example
Here's an example of a valid correction rules CSV file:

```csv
From,To,Category,Enabled
Маһоп12,D4rkBlizZ4rD,player,true
АЙ,D4rkBlizZ4rD,player,true
"Fenrir""s Chest",Fenrir's Chest,chest,true
"Hermes"" Store",Hermes' Store,source,true
"VVarrior""s Chest",Warrior's Chest,chest,true
Clan vvealth,Clan wealth,general,true
```

## Usage Notes
1. Rules are applied based on exact string matching by default
2. Category determines where the rule is applied:
   - "player": Only applied to player fields
   - "chest": Only applied to chest type fields
   - "source": Only applied to source fields
   - "general": Applied to all fields
3. Disabled rules (Enabled = false) are stored but not applied during correction
4. Special characters and quotes should be properly escaped in CSV format

## Backward Compatibility
For backward compatibility, the system will automatically convert older formats with different column names:

- "From" → "from_text"
- "To" → "to_text"
- "Category" → "category"

However, all newly created files will use the standard format specified above. 