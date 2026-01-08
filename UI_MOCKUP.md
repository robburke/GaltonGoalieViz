# Galton's Goalie - UI Mockup & Wireframes
## Mark Rober Inspired Design

---

## Color Palette

### Primary Colors
- **Deep Blue (Primary)**: `#0A2463` - Main backgrounds, headers
- **Royal Blue (Accent)**: `#3E92CC` - Buttons, highlights, active states
- **Bright Cyan (Pop)**: `#1C77C3` - Data visualization, important info
- **Sky Blue (Secondary)**: `#5DADE2` - Secondary buttons, links

### Supporting Colors
- **Dark Navy (Background)**: `#071A2F` - App background, darkest areas
- **Slate**: `#2C3E50` - Panel backgrounds
- **White (Text)**: `#FFFFFF` - Primary text
- **Light Gray (Secondary Text)**: `#BDC3C7` - Labels, secondary info
- **Success Green**: `#27AE60` - Calibration success, positive actions
- **Warning Orange**: `#E67E22` - Recording indicator, warnings
- **Error Red**: `#C0392B` - Errors, critical alerts

### Data Visualization Gradient (for histogram & trails)
- **Cold (Low Probability)**: `#3498DB` (Blue)
- **Warm (Medium)**: `#9B59B6` (Purple)
- **Hot (High Probability)**: `#E74C3C` (Red-Orange)

---

## Layout Structure

```
┌────────────────────────────────────────────────────────────────────────────┐
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║  TOP BAR (60px height, gradient: #0A2463 → #071A2F)                ║    │
│  ║                                                                     ║    │
│  ║  🎲 GALTON'S GOALIE          Mode: Ultra-Long Exp    ⚙️ 📊 ● REC   ║    │
│  ║     v1.0                                            FPS: 60  0:45   ║    │
│  ╚════════════════════════════════════════════════════════════════════╝    │
│                                                                             │
│  ┌─────────────┐  ┌────────────────────────────────────────────────────┐  │
│  │             │  │                                                     │  │
│  │   SIDEBAR   │  │                                                     │  │
│  │   280px     │  │          MAIN VISUALIZATION AREA                   │  │
│  │   wide      │  │          (Camera Feed + Overlays)                  │  │
│  │             │  │                                                     │  │
│  │  (Glass     │  │          Full-screen immersive view                │  │
│  │   panel     │  │          Clean, minimal overlays                   │  │
│  │   semi-     │  │                                                     │  │
│  │   trans-    │  │          [Visualization content fills here]        │  │
│  │   parent)   │  │                                                     │  │
│  │             │  │                                                     │  │
│  │  Collap-    │  │                                                     │  │
│  │  sible ◀    │  │                                                     │  │
│  │             │  │                                                     │  │
│  └─────────────┘  └────────────────────────────────────────────────────┘  │
│                   ┌────────────────────────────────────────────────────┐  │
│                   │  BOTTOM PANEL (180px height, when visible)         │  │
│                   │  Elegant Histogram with Statistics                 │  │
│                   │  [Smooth bars, Gaussian overlay, clean labels]     │  │
│                   └────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Mockups

### 1. TOP BAR (Always Visible)

```
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  🎲 GALTON'S GOALIE       Mode: ✨ Ultra-Long Exp      [⚙️] [📊] [●REC]  ║
║     Science Edition                                    60 FPS   0:45      ║
║                                                                           ║
╚══════════════════════════════════════════════════════════════════════════╝
```

**Details:**
- **Left Side:**
  - App logo/icon (dice/ball icon)
  - App name in clean sans-serif (e.g., Roboto or Open Sans)
  - Subtle subtitle "Science Edition"

- **Center:**
  - Current mode indicator with icon
  - Color-coded by mode (Trails=orange, Long Exp=purple, Ultra=cyan)

- **Right Side:**
  - Icon buttons: Settings ⚙️, Stats 📊, Help ❓
  - Recording indicator (pulsing red dot when active) with timer
  - FPS counter (small, subtle)

**Styling:**
- Gradient background: `#0A2463` → `#071A2F`
- Semi-transparent backdrop blur
- Drop shadow for depth
- Height: 60px

