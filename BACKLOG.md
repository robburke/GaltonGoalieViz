# Galton's Goalie - Feature Backlog

This file tracks feature requests, improvements, and bug fixes for the Galton's Goalie application.

## Status Legend
- 🔴 **TODO** - Not started
- 🟡 **IN PROGRESS** - Currently being worked on
- 🟢 **DONE** - Completed

---

## Backlog Items

---

### 🟡 Change title from ALLCAPS to Regular Caps
**Priority:** Medium
**Description:** So it's Galton's Goalie, not GALTON'S GOALIE



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

---

## How to Use This File

1. Add new tasks under "Backlog Items" with 🔴 status
2. When starting work on a task, change status to 🟡
3. When complete, change status to 🟢 and move to "Completed Items"
4. Feel free to add priority, requirements, and affected files for each task
