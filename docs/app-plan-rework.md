# Chest Tracker Correction Tool - Rework Plan

## Overview

This document outlines the comprehensive plan for reworking the Chest Tracker Correction Tool. The current application has several issues including inconsistent correction application, redundant UI, confusing workflow, and incomplete fuzzy matching implementation. This rework aims to create a more intuitive, efficient, and visually appealing application.

## Current Issues

1. **Inconsistent Correction Application**
   - Apply Corrections button initially disabled
   - Corrections sometimes require multiple attempts in different orders
   - Auto-apply toggle doesn't work consistently

2. **Redundant UI Structure**
   - Multiple tabs with overlapping functionality (Dashboard, File Management, Corrections)
   - Inefficient use of screen space
   - Preview panel adds complexity without sufficient benefit

3. **Inefficient Validation/Correction Management**
   - Validation lists in separate tabs
   - Too much space for simple elements like list names
   - No direct editing of entries
   - No drag-and-drop functionality

4. **Incomplete Fuzzy Matching**
   - `FuzzyMatcher` service exists but isn't properly integrated with validation
   - UI has settings for "Relaxed (Fuzzy match)" but they aren't connected to actual functionality
   - Missing UI controls for enabling/disabling fuzzy matching and adjusting threshold
   - No visual feedback for fuzzy matches vs. exact matches
   - Missing correction suggestions based on fuzzy matches

5. **Visual Design Issues**
   - Lack of consistent styling
   - Large empty black backgrounds
   - Oversized buttons
   - Missing visual feedback for operations

## Rework Architecture

### Application Structure

We will simplify the application to have just two main tabs:

1. **Dashboard** - Primary workspace for viewing and correcting entries
2. **Correction Manager** - For managing validation lists and correction rules

### Dashboard Design

The Dashboard will be redesigned with a more efficient layout:

- **Left Sidebar (25-30% width)**
  - File import section (more compact)
  - Statistics display
  - Action buttons (vertical group)
  - Filter controls (dropdowns from validation lists)
  - Auto-apply toggle (enabled by default)
  - **Fuzzy matching controls** (toggle and threshold slider)

- **Main Content (70-75% width)**
  - Enhanced table view with:
    - Color-coded cells for validation errors
    - Field-specific error highlighting
    - Distinct highlighting for fuzzy matches
    - In-place editing
    - Right-click context menu for quick corrections
  - Status bar with operation feedback

### Correction Manager Design

The Correction Manager will have a split layout:

- **Left Side (50% width)**
  - Correction rules table (From → To columns)
  - Add/Edit/Delete buttons
  - Import/Export controls
  - Search/filter functionality
  - Drag-and-drop target area
  - **Fuzzy match suggestion section**

- **Right Side (50% width)**
  - Three compact validation list sections (stacked vertically)
    - Player List
    - Chest Type List
    - Source List
  - Each with:
    - Compact table view
    - Direct editing capability
    - Import/Export buttons
  - Bottom section for common controls

## Functional Improvements

### Validation System

- **Automatic Validation**
  - Validate entries automatically on load
  - Provide clear visual indicators for validation errors
  - Highlight specific fields with errors (player, chest type, source)
  - Field-specific coloring (e.g., player errors in blue, chest type in green, source in orange)

- **Manual Validation**
  - Allow re-validation after changes
  - Clear status indicators for validation results

- **Fuzzy Validation**
  - Support multiple validation strictness levels:
    - Strict: Exact matches only
    - Moderate: Case-insensitive matches
    - Relaxed: Fuzzy matches based on similarity threshold
  - Visual distinction between exact and fuzzy matches
  - Confidence score display for fuzzy matches
  - User-configurable fuzzy matching threshold

### Correction System

- **Auto-Apply Corrections**
  - Toggle enabled by default
  - Apply corrections immediately when files are loaded
  - Provide visual feedback when corrections are applied

- **Manual Corrections**
  - Always-enabled Apply Corrections button when correction list exists
  - Right-click context menu for quick corrections
  - In-place editing of table entries
  - Option to add corrections to the correction list

- **Fuzzy Match Corrections**
  - Suggest corrections based on fuzzy matches to validation lists
  - Display confidence scores for suggestions
  - One-click application of suggested corrections
  - Option to add applied fuzzy corrections to correction rules

### Drag-and-Drop Functionality

- Drag entries from validation lists to correction rules
- Drag between validation lists
- Visual feedback during drag operations
- Confirmation dialog for creating new entries

### Filter Improvements

- Dropdown filters populated from validation lists
- Multi-select filtering
- Search within filters
- Persistence of filter state

## Fuzzy Matching Implementation Details

### FuzzyMatcher Service Enhancement

The existing `FuzzyMatcher` class will be enhanced to:

