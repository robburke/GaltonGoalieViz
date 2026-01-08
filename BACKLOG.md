# Galton's Goalie - Feature Backlog

This file tracks feature requests, improvements, and bug fixes for the Galton's Goalie application.

## Status Legend
- 🔴 **TODO** - Not started
- 🟡 **IN PROGRESS** - Currently being worked on
- 🟢 **DONE** - Completed

---

## Backlog Items

*(All items completed!)*


## Completed Items

### 🟢 Settings Menu - ensure startup settings work correctly
**Priority:** Medium
**Description:** can you please check to make sure all the UI in the Settings menu populates correctly on load? for instance, I notice the "Show bucket dividers on video feed" starts checked even if it should be not checked on load.
**Completed:** Fixed - Settings dialog now properly loads current state from video thread and histogram widget instead of defaulting to hardcoded values.

### 🟢 Keyboard shortcuts - make sure these work correctly
**Priority:** Medium
**Description:** Pressing 1, 2, 3, 4 does not seem to properly change the mode. can you please fix this.
**Completed:** Fixed - Changed keyboard shortcuts from setChecked() to click() so they properly trigger the mode change event.

### 🟢 Camera feature - allow flip horizontally
**Priority:** Medium
**Description:** Add a feature to the camera menu enabling horizontal flip
**Completed:** Added checkbox in Camera tab of Settings dialog. Flip is applied using cv2.flip(frame, 1) and persisted to config file.

### 🟢 Make mean, std dev, n on the graph a toggle
**Priority:** Medium
**Description:** Add a feature showing/hiding the statistics on the main histogram. It's fine to keep them on the sidebar
**Completed:** Added checkbox in Display Overlays settings. Statistics text on histogram can now be toggled on/off while keeping sidebar stats visible.

### 🟢 Move statistics on the sidebar below the Actions
**Priority:** Medium
**Description:** Actions group should be above Statistics group.
**Completed:** Reordered sidebar groups - Actions now appears before Statistics.

### 🟢 Change title from ALLCAPS to Regular Caps
**Priority:** Medium
**Description:** So it's Galton's Goalie, not GALTON'S GOALIE
**Completed:** Changed all titles from ALLCAPS to Regular Caps: "Galton's Goalie", "Mode Selection", "Controls", "Actions", "Statistics", and help dialog categories.

### 🟢 Add keyboard shortcut P for Pause
**Priority:** Medium
**Description:** Pause function can be activated with P key
**Completed:** Added P key as alternative to Space for pause/resume. Updated help dialog to show "Space / P" for pause.

### 🟢 Add keyboard shortcuts to button labels
**Priority:** Medium
**Description:** Help is right, the button says Help (H). Also add Pause (P), Reset Data (R), Start Recording (V), Calibrate (C)
**Completed:** Added keyboard shortcuts to all action buttons: Calibrate (C), Pause (P), Reset Data (R), Export Session (E), Start Recording (V). Shortcuts dynamically update when button text changes (e.g., Resume (P), Stop Recording (V)).

### 🟢 Visualize Pause
**Priority:** Medium
**Description:** When Paused there's no indicator. provide some UI on the video feed, maybe the traditional pause symbol of two boxes, indicating that the functionality is paused.
**Completed:** Added pause overlay on video feed showing two white vertical bars (pause symbol) with semi-transparent white background and "PAUSED" text. Overlay only appears when paused and doesn't get recorded to video files.

### 🟢 Fix Reset Dialog Box and keyboard shortcut box color schemes
**Priority:** Medium
**Description:** The reset data popup and the keyboard shortcut box has text that is unreadable.. white on light grey in the dialog, and light grey on white in the keyboard shortcuts .. please fix that.
**Completed:** Created create_styled_message_box() helper function with dark theme styling (dark blue background #071A2F, white text, styled buttons). Applied to all QMessageBox dialogs throughout the app for consistent dark theme. Help dialog already had proper styling.

---

## How to Use This File

1. Add new tasks under "Backlog Items" with 🔴 status
2. When starting work on a task, change status to 🟡
3. When complete, change status to 🟢 and move to "Completed Items"
4. Feel free to add priority, requirements, and affected files for each task