---

### 2. LEFT SIDEBAR (Collapsible)

```
┌──────────────────────────────┐
│  ◀ COLLAPSE                  │  ← Collapse button (arrow flips when open)
├──────────────────────────────┤
│                              │
│  🎮 MODE SELECTION           │
│  ┌────────────────────────┐ │
│  │ 📊 Standard            │ │  ← Radio button style
│  │ 🌊 Motion Trails       │ │
│  │ 💫 Long Exposure       │ │
│  │ ✨ Ultra-Long Exp  ●   │ │  ← Active (filled circle)
│  └────────────────────────┘ │
│                              │
│  ⚙️ CONTROLS                 │
│  ┌────────────────────────┐ │
│  │ ▼ Detection            │ │  ← Collapsible sections
│  │   Cooldown    [====○] │ │  ← Custom slider
│  │   20 frames (0.7s)    │ │
│  │                        │ │
│  │   Sensitivity [==○==] │ │
│  │   30                   │ │
│  │                        │ │
│  │   Min Size    [===○=] │ │
│  │   100 px               │ │
│  │                        │ │
│  │ ▶ Visual               │ │
│  │ ▶ Recording            │ │
│  └────────────────────────┘ │
│                              │
│  📊 STATISTICS               │
│  ┌────────────────────────┐ │
│  │  Total Hits:  1,247    │ │
│  │  Camera:      #0       │ │
│  │  Session:     12:34    │ │
│  │                        │ │
│  │  Mean:    μ = 6.2      │ │
│  │  Std Dev: σ = 1.8      │ │
│  └────────────────────────┘ │
│                              │
│  🎬 ACTIONS                  │
│  ┌────────────────────────┐ │
│  │  [🎯 Calibrate]        │ │  ← Primary button
│  │  [🔄 Reset Data]       │ │  ← Secondary button
│  │  [💾 Export Session]   │ │
│  └────────────────────────┘ │
│                              │
│  ❓ HELP                     │
│  [Keyboard Shortcuts]        │
│  [Quick Start Guide]         │
│                              │
└──────────────────────────────┘
```

**Details:**
- **Width:** 280px (collapsed: 50px, just icons)
- **Background:** Semi-transparent `#2C3E50` with 20% opacity + backdrop blur
- **Borders:** Subtle glow effect on right edge (`#3E92CC` at 30% opacity)
- **Sections:** Collapsible accordions with smooth animations
- **Buttons:** Rounded corners (8px), gradient fills, hover effects
- **Sliders:** Custom-styled with circular handles, track shows fill color

---

### 3. MAIN VISUALIZATION AREA

**Standard Mode (with buckets):**
```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│                                                          │
│        [Camera feed shows Galton board]                 │
│                                                          │
│                                                          │
│        ┌────────────────────────────────┐              │
│        │  1   2   3   4   5   6   7  ...│  ← Bucket #s│
│        ├┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬┤              │
│        ││  ││  ││  ││  ││✨││  ││  ││  ││  ← Glow on │
│        ││  ││  ││  ││  ││  ││  ││  ││  ││    hit      │
│        └┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴┘              │
│         ↑ Goal region (subtle glow outline)             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Ultra-Long Exposure Mode (clean):**
```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│                                                          │
│                                                          │
│                                                          │
│        [Camera feed with ghostly trail overlay]         │
│        [Brighter in center, dimmer on edges]            │
│        [No buckets, no histogram - pure viz]            │
│                                                          │
│                                                          │
│                                                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Overlay Elements (Standard mode only):**
- **Goal Region:** Hair-thin glowing outline (cyan, 2px, 40% opacity)
- **Bucket Dividers:** Vertical dashed lines (1px, cyan, 20% opacity)
- **Bucket Numbers:** Small, elegant font above region (white, 60% opacity)
- **Hit Glow:** Animated particle burst + bucket highlight (fades over 0.5s)
- **Corner Markers:** Small animated brackets at goal region corners

