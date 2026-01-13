# Galton's Goalie Visualizer

A real-time computer vision app that tracks balls shot through a Galton board (Plinko machine) and visualizes the resulting bell curve distribution.

Inspired by the [CrunchLabs](https://www.crunchlabs.com/) ["Galton's Goalie" project](https://www.crunchlabs.com/products/galtons-goalie?srsltid=AfmBOoqQ8V6aj6XHOs5uSdeRfJU1NJJluky5hNH1kjtexU9fOu944Vwk), but could be adapted for any similar setup.

A YouTube video showing an earlier version of this in action is [here](https://www.youtube.com/watch?v=Z8H1zYT_3DY) 

## What It Does

1. **Watches a live webcam feed** of your Galton board
2. **Detects when balls enter the goal** using motion detection
3. **Counts hits in 11 buckets** across the goal area
4. **Displays a real-time histogram** showing the distribution (which forms a bell curve over time)
5. **Visualizes ball paths** with motion trails or long-exposure effects

![Demo: Full setup with Galton board](demo-board.webp)

![Demo: Real-time ball tracking and histogram visualization](demo.webp)

With the game board removed, you can watch motion trails and use long exposures to visualize the bell curve forming. Ultra-long exposure lets you see the "Plinko" trails pile up in real time. In addition to looking cool, maybe this will also help you "debug" physical inaccuracies in your Plinko pin  setup, like it did for us! 

## Installation

Requires Python 3.7+ and OpenCV.

```bash
pip install opencv-python numpy pyqt5
```

## Quick Start

```bash
python galton_goalie_qt.py
```

1. Point your webcam at the Galton board goal area
2. Press **C** to calibrate - click the top-left corner of the goal, then the bottom-right corner
3. Start dropping balls! Watch the histogram build up at the bottom of the screen

## Controls

| Key | Action |
|-----|--------|
| **C** | Calibrate goal region (two clicks: top-left, then bottom-right) |
| **R** | Reset histogram counts to zero |
| **S** | Save calibration to config file |
| **P** or **Space** | Pause/unpause ball counting |
| **V** | Start/stop video recording |
| **T** | Cycle trail mode: Off → Trails → Long Exposure → Off |
| **G** | Cycle trail color (Orange, Cyan, Magenta, Green, Blue, Yellow, White, Red) |
| **0-9** | Switch camera (0 = first camera, 1 = second, etc.) |
| **Q** | Quit |

## Sliders (Controls Window)

A separate "Controls" window appears with adjustable sliders:

| Slider | What It Does |
|--------|--------------|
| **Cooldown** | Frames to wait after detecting a hit before counting another in the same bucket (prevents double-counting) |
| **Sensitivity** | Motion detection threshold. Lower = more sensitive, may pick up noise. Higher = less sensitive, may miss balls |
| **Min Size** | Minimum pixel area for detected motion. Filters out small noise |
| **Trail Fade** | How slowly trails/long exposure fades (higher = longer persistence) |

## Features

### Ball Detection
- Uses frame differencing to detect motion in the calibrated goal region
- Each of the 11 buckets has its own cooldown timer, so simultaneous balls in different buckets both register
- Visual "glow" effect highlights which bucket was hit

### Histogram
- Real-time bar chart at the bottom of the screen
- Color gradient: center buckets are red/orange (most hits expected), edge buckets are blue (fewer hits expected)
- Shows count above each bar
- Total count displayed in top-right corner

### Motion Trails (press T)
- **Trails mode**: Colored glow effect showing where motion was detected. Creates light-painting style streaks as balls travel across the screen.
- **Long Exposure mode**: Simulates a long-exposure photograph, keeping the brightest pixels over time. Shows actual ball paths with a dreamy, photographic look.

### Video Recording (press V)
- Records the full visualization (video feed + overlay + histogram)
- Saves as `galton_recording_YYYYMMDD_HHMMSS.mp4`
- Recording indicator shows elapsed time

## Configuration

Settings are automatically saved to `galton_config.json`:
- Goal region calibration (so you don't have to recalibrate each run)
- Selected camera index

## Tips

- **Lighting matters**: Consistent lighting helps detection. Avoid shadows crossing the goal area.
- **Camera position**: Mount the camera so it has a clear, stable view of the goal. Minimize camera shake.
- **Start with defaults**: The default sensitivity and min size work well for most setups. Adjust if you're getting false detections or missing balls.
- **Use Pause**: Press P to pause counting while you adjust the board or retrieve balls.
- **Trails are fun**: Press T to enable trails, then G to pick your favorite color. Makes for great recordings!

## How the Bell Curve Forms

The Galton board demonstrates the Central Limit Theorem. Each ball bounces off pegs, going left or right randomly at each level. After many bounces, the distribution of where balls land follows a normal (bell curve) distribution:
- Most balls end up in the center buckets
- Fewer balls end up at the edges
- The more balls you drop, the smoother the curve becomes

This visualizer lets you watch that mathematical principle emerge in real-time!

## Troubleshooting

**"Could not open camera"**
- Try a different camera index (press 1, 2, etc.)
- Make sure no other app is using the webcam

**Balls not being detected**
- Lower the Sensitivity slider
- Lower the Min Size slider
- Make sure the goal region is calibrated correctly (press C)
- Check that lighting is adequate

**Too many false detections**
- Raise the Sensitivity slider
- Raise the Min Size slider
- Increase the Cooldown slider
- Check for shadows or reflections in the goal area

**Calibration not saving**
- Press S to manually save, or the calibration saves automatically when you complete it

## License

MIT License - feel free to modify and share!

---

*Built with OpenCV and Python. Have fun watching probability in action!*
