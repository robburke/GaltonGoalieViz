# Galton's Goalie Visualizer

## Project Overview

This is a real-time computer vision application that tracks balls falling through a Galton board (bean machine) and visualizes their distribution as a histogram. The application uses OpenCV for motion detection and displays a live histogram showing which buckets balls land in, demonstrating the central limit theorem in action.

## Core Functionality

- **Real-time ball tracking**: Detects balls entering a goal region using motion detection
- **12-bucket histogram**: Visualizes the distribution of ball landings
- **Interactive calibration**: Point-and-click interface to define the goal region
- **Adjustable parameters**: Real-time sliders for fine-tuning detection sensitivity

## Key Files

- `galton_goalie.py`: Main application (349 lines)
  - `GaltonGoalieApp` class handles all functionality
  - Motion detection using frame differencing
  - Histogram visualization with color gradient (blue edges to red center)
  - Interactive calibration system

- `galton_config.json`: Stores calibrated goal region coordinates
  - Current calibration: `[374, 415, 896, 459]` (x1, y1, x2, y2)

- `Galton1.jpg`, `Galton2.jpg`: Reference images
- `GaltonSampleVideo.mp4`: Sample video footage

## How It Works

### Motion Detection Algorithm

1. Extracts ROI (region of interest) from the calibrated goal area
2. Converts to grayscale and applies Gaussian blur
3. Computes frame difference to detect motion
4. Applies binary threshold and dilation
5. Finds contours and selects the largest one meeting minimum area
6. Calculates centroid and determines which bucket it falls into
7. Applies cooldown period to prevent duplicate detections

### Bucket Assignment

The goal region is divided into 12 equal-width buckets. When a ball is detected, its x-coordinate determines which bucket (1-12) it lands in using:
```python
bucket = (x - x1) / bucket_width
```

## Configuration Parameters

### Adjustable via Sliders (in Controls window)

- **Cooldown** (1-120 frames, default: 45)
  - Time to wait after detecting a ball before counting another
  - At 30fps, 45 frames ≈ 1.5 seconds
  - Prevents counting the same ball multiple times

- **Sensitivity** (1-100, default: 30)
  - Motion detection threshold
  - Lower = more sensitive to small movements
  - Higher = requires more significant motion

- **Min Size** (10-1000 pixels, default: 100)
  - Minimum contour area to count as a ball
  - Filters out noise and small movements

### Fixed Parameters

- `NUM_BUCKETS = 12`: Number of histogram bins
- Camera resolution: 1280x720

## Controls

| Key | Action |
|-----|--------|
| `C` | Enter calibration mode |
| `R` | Reset histogram counts to zero |
| `S` | Save current calibration to config file |
| `Q` | Quit application |

## Usage Instructions

1. Run the application: `python galton_goalie.py`
2. Press `C` to calibrate:
   - Click the top-left corner of the goal region
   - Click the bottom-right corner
   - Calibration is auto-saved
3. Adjust sliders in the Controls window as needed
4. Drop balls through the Galton board
5. Watch the histogram build up in real-time

## Visual Features

### Main Display Window

- Green rectangle showing calibrated goal region
- Vertical green lines dividing the 12 buckets
- Bucket numbers (1-12) above the goal region
- Real-time histogram at bottom with:
  - Color gradient (blue at edges → red/orange at center)
  - Count labels above each bar
  - Bucket numbers below bars
- Current settings display
- Total count in top-right corner
- Control hints at bottom

### Histogram Visualization

- Background: Dark gray (40, 40, 40)
- Border: Medium gray (100, 100, 100)
- Bars: Color-coded by distance from center
  - Center buckets: Red/orange (representing higher probability)
  - Edge buckets: Blue (representing lower probability)
- Automatically scales to fit the maximum count

## Technical Details

### Dependencies

- `cv2` (OpenCV): Video capture, image processing, GUI
- `numpy`: Numerical operations
- `json`: Configuration file I/O
- `os`: File system operations
- `datetime`: Timestamping (imported but not actively used)

### Camera Configuration

- Default camera index: 0 (primary webcam)
- Resolution: 1280x720
- Can be changed via `GaltonGoalieApp(camera_index=N)`

### State Management

The application maintains several state variables:
- `bucket_counts`: Array of 12 integers tracking hits per bucket
- `goal_region`: Tuple (x1, y1, x2, y2) defining calibrated area
- `prev_frame`: Previous grayscale frame for motion detection
- `cooldown_counter`: Frames remaining before next detection allowed
- `calibrating`: Boolean flag for calibration mode
- `calibration_step`: 0 (awaiting top-left) or 1 (awaiting bottom-right)

## Common Workflows

### First-Time Setup

1. Position camera to view Galton board goal area
2. Run application
3. Calibrate goal region with `C` key
4. Adjust sensitivity sliders
5. Press `S` to save (auto-saved after calibration anyway)

### Recalibrating

1. Press `C` to enter calibration mode
2. Click new top-left corner
3. Click new bottom-right corner
4. Previous frame buffer is automatically reset

### Experimenting with Different Settings

1. Use the sliders to adjust parameters in real-time
2. Press `R` to reset counts and start fresh
3. Compare distributions with different cooldown/sensitivity settings

## Expected Behavior (Galton Board Physics)

With enough samples, the histogram should approximate a normal (Gaussian) distribution:
- Most balls land in center buckets (6-7)
- Fewer balls land in edge buckets (1, 12)
- Symmetric distribution around the center

This demonstrates the Central Limit Theorem in action.

## Troubleshooting

### Balls Not Detected

- Lower the Sensitivity slider (motion threshold)
- Lower the Min Size slider (minimum contour area)
- Ensure good lighting and contrast
- Recalibrate if goal region is incorrect

### Too Many False Detections

- Raise the Sensitivity slider
- Raise the Min Size slider
- Increase Cooldown frames
- Reduce background motion/vibration

### Histogram Looks Wrong

- Press `R` to reset and collect more samples
- Verify calibration is accurate
- Check that balls are actually falling randomly (not biased by table tilt, etc.)

## Future Enhancement Ideas

- Export histogram data to CSV
- Statistical analysis overlay (mean, standard deviation, fit to normal curve)
- Multiple camera support for different angles
- Replay mode using saved video
- Heatmap showing ball trajectories
- Session logging with timestamps
- Comparison mode (overlay multiple runs)