---

### 4. BOTTOM HISTOGRAM PANEL (Toggleable)

```
┌────────────────────────────────────────────────────────────────────┐
│  📊 DISTRIBUTION HISTOGRAM                          [Gaussian Fit] │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│     │                      147                                     │
│ 200 │                       ██                                     │
│     │                       ██                                     │
│     │              124      ██      126                            │
│ 150 │               ██      ██      ██                             │
│     │               ██      ██      ██                             │
│     │        89     ██      ██      ██      91                     │
│ 100 │        ██     ██      ██      ██      ██                     │
│     │        ██     ██      ██      ██      ██                     │
│     │   52   ██     ██      ██      ██      ██   54                │
│  50 │   ██   ██     ██      ██      ██      ██   ██                │
│     │   ██   ██     ██      ██      ██      ██   ██   28    17    │
│   0 ├───██───██──┬──██──┬───██───┬──██──┬───██───██───██────██─── │
│       1   2   3   4   5   6   7   8   9  10  11                   │
│                                                                     │
│       ╭─────────────── Gaussian Curve ───────────────╮            │
│       │  μ = 6.1  |  σ = 1.9  |  n = 1,247           │            │
│       ╰──────────────────────────────────────────────╯            │
└────────────────────────────────────────────────────────────────────┘
```

**Details:**
- **Height:** 180px (collapsed: 0px with smooth slide animation)
- **Background:** Semi-transparent `#071A2F` with 85% opacity
- **Bars:**
  - Rounded tops (4px radius)
  - Gradient fill: Blue (edges) → Purple (mid) → Red-Orange (center)
  - Smooth shadow underneath
  - Count labels above each bar (white, 12px font)
  - Animated growth when values update (spring easing)

- **Gaussian Overlay:**
  - Dotted line (cyan, 2px) showing theoretical normal distribution
  - Toggle on/off with button in header

- **Grid Lines:**
  - Horizontal reference lines (subtle gray, 10% opacity)
  - Every 50 count increment

- **Statistics Box:**
  - Bottom center, glass morphism style
  - Shows μ (mean), σ (std dev), n (sample size)

---

### 5. CALIBRATION MODE OVERLAY

```
┌────────────────────────────────────────────────────────────────────┐
│  ╔════════════════════════════════════════════════════════════╗    │
│  ║                    Semi-transparent overlay                 ║    │
│  ║                    (80% opacity dark blue)                  ║    │
│  ║                                                             ║    │
│  ║          ┌─────────────────────────────────────┐           ║    │
│  ║          │                                      │           ║    │
│  ║          │   🎯  CALIBRATION - STEP 1 OF 2     │           ║    │
│  ║          │                                      │           ║    │
│  ║          │   Click the TOP-LEFT corner         │           ║    │
│  ║          │   of your goal region               │           ║    │
│  ║          │                                      │           ║    │
│  ║          │          ┌──┐                        │           ║    │
│  ║          │          │  │   ← Click here         │           ║    │
│  ║          │          └──┘                        │           ║    │
│  ║          │                                      │           ║    │
│  ║          │          [Cancel] [Skip to Step 2]  │           ║    │
│  ║          │                                      │           ║    │
│  ║          └─────────────────────────────────────┘           ║    │
│  ║                                                             ║    │
│  ║         Animated pulsing crosshair at mouse cursor         ║    │
│  ║                                                             ║    │
│  ╚════════════════════════════════════════════════════════════╝    │
└────────────────────────────────────────────────────────────────────┘
```

**Details:**
- **Full-screen overlay:** Dark blue (`#071A2F`) at 80% opacity
- **Instruction card:**
  - Centered, glass morphism effect
  - White text, large readable font (18px)
  - Icon indicating action (target 🎯)
  - Progress indicator (Step 1 of 2)

