# Custom Fonts for Galton's Goalie

This directory contains custom fonts used by the application.

## Required Fonts

### Campton (Headings)
- **Used for**: App title, section headers, labels, tab names
- **Download from**:
  - Purchase from: https://www.myfonts.com/collections/campton-font-rene-bieder
  - Free alternative: Use Montserrat (already in fallback chain)

**Files needed:**
- `Campton-Bold.otf` or `Campton-Bold.ttf`
- `Campton-Medium.otf` or `Campton-Medium.ttf` (optional)

### Open Sans (Body Text)
- **Used for**: All body text, descriptions, labels
- **Download from**: https://fonts.google.com/specimen/Open+Sans (Free)

**Files needed:**
- `OpenSans-Regular.ttf`
- `OpenSans-Bold.ttf`
- `OpenSans-SemiBold.ttf` (optional)

## Installation

1. Download the font files (.ttf or .otf format)
2. Place them in this `fonts/` directory
3. Run the application - fonts will load automatically
4. You should see console output like:
   ```
   Loaded font: Campton from Campton-Bold.otf
   Loaded font: Open Sans from OpenSans-Regular.ttf
   ```

## Fallback Fonts

If custom fonts aren't installed, the app uses these fallbacks:
- **Headings**: Montserrat → Arial Black → sans-serif
- **Body**: Segoe UI → Arial → sans-serif

## File Structure

```
GaltonGoalieViz/
├── galton_goalie_qt.py
├── fonts/
│   ├── README.md (this file)
│   ├── Campton-Bold.otf        # Add these files
│   ├── OpenSans-Regular.ttf    # Add these files
│   └── OpenSans-Bold.ttf       # Add these files
```

## Free Alternatives

If you want similar fonts for free:
- **Instead of Campton**: Download **Montserrat** from Google Fonts
  - https://fonts.google.com/specimen/Montserrat
- **Instead of Open Sans**: Already free! Download from Google Fonts
  - https://fonts.google.com/specimen/Open+Sans

Both are excellent Mark Rober-style fonts and work perfectly with the app!
