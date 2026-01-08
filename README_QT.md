# Galton's Goalie - Qt Professional Edition

🎲 **A beautiful, market-ready visualization tool for exploring the Central Limit Theorem through a physical Galton board.**

---

## ✨ What's New in Version 2.0

This is a **complete redesign** with a professional Qt-based interface, featuring:

- 🎨 **Mark Rober-inspired design** - Deep blue color scheme, clean typography, professional polish
- 🖥️ **Modern UI** - Glass morphism effects, smooth gradients, intuitive layout
- 📊 **Enhanced histogram** - Gaussian curve overlay, color-coded bars, real-time statistics
- ⚡ **Responsive performance** - Multi-threaded video processing keeps UI smooth
- 🎯 **Live statistics** - Mean (μ), standard deviation (σ), sample size (n)
- 💾 **Export functionality** - Save session data as CSV for further analysis
- 🎬 **Recording** - Built-in video recording with visual indicator
- ✨ **Ultra-Long Exposure mode** - Ghostly trails that naturally form a bell curve

---

## 📦 Requirements

```bash
pip install PyQt5 opencv-python numpy
```

**Tested on:**
- Python 3.8+
- Windows 10/11
- Camera/webcam required

---

## 🚀 Quick Start

### Running the Application

```bash
python galton_goalie_qt.py
```

### First-Time Setup

1. **Launch the app** - The camera feed will appear automatically
2. **Calibrate** (optional) - Click "🎯 Calibrate" to set your goal region
3. **Adjust sensitivity** - Use the sliders to fine-tune detection
4. **Select mode** - Choose visualization style (Standard, Trails, Long Exposure, Ultra-Long Exp)
5. **Drop balls** - Watch the histogram build in real-time!

---

## 🎮 Interface Overview

### Top Bar
- **App Title** - "Galton's Goalie - Science Edition"
- **Mode Indicator** - Shows current visualization mode
- **FPS Counter** - Real-time performance metric
- **Recording Indicator** - Red "REC" badge when recording

### Left Sidebar

#### Mode Selection
- **Standard** - Basic bucket detection with live histogram
- **Motion Trails** - Colored trails showing ball paths (fading)
- **Long Exposure** - Smooth accumulated visualization
- **Ultra-Long Exp** - Ghostly trails that form the bell curve (histogram hidden)

#### Controls
- **Cooldown** (1-120 frames) - Wait time between detections to prevent duplicates
- **Sensitivity** (1-100) - Motion detection threshold (lower = more sensitive)
- **Min Size** (10-1000 px) - Minimum contour area to count as a ball

#### Statistics
- **Total Hits** - Number of balls detected across all buckets
- **Camera** - Active camera index
- **Mean (μ)** - Average bucket position
- **Std Dev (σ)** - Distribution spread

#### Actions
- **🎯 Calibrate** - Define the goal region (coming soon)
- **🔄 Reset Data** - Clear all counts and reset visualizations
- **💾 Export Session** - Save bucket counts as CSV
- **🎬 Start/Stop Recording** - Toggle video recording

### Main Visualization Area
- Full-screen camera feed with OpenCV processing
- Overlays change based on selected mode
- Smooth, responsive updates at 30-60 FPS

### Bottom Histogram (hidden in Ultra-Long Exp mode)
- **Color-coded bars** - Blue (edges) → Purple → Red (center)
- **Gaussian curve** - Dotted line showing theoretical normal distribution
- **Live statistics** - μ, σ, n displayed below
- **Auto-scaling** - Always fits the current maximum count

---

## 🎨 Visual Modes Explained

### 1. Standard Mode
- Clean bucket detection
- Visual glow effect when balls are detected
- Real-time histogram at bottom
- Best for: Classroom demonstrations, data collection

### 2. Motion Trails
- Colored trails fade over time
- Cycle through 8 colors
- Adjustable fade rate (Trail Fade slider)
- Best for: Visualizing individual ball paths

### 3. Long Exposure
- Accumulates motion with slow fade
- Creates a "photograph" effect
- Merges current frame with accumulated history
- Best for: Artistic visualization, showing flow patterns

### 4. Ultra-Long Exposure ✨ (NEW!)
- Pure motion accumulation (no fade)
- Ghostly white trails overlay live feed
- Histogram automatically hides for clean view
- Brightness naturally forms bell curve over time
- Best for: Demonstrating Central Limit Theorem visually