- **Visual feedback:**
  - Pulsing animated crosshair follows mouse
  - After first click, shows green checkmark and line to second point
  - Smooth transitions between steps

- **Buttons:**
  - Cancel (secondary, gray)
  - Skip/Next (primary, blue) - only if applicable

---

### 6. SETTINGS DIALOG (Modal)

```
┌────────────────────────────────────────────────────────────────────┐
│  ╔════════════════════════════════════════════════════════════╗    │
│  ║  ⚙️ SETTINGS                                          [X]   ║    │
│  ╠════════════════════════════════════════════════════════════╣    │
│  ║                                                             ║    │
│  ║  ┌─────┬─────────┬──────────┬──────────┬──────────┐        ║    │
│  ║  │ 🔍  │ 🎨      │ 🎬       │ 📁       │ ℹ️        │        ║    │
│  ║  │Detec│ Visual  │ Record   │ Export   │ About    │        ║    │
│  ║  └─────┴─────────┴──────────┴──────────┴──────────┘        ║    │
│  ║                                                             ║    │
│  ║  🔍 DETECTION SETTINGS                                      ║    │
│  ║  ┌───────────────────────────────────────────────────────┐ ║    │
│  ║  │                                                        │ ║    │
│  ║  │  Motion Threshold                                     │ ║    │
│  ║  │  ╭──────────────────────○──────────╮                 │ ║    │
│  ║  │  1                     30                        100  │ ║    │
│  ║  │  Lower = More Sensitive                               │ ║    │
│  ║  │                                                        │ ║    │
│  ║  │  Cooldown Period                                      │ ║    │
│  ║  │  ╭────────○──────────────────────────╮               │ ║    │
│  ║  │  1      20 frames (0.67s)         120                │ ║    │
│  ║  │  Prevent duplicate detections                         │ ║    │
│  ║  │                                                        │ ║    │
│  ║  │  Minimum Contour Area                                 │ ║    │
│  ║  │  ╭──────────○────────────────────────╮               │ ║    │
│  ║  │  10      100 pixels              1000                │ ║    │
│  ║  │  Filter out noise                                     │ ║    │
│  ║  │                                                        │ ║    │
│  ║  │  Presets:  [High Sens] [Standard] [Low Noise]        │ ║    │
│  ║  │                                                        │ ║    │
│  ║  └───────────────────────────────────────────────────────┘ ║    │
│  ║                                                             ║    │
│  ║                              [Reset to Defaults] [Apply]   ║    │
│  ╚════════════════════════════════════════════════════════════╝    │
└────────────────────────────────────────────────────────────────────┘
```

**Tab Sections:**
1. **Detection** (🔍): Threshold, cooldown, min size, presets
2. **Visual** (🎨): Colors, theme, overlay opacity, font size
3. **Recording** (🎬): Video format, quality, auto-save options
4. **Export** (📁): CSV format, screenshot settings, session naming
5. **About** (ℹ️): Version, credits, license, help links

---

### 7. HELP OVERLAY (Keyboard Shortcuts)