1. **Improve Performance**
   - Add caching for repeated comparisons
   - Optimize for large validation lists
   - Implement batch processing capabilities

2. **Enhance Functionality**
   - Add methods for providing correction suggestions
   - Support for different matching algorithms (token sort ratio, partial ratio, etc.)
   - Configurable match type based on validation settings

3. **Integrate with Validation**
   - Connect to `ValidationList.is_valid()` method
   - Store and provide confidence scores
   - Track matching method used (exact, case-insensitive, fuzzy)

### UI Integration

1. **Dashboard Controls**
   - Toggle switch for enabling/disabling fuzzy matching
   - Threshold slider (0.0-1.0) with visual feedback
   - Presets for common threshold values (0.75, 0.85, 0.95)

2. **Settings Panel Integration**
   - Connect "Validation Strictness" setting to fuzzy matching behavior
   - Add detailed configuration options for fuzzy matching
   - Allow customization of match algorithms

3. **Visual Feedback**
   - Different highlight colors for exact vs. fuzzy matches
   - Tooltips showing match details and confidence scores
   - Suggestion indicators for potential corrections

### Validation Process

1. The validation process will work as follows:

   a. **Exact Match Check**
      - First, check if the entry exactly matches any validation list entry
      - If match found, mark as valid with 100% confidence

   b. **Case-Insensitive Check** (if strictness allows)
      - If no exact match, check for case-insensitive matches
      - If match found, mark as valid with high confidence

   c. **Fuzzy Match Check** (if enabled and strictness allows)
      - If no previous matches and fuzzy matching is enabled
      - Calculate similarity scores against validation list entries
      - If any score exceeds threshold, mark as valid with the confidence score
      - Store the best match for correction suggestions

2. **Results Presentation**
   - Clear visual distinction between validation methods
   - Confidence score display for fuzzy matches
   - Quick-action buttons for applying suggested corrections

## Visual Design Improvements

### Color Scheme

- Main background: Dark theme with reduced solid black
- Accent: Consistent golden highlights for important elements
- Text: Improved contrast and readability
- Validation errors: Color-coded by field type
- **Fuzzy matches**: Distinguished from exact matches with different highlight color

### UI Elements

- Modern, appropriately sized buttons with icons
- Consistent spacing and padding
- Responsive layouts
- Custom styled tables
- Subtle animations for state changes
- Improved scrollbars and selection highlighting

## Workflow Improvements

### Data Loading

1. User loads input file (TXT)
2. User loads correction list (CSV)
3. Automatic validation occurs
4. Corrections applied automatically (if toggle enabled)
5. Status updates shown with clear visual feedback

### Correction Process

1. Invalid entries highlighted in table with field-specific colors
2. User can edit directly in the table
3. User can right-click for quick correction options
4. Corrections can be added to the correction list
5. Apply Corrections button provides immediate feedback

### Fuzzy Matching Workflow

1. User enables fuzzy matching if desired
2. Validation automatically includes fuzzy matching
3. Fuzzy matches are visually distinguished from exact matches
4. User can see confidence scores and suggested corrections
5. User can apply suggestions with one click
6. Applied suggestions can be added to correction rules

### Validation List Management

1. User navigates to Correction Manager
2. User can directly edit validation lists
3. Changes reflected immediately in filters
4. Import/Export functionality for all lists

### Correction Rules Management

1. User adds rules via form or direct editing
2. Drag-and-drop from validation lists
3. Rules applied immediately or on demand
4. Search/filter for finding specific rules

## Implementation Approach

We will follow a phased implementation approach:

1. **Preliminary Cleanup**
   - Remove redundant components
   - Prepare codebase for new structure

2. **Dashboard Redesign**
   - Implement new layout
   - Enhance table functionality

3. **Correction Manager Implementation**
   - Create new interface
   - Implement validation list management

4. **Fuzzy Matching Implementation**
   - Enhance FuzzyMatcher service
   - Integrate with validation system
   - Add UI controls and feedback

5. **Advanced Features**
   - Add drag-and-drop
   - Improve filters
   - Enhance visual design

6. **Testing & Polishing**
   - Ensure consistent behavior
   - Optimize performance
   - Final UI adjustments

## Technology Considerations

- Continue using PySide6 for the UI
- Implement custom delegates for table functionality
- Use Qt's built-in drag-and-drop system
- Leverage QSS for styling improvements
- Consider QGraphicsEffects for visual feedback
- Use fuzzywuzzy library for text similarity

## Success Criteria

The rework will be considered successful when:

1. Corrections are applied consistently and predictably
2. The UI is intuitive and efficient
3. Validation errors are clearly indicated with field-specific information
4. Fuzzy matching is properly integrated and helpful for users
5. Users can easily manage validation lists and correction rules
6. The application has a modern, visually appealing design
7. All operations provide clear feedback
8. The application performs well with large datasets 