---

## 📊 Understanding the Histogram

The histogram shows which buckets balls land in:

**Color Coding:**
- **Blue bars** (edges) - Low probability regions (buckets 1, 11)
- **Purple bars** (mid) - Medium probability
- **Red/Orange bars** (center) - High probability (buckets 5-7)

**Gaussian Curve (dotted line):**
- Theoretical normal distribution overlay
- Should match your empirical data with enough samples
- Demonstrates the Central Limit Theorem in action

**Statistics:**
- **μ (mu)** - Mean bucket position (ideally ~6 for 11 buckets)
- **σ (sigma)** - Standard deviation (spread of distribution)
- **n** - Total sample size

---

## 💡 Tips for Best Results

### Detection Tuning
1. **Start with defaults** - Cooldown: 20, Sensitivity: 30, Min Size: 100
2. **If missing detections:**
   - Lower sensitivity (more responsive)
   - Lower min size (detect smaller objects)
   - Reduce cooldown (faster re-detection)

3. **If too many false detections:**
   - Raise sensitivity (less responsive)
   - Raise min size (filter small movements)
   - Increase cooldown (longer wait between hits)

### Calibration
- Position camera to see entire goal region
- Good lighting improves detection accuracy
- Minimize background motion
- Use contrasting colored balls (vs. background)

### Data Collection
- Collect at least 100 samples for reliable statistics
- Use Standard mode for purest data
- Export CSV for analysis in Excel, Python, R, etc.

---

## 📁 Exporting Data

Click "💾 Export Session" to save bucket counts as CSV:

```csv
Bucket,Count
1,52
2,89
3,124
4,147
5,126
6,91
7,54
8,28
9,17
10,8
11,3
```

Import into your favorite analysis tool to:
- Create custom visualizations
- Perform statistical tests
- Compare multiple experiments
- Generate reports

---

## 🎯 Use Cases

### Education
- **Physics/Math classes** - Demonstrate probability and statistics
- **STEM workshops** - Hands-on Central Limit Theorem exploration
- **Science fairs** - Interactive exhibit with live data

### Research
- **Data collection** - Gather empirical distribution data
- **Hypothesis testing** - Compare theoretical vs. observed distributions
- **Experimental design** - Test different Galton board configurations

### Art & Communication
- **Science communication** - Beautiful visualizations for YouTube, presentations
- **Museums** - Interactive installation
- **Social media** - Share stunning ultra-long exposure images

---

## 🔧 Configuration

Settings are auto-saved to `galton_config.json`:

```json
{
  "goal_region": [374, 415, 896, 459],
  "camera_index": 0
}
```

Delete this file to reset to defaults.

---

## 🐛 Troubleshooting

### Camera not detected
- Check that your webcam is connected
- Try changing camera index (modify `camera_index=0` in code)
- Ensure no other app is using the camera

### Low FPS
- Close other applications
- Reduce camera resolution (in code: CAP_PROP_FRAME_WIDTH/HEIGHT)
- Disable unnecessary visualizations

### Histogram doesn't match expected bell curve
- Collect more samples (need 100+ for reliable distribution)
- Check physical Galton board alignment (should be level)
- Verify ball release mechanism is centered

### Detections seem wrong
- Recalibrate goal region
- Adjust sensitivity and min size sliders
- Check lighting conditions
- Verify cooldown isn't too high

---

## 🌟 Future Enhancements

Coming soon:
- ✅ Interactive calibration with visual overlay
- ✅ Settings dialog with presets
- ✅ Keyboard shortcuts help screen
- ✅ Sidebar collapse/expand animation
- ✅ Multiple camera switching (UI controls)
- ✅ Advanced export (video + data + metadata package)
- ✅ Trail color options for ultra-long exposure mode
- ✅ Statistical overlays (confidence intervals, z-scores)

---

## 📜 License

MIT License - Feel free to use, modify, and distribute!

## 👏 Credits

- **Design inspiration**: Mark Rober's clean science communication aesthetic
- **Concept**: Sir Francis Galton's original Galton Board (1889)
- **Built with**: PyQt5, OpenCV, NumPy, Python

---

## 🤝 Contributing

Have ideas? Found a bug? Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

**Enjoy exploring probability with Galton's Goalie!** 🎲📊✨