```
┌────────────────────────────────────────────────────────────────────┐
│  ╔════════════════════════════════════════════════════════════╗    │
│  ║  ❓ KEYBOARD SHORTCUTS                               [X]   ║    │
│  ╠════════════════════════════════════════════════════════════╣    │
│  ║                                                             ║    │
│  ║  ⌨️  GENERAL                                                ║    │
│  ║  ┌─────────────────────────────────────────────────────┐   ║    │
│  ║  │  H or ?          Show this help                     │   ║    │
│  ║  │  Q or ESC        Quit application                   │   ║    │
│  ║  │  Tab             Toggle sidebar                     │   ║    │
│  ║  │  F11             Fullscreen mode                    │   ║    │
│  ║  └─────────────────────────────────────────────────────┘   ║    │
│  ║                                                             ║    │
│  ║  🎮  MODES                                                  ║    │
│  ║  ┌─────────────────────────────────────────────────────┐   ║    │
│  ║  │  1               Standard mode                      │   ║    │
│  ║  │  2               Motion trails                      │   ║    │
│  ║  │  3               Long exposure                      │   ║    │
│  ║  │  4               Ultra-long exposure                │   ║    │
│  ║  │  T               Cycle modes                        │   ║    │
│  ║  └─────────────────────────────────────────────────────┘   ║    │
│  ║                                                             ║    │
│  ║  🎬  RECORDING                                              ║    │
│  ║  ┌─────────────────────────────────────────────────────┐   ║    │
│  ║  │  V               Start/stop recording               │   ║    │
│  ║  │  P or Space      Pause counting                     │   ║    │
│  ║  │  R               Reset data                         │   ║    │
│  ║  │  S               Save calibration                   │   ║    │
│  ║  └─────────────────────────────────────────────────────┘   ║    │
│  ║                                                             ║    │
│  ║  🎯  CALIBRATION                                            ║    │
│  ║  ┌─────────────────────────────────────────────────────┐   ║    │
│  ║  │  C               Enter calibration mode             │   ║    │
│  ║  │  0-9             Switch camera                      │   ║    │
│  ║  └─────────────────────────────────────────────────────┘   ║    │
│  ║                                                             ║    │
│  ║                                            [Close]          ║    │
│  ╚════════════════════════════════════════════════════════════╝    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Animation & Interaction Details

### Transitions
- **Mode switches:** 300ms fade with ease-in-out
- **Sidebar collapse:** 250ms slide with cubic-bezier easing
- **Panel show/hide:** 200ms slide-up/down
- **Button hover:** 150ms scale (1.0 → 1.05) + glow
- **Button click:** 100ms scale (1.05 → 0.95 → 1.0)

### Visual Effects
- **Glass morphism:**
  - Background: Semi-transparent white/dark with blur
  - Border: 1px semi-transparent white
  - Box shadow: Subtle, layered shadows for depth

- **Glow effects:**
  - Hit detection: Yellow/cyan glow, fades over 500ms
  - Active buttons: Cyan outer glow (4px blur)
  - Recording indicator: Pulsing red (1s cycle)

- **Particle effects:**
  - Ball hit: 5-8 particles burst radially, fade over 300ms
  - Mode switch: Subtle sparkle effect at icon

### Hover States
- **Buttons:** Scale up, brighten, add glow
- **Sliders:** Handle enlarges, track highlights
- **Tabs:** Underline animates in from center
- **Cards:** Lift up with shadow increase

---

## Typography

### Font Family
- **Primary:** "Roboto" or "Open Sans" (clean, modern sans-serif)
- **Monospace (for data):** "Fira Code" or "JetBrains Mono"

### Font Sizes
- **H1 (App Title):** 24px, Bold
- **H2 (Section Headers):** 18px, SemiBold
- **H3 (Subsections):** 14px, Medium
- **Body:** 13px, Regular
- **Small (Labels):** 11px, Regular
- **Stats/Data:** 16px, Monospace, Medium

---

## Responsive Behavior

### Sidebar States
1. **Expanded (default):** 280px wide
2. **Collapsed:** 50px wide (icons only, tooltips on hover)
3. **Hidden:** 0px (fullscreen viz mode)

### Bottom Panel States
1. **Visible (default):** 180px height
2. **Minimized:** 40px (title bar only)
3. **Hidden:** 0px (ultra-long exposure mode)

### Window Resize
- Maintains 16:9 aspect ratio for viz area when possible
- Sidebar and panels adjust smoothly
- Minimum window size: 1024x600

---

## Dark Theme Specifications

### Background Layers (from back to front)
1. **App background:** `#071A2F` (darkest navy)
2. **Panel backgrounds:** `#0A2463` (deep blue) at 60% opacity
3. **Card backgrounds:** `#2C3E50` (slate) at 40% opacity
4. **Hover/Active:** `#3E92CC` (royal blue) at 20% opacity

### Text Colors
- **Primary:** `#FFFFFF` (100%)
- **Secondary:** `#BDC3C7` (80%)
- **Disabled:** `#7F8C8D` (50%)
- **Links:** `#5DADE2` (bright cyan)

### Borders & Dividers
- **Default:** `#34495E` at 30% opacity
- **Active:** `#3E92CC` at 60% opacity
- **Glow:** `#1C77C3` with 8px blur

---

## Icon Set

Use **Feather Icons** or **Material Design Icons** for consistency:
- 🎲 Dice (logo)
- 📊 Bar chart (stats)
- 🌊 Wave (trails)
- 💫 Sparkles (long exp)
- ✨ Stars (ultra-long exp)
- ⚙️ Settings
- 🎯 Target (calibration)
- 🔄 Refresh (reset)
- 💾 Save
- 🎬 Video (recording)
- ❓ Help
- ⏸️ Pause
- ▶️ Play
- 📸 Camera

---

## Special Mode: Ultra-Long Exposure

### Visual Treatment
- **No overlays** except:
  - Top bar (can be hidden with `F11`)
  - Subtle mode indicator (top-right, fades after 3s)

- **Trail gradient options:**
  1. **Classic:** White → Cyan (brighter = more passes)
  2. **Fire:** Blue → Purple → Red → Yellow
  3. **Ocean:** Navy → Teal → Cyan → White
  4. **Monochrome:** Black → Gray → White

- **Density heatmap toggle:**
  - Color intensity mapped to probability density
  - Smoothed with Gaussian kernel for bell curve effect

- **Statistical overlay (optional toggle):**
  - Vertical line at mean (μ)
  - Shaded region showing ±1σ, ±2σ
  - Faint, non-intrusive, toggleable with 'I' key

---

## Export Options

### Session Data Package
When user clicks "Export Session":
```
galton_session_20250107_143022/
  ├── video.mp4              (recorded footage with overlays)
  ├── data.csv               (bucket counts, timestamps)
  ├── statistics.json        (μ, σ, n, config params)
  ├── histogram.png          (final distribution chart)
  ├── ultra_long_exp.png     (final accumulated visualization)
  └── session_metadata.json  (settings, calibration, duration)
```

---

## Implementation Notes for Qt

### Main Window Structure
```
QMainWindow
├── QMenuBar (File, Edit, View, Tools, Help)
├── Top Bar Widget (custom)
├── QHBoxLayout (main layout)
│   ├── Sidebar Widget (QWidget with QVBoxLayout)
│   └── QVBoxLayout (viz + histogram)
│       ├── Visualization Widget (QLabel for OpenCV frames)
│       └── Histogram Widget (custom QWidget with QPainter)
└── QStatusBar (optional, minimal)
```

### Key Qt Classes to Use
- **QTimer:** For frame updates (30-60 FPS)
- **QPropertyAnimation:** For smooth transitions
- **QGraphicsEffect:** For blur/shadow effects
- **QPainter:** For custom drawing (histogram, overlays)
- **QSettings:** For persistent config storage
- **QThread:** For video processing (keep UI responsive)

### Stylesheet Strategy
- Use QSS (Qt Style Sheets) for colors, borders, spacing
- Custom painting for complex visualizations
- Glass morphism via QGraphicsBlurEffect + semi-transparent backgrounds

---

## Final Notes

This design prioritizes:
✅ **Clarity** - Easy to understand at a glance
✅ **Functionality** - All existing features preserved
✅ **Aesthetics** - Mark Rober style science communication vibe
✅ **Professionalism** - Market-ready polish
✅ **Engagement** - Animations and feedback keep it interesting

---

**Ready for your approval!** 🎨

Once you give the go-ahead, I'll start implementing this beautiful Qt-based interface!
