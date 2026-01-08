"""
Galton's Goalie Visualizer
--------------------------
Real-time ball tracking and histogram visualization for the Galton board.

Controls:
  C - Calibrate goal region (two clicks: top-left, then bottom-right)
  R - Reset histogram counts
  S - Save calibration
  P/Space - Pause/unpause counting
  V - Start/stop video recording
  T - Cycle trail mode (Off -> Trails -> Long Exposure -> Ultra-Long Exposure -> Off)
  G - Cycle trail color (Orange, Cyan, Magenta, Green, Blue, Yellow, White, Red)
  Q - Quit
  0-9 - Switch camera (0 = first camera, 1 = second, etc.)

Sliders:
  Cooldown (frames) - Time to wait after detecting a hit before counting another
  Motion Threshold  - Sensitivity for detecting movement (lower = more sensitive)
  Min Contour Area  - Minimum size of movement to count as a ball

"""

import cv2
import numpy as np
import json
import os
import time

# Configuration
CONFIG_FILE = "galton_config.json"
NUM_BUCKETS = 11
DEFAULT_COOLDOWN_FRAMES = 20  # Frames to wait before counting another hit (~0.7s at 30fps)
DEFAULT_MOTION_THRESHOLD = 30  # Sensitivity for motion detection
DEFAULT_MIN_CONTOUR_AREA = 100  # Minimum area to consider as ball movement

class GaltonGoalieApp:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None

        # Calibration state
        self.calibrating = False
        self.calibration_step = 0  # 0 = waiting for top-left, 1 = waiting for bottom-right
        self.goal_region = None  # (x1, y1, x2, y2)
        self.temp_click = None  # Temporary storage for first click

        # Histogram data
        self.bucket_counts = [0] * NUM_BUCKETS

        # Motion detection state
        self.prev_frame = None
        self.cooldown_counters = [0] * NUM_BUCKETS  # Per-bucket cooldowns
        self.glow_counters = [0] * NUM_BUCKETS  # Per-bucket glow effect timers
        self.paused = False  # Pause counting

        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.fps_start_time = time.time()

        # Video recording
        self.recording = False
        self.video_writer = None
        self.record_start_time = 0

        # Motion trails and long exposure
        # trail_mode: 0=Off, 1=Motion Trails, 2=Long Exposure, 3=Ultra-Long Exposure
        self.trail_mode = 0
        self.trail_mode_names = ["Off", "Trails", "Long Exp", "Ultra-Long Exp"]
        self.trail_canvas = None
        self.long_exposure_canvas = None
        self.ultra_long_exposure_canvas = None
        self.prev_frame_full = None  # For full-frame motion detection
        self.trail_fade = 70  # Fade rate (0-100, higher = slower fade)
        self.trail_colors = [
            ([50, 150, 255], "Orange"),
            ([255, 200, 50], "Cyan"),
            ([255, 50, 255], "Magenta"),
            ([50, 255, 50], "Green"),
            ([255, 100, 100], "Blue"),
            ([50, 255, 255], "Yellow"),
            ([255, 255, 255], "White"),
            ([100, 100, 255], "Red"),
        ]
        self.trail_color_index = 0

        # Adjustable parameters (will be controlled by sliders)
        self.cooldown_frames = DEFAULT_COOLDOWN_FRAMES
        self.motion_threshold = DEFAULT_MOTION_THRESHOLD
        self.min_contour_area = DEFAULT_MIN_CONTOUR_AREA

        # Load saved calibration if exists
        self.load_config()

    def update_fps(self):
        """Update FPS calculation."""
        self.frame_count += 1
        elapsed = time.time() - self.fps_start_time
        if elapsed >= 1.0:  # Update FPS every second
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start_time = time.time()

    def update_trails(self, frame):
        """Update motion trail visualization."""
        h, w = frame.shape[:2]

        # Initialize trail canvas if needed
        if self.trail_canvas is None or self.trail_canvas.shape[:2] != (h, w):
            self.trail_canvas = np.zeros((h, w, 3), dtype=np.float32)

        # Convert to grayscale for motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)

        if self.prev_frame_full is None:
            self.prev_frame_full = gray
            return

        # Detect motion across entire frame
        frame_delta = cv2.absdiff(self.prev_frame_full, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=1)

        # Add motion to trail canvas with selected color
        motion_mask = thresh > 0
        color = self.trail_colors[self.trail_color_index][0]
        self.trail_canvas[motion_mask] = color

        # Fade the trail canvas (trail_fade is 0-100, convert to 0.0-1.0)
        fade_rate = self.trail_fade / 100.0
        self.trail_canvas *= fade_rate

        self.prev_frame_full = gray

    def apply_trails(self, frame):
        """Blend trail canvas onto frame."""
        if self.trail_canvas is None:
            return frame

        # Convert trail canvas to uint8 and blend
        trail_uint8 = np.clip(self.trail_canvas, 0, 255).astype(np.uint8)
        # Additive blending for glow effect
        result = cv2.add(frame, trail_uint8)
        return result

    def update_long_exposure(self, frame):
        """Update long exposure visualization."""
        h, w = frame.shape[:2]

        # Initialize long exposure canvas if needed
        if self.long_exposure_canvas is None or self.long_exposure_canvas.shape[:2] != (h, w):
            self.long_exposure_canvas = np.zeros((h, w, 3), dtype=np.float32)

        # Convert frame to float
        frame_float = frame.astype(np.float32)

        # Take maximum of current canvas and new frame (keeps brightest pixels)
        self.long_exposure_canvas = np.maximum(self.long_exposure_canvas, frame_float)

        # Slowly fade the canvas (controlled by trail_fade slider)
        fade_rate = self.trail_fade / 100.0
        # Fade towards the current frame rather than to black
        self.long_exposure_canvas = self.long_exposure_canvas * fade_rate + frame_float * (1 - fade_rate) * 0.5

    def apply_long_exposure(self, frame):
        """Blend long exposure canvas onto frame."""
        if self.long_exposure_canvas is None:
            return frame

        # Convert to uint8
        result = np.clip(self.long_exposure_canvas, 0, 255).astype(np.uint8)
        return result

    def update_ultra_long_exposure(self, frame):
        """Update ultra-long exposure visualization - accumulates motion indefinitely."""
        h, w = frame.shape[:2]

        # Initialize ultra-long exposure canvas if needed
        if self.ultra_long_exposure_canvas is None or self.ultra_long_exposure_canvas.shape[:2] != (h, w):
            self.ultra_long_exposure_canvas = np.zeros((h, w, 3), dtype=np.float32)

        # Convert to grayscale for motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)

        if self.prev_frame_full is None:
            self.prev_frame_full = gray
            return

        # Detect motion across entire frame
        frame_delta = cv2.absdiff(self.prev_frame_full, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=1)

        # Add motion to canvas (pure accumulation, no fade)
        # Each detection adds a small amount of brightness
        motion_mask = thresh > 0
        # Add faint white trails where motion is detected (smaller increment for ghostly effect)
        self.ultra_long_exposure_canvas[motion_mask] += [15, 15, 15]

        # Clip to prevent overflow
        self.ultra_long_exposure_canvas = np.clip(self.ultra_long_exposure_canvas, 0, 255)

        self.prev_frame_full = gray

    def apply_ultra_long_exposure(self, frame):
        """Blend the accumulated trails on top of the live camera feed."""
        if self.ultra_long_exposure_canvas is None:
            return frame

        # Convert accumulated canvas to uint8
        trails = np.clip(self.ultra_long_exposure_canvas, 0, 255).astype(np.uint8)

        # Blend trails on top of the live frame using additive blending
        # This shows the background with ghostly trails overlaid
        result = cv2.add(frame, trails)

        return result

    def start_recording(self, frame):
        """Start recording video."""
        h, w = frame.shape[:2]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"galton_recording_{timestamp}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(filename, fourcc, 30.0, (w, h))
        self.recording = True
        self.record_start_time = time.time()
        print(f"Recording started: {filename}")

    def stop_recording(self):
        """Stop recording video."""
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        self.recording = False
        duration = time.time() - self.record_start_time
        print(f"Recording saved ({duration:.1f}s)")

    def on_cooldown_change(self, val):
        """Callback for cooldown slider."""
        self.cooldown_frames = max(1, val)  # Minimum 1 frame

    def on_threshold_change(self, val):
        """Callback for motion threshold slider."""
        self.motion_threshold = max(1, val)

    def on_contour_change(self, val):
        """Callback for min contour area slider."""
        self.min_contour_area = max(10, val)

    def on_trail_fade_change(self, val):
        """Callback for trail fade slider."""
        self.trail_fade = max(50, min(99, val))  # Clamp between 50-99

    def switch_camera(self, index):
        """Switch to a different camera."""
        if index == self.camera_index:
            return True  # Already on this camera

        # Try to open the new camera
        new_cap = cv2.VideoCapture(index)
        if not new_cap.isOpened():
            print(f"Camera {index} not available")
            new_cap.release()
            return False

        # Release old camera and switch
        if self.cap:
            self.cap.release()
        self.cap = new_cap
        self.camera_index = index
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.prev_frame = None  # Reset motion detection
        print(f"Switched to camera {index}")
        return True

    def load_config(self):
        """Load calibration from config file if it exists."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.goal_region = tuple(config.get('goal_region', []))
                    if len(self.goal_region) != 4:
                        self.goal_region = None
                    self.camera_index = config.get('camera_index', 0)
                    print(f"Loaded config - calibration: {self.goal_region}, camera: {self.camera_index}")
            except Exception as e:
                print(f"Could not load config: {e}")

    def save_config(self):
        """Save calibration and settings to config file."""
        config = {
            'camera_index': self.camera_index
        }
        if self.goal_region:
            config['goal_region'] = list(self.goal_region)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        print(f"Saved config - calibration: {self.goal_region}, camera: {self.camera_index}")

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks for calibration."""
        if event == cv2.EVENT_LBUTTONDOWN and self.calibrating:
            if self.calibration_step == 0:
                # First click - top-left corner
                self.temp_click = (x, y)
                self.calibration_step = 1
                print(f"Top-left set to ({x}, {y}). Click bottom-right corner...")
            elif self.calibration_step == 1:
                # Second click - bottom-right corner
                x1, y1 = self.temp_click
                x2, y2 = x, y
                # Ensure proper ordering
                self.goal_region = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                self.calibrating = False
                self.calibration_step = 0
                self.temp_click = None
                self.prev_frame = None  # Reset motion detection for new region size
                self.save_config()
                print(f"Calibration complete: {self.goal_region}")

    def get_bucket_index(self, x):
        """Determine which bucket (0-11) an x-coordinate falls into."""
        if not self.goal_region:
            return None
        x1, y1, x2, y2 = self.goal_region
        if x < x1 or x > x2:
            return None
        bucket_width = (x2 - x1) / NUM_BUCKETS
        bucket = int((x - x1) / bucket_width)
        return min(bucket, NUM_BUCKETS - 1)  # Clamp to valid range

    def detect_ball(self, frame):
        """Detect ball movement in the goal region and return list of bucket indices detected."""
        # Decrement all cooldown and glow counters
        for i in range(NUM_BUCKETS):
            self.cooldown_counters[i] = max(0, self.cooldown_counters[i] - 1)
            self.glow_counters[i] = max(0, self.glow_counters[i] - 1)

        if self.paused or not self.goal_region:
            return []

        x1, y1, x2, y2 = self.goal_region

        # Extract goal region from frame
        roi = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_frame is None:
            self.prev_frame = gray
            return []

        # Compute difference between frames
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.prev_frame = gray

        # Find all contours that meet minimum area and check their buckets
        detected_buckets = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_contour_area:
                # Get centroid of the contour
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"]) + x1  # Adjust for ROI offset
                    bucket = self.get_bucket_index(cx)
                    if bucket is not None and self.cooldown_counters[bucket] == 0:
                        self.cooldown_counters[bucket] = self.cooldown_frames
                        self.glow_counters[bucket] = 15  # Glow for ~0.5s at 30fps
                        detected_buckets.append(bucket)

        return detected_buckets

    def draw_overlay(self, frame):
        """Draw the goal region, bucket divisions, and histogram on the frame."""
        h, w = frame.shape[:2]

        # In ultra-long exposure mode, skip most overlays
        in_ultra_mode = (self.trail_mode == 3)

        # Draw instructions
        if self.calibrating:
            if self.calibration_step == 0:
                msg = "Click TOP-LEFT corner of goal"
            else:
                msg = "Click BOTTOM-RIGHT corner of goal"
            cv2.putText(frame, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            if self.temp_click:
                cv2.circle(frame, self.temp_click, 5, (0, 255, 0), -1)
        elif not self.goal_region:
            cv2.putText(frame, "Press C to calibrate goal region", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Draw goal region and bucket divisions (hidden in ultra-long exposure mode)
        if self.goal_region and not in_ultra_mode:
            x1, y1, x2, y2 = self.goal_region
            bucket_width = (x2 - x1) / NUM_BUCKETS

            # Draw glow effect for recently hit buckets
            for i in range(NUM_BUCKETS):
                if self.glow_counters[i] > 0:
                    # Calculate glow intensity (fades out)
                    intensity = self.glow_counters[i] / 15.0
                    bx1 = int(x1 + i * bucket_width)
                    bx2 = int(x1 + (i + 1) * bucket_width)

                    # Create a bright overlay
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (bx1, y1), (bx2, y2), (0, 255, 255), -1)
                    cv2.addWeighted(overlay, intensity * 0.5, frame, 1 - intensity * 0.5, 0, frame)

            # Draw goal rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw bucket divisions
            for i in range(1, NUM_BUCKETS):
                bx = int(x1 + i * bucket_width)
                cv2.line(frame, (bx, y1), (bx, y2), (0, 255, 0), 1)

            # Draw bucket numbers
            for i in range(NUM_BUCKETS):
                bx = int(x1 + (i + 0.5) * bucket_width)
                cv2.putText(frame, str(i + 1), (bx - 5, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # Draw histogram at bottom of frame (hidden in ultra-long exposure mode)
        if not in_ultra_mode:
            self.draw_histogram(frame)

        # Draw stats (calculate text size to right-align properly)
        total = sum(self.bucket_counts)
        stats_text = f"Cam: {self.camera_index} | Total: {total}"
        (text_width, text_height), _ = cv2.getTextSize(stats_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.putText(frame, stats_text, (w - text_width - 10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Draw pause indicator
        if self.paused:
            cv2.putText(frame, "PAUSED", (w // 2 - 60, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        # Draw recording indicator
        if self.recording:
            elapsed = time.time() - self.record_start_time
            cv2.circle(frame, (30, 60), 10, (0, 0, 255), -1)  # Red dot
            cv2.putText(frame, f"REC {elapsed:.1f}s", (50, 67),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Draw trail mode indicator
        if self.trail_mode == 1:  # Motion Trails
            color_bgr, color_name = self.trail_colors[self.trail_color_index]
            cv2.putText(frame, f"TRAILS ({color_name})", (w - 180, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, tuple(color_bgr), 2)
        elif self.trail_mode == 2:  # Long Exposure
            cv2.putText(frame, "LONG EXPOSURE", (w - 180, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 255), 2)
        elif self.trail_mode == 3:  # Ultra-Long Exposure
            cv2.putText(frame, "ULTRA-LONG EXP", (w - 200, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 255, 150), 2)

        # Draw current settings (top-left area, below calibration message)
        settings_y = 60 if (self.calibrating or not self.goal_region) else 30
        cooldown_sec = self.cooldown_frames / self.fps if self.fps > 0 else 0
        cv2.putText(frame, f"Cooldown: {self.cooldown_frames}f ({cooldown_sec:.1f}s) | Sensitivity: {self.motion_threshold} | Min Size: {self.min_contour_area}",
                   (10, settings_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        # Draw FPS
        cv2.putText(frame, f"FPS: {self.fps:.0f}", (w - 90, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

        # Draw controls help
        cv2.putText(frame, "C:Calibrate R:Reset P:Pause V:Record T:Trails G:Color 0-9:Cam Q:Quit", (10, h - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        return frame

    def draw_histogram(self, frame):
        """Draw the histogram at the bottom of the frame."""
        h, w = frame.shape[:2]

        # Histogram dimensions
        hist_height = 120
        hist_margin = 20
        hist_top = h - hist_height - hist_margin
        hist_bottom = h - hist_margin
        hist_left = hist_margin
        hist_right = w - hist_margin

        # Draw histogram background
        cv2.rectangle(frame, (hist_left, hist_top), (hist_right, hist_bottom),
                     (40, 40, 40), -1)
        cv2.rectangle(frame, (hist_left, hist_top), (hist_right, hist_bottom),
                     (100, 100, 100), 1)

        # Calculate bar dimensions
        bar_width = (hist_right - hist_left - 20) // NUM_BUCKETS
        bar_spacing = 2
        max_count = max(self.bucket_counts) if max(self.bucket_counts) > 0 else 1

        # Draw bars
        for i, count in enumerate(self.bucket_counts):
            bar_height = int((count / max_count) * (hist_height - 30)) if max_count > 0 else 0
            bar_left = hist_left + 10 + i * bar_width + bar_spacing
            bar_right = bar_left + bar_width - bar_spacing * 2
            bar_top = hist_bottom - 20 - bar_height
            bar_bottom_y = hist_bottom - 20

            # Color gradient from edges (blue) to center (red/orange)
            center_dist = abs(i - (NUM_BUCKETS - 1) / 2) / ((NUM_BUCKETS - 1) / 2)
            r = int(255 * (1 - center_dist))
            b = int(255 * center_dist)
            g = int(100 * (1 - center_dist))
            color = (b, g, r)

            cv2.rectangle(frame, (bar_left, bar_top), (bar_right, bar_bottom_y), color, -1)

            # Draw count above bar
            if count > 0:
                cv2.putText(frame, str(count), (bar_left, bar_top - 3),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

            # Draw bucket number below bar
            cv2.putText(frame, str(i + 1), (bar_left + bar_width // 4, hist_bottom - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)

    def run(self):
        """Main application loop."""
        print("Starting Galton's Goalie Visualizer...")
        print("Controls: C=Calibrate, R=Reset, S=Save, Q=Quit")
        print("Use sliders to adjust: Cooldown, Motion Threshold, Min Contour Area")

        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.camera_index}")
            return

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        cv2.namedWindow("Galton's Goalie")
        cv2.setMouseCallback("Galton's Goalie", self.mouse_callback)

        # Create a separate control panel window with short labels
        cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Controls", 400, 150)
        cv2.createTrackbar("Cooldown", "Controls",
                          self.cooldown_frames, 120, self.on_cooldown_change)
        cv2.createTrackbar("Sensitivity", "Controls",
                          self.motion_threshold, 100, self.on_threshold_change)
        cv2.createTrackbar("Min Size", "Controls",
                          self.min_contour_area, 1000, self.on_contour_change)
        cv2.createTrackbar("Trail Fade", "Controls",
                          self.trail_fade, 99, self.on_trail_fade_change)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame")
                break

            # Update FPS
            self.update_fps()

            # Update visualization based on mode (only if not paused)
            if not self.paused:
                if self.trail_mode == 1:  # Motion Trails
                    self.update_trails(frame)
                elif self.trail_mode == 2:  # Long Exposure
                    self.update_long_exposure(frame)
                elif self.trail_mode == 3:  # Ultra-Long Exposure
                    self.update_ultra_long_exposure(frame)

            # Detect ball and update counts
            detected_buckets = self.detect_ball(frame)
            for bucket in detected_buckets:
                self.bucket_counts[bucket] += 1
                print(f"Hit detected in bucket {bucket + 1}! Counts: {self.bucket_counts}")

            # Apply visualization before overlay
            if self.trail_mode == 1:  # Motion Trails
                frame = self.apply_trails(frame)
            elif self.trail_mode == 2:  # Long Exposure
                frame = self.apply_long_exposure(frame)
            elif self.trail_mode == 3:  # Ultra-Long Exposure
                frame = self.apply_ultra_long_exposure(frame)

            # Draw overlay
            frame = self.draw_overlay(frame)

            # Write frame if recording
            if self.recording and self.video_writer:
                self.video_writer.write(frame)

            # Show frame
            cv2.imshow("Galton's Goalie", frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.calibrating = True
                self.calibration_step = 0
                self.temp_click = None
                self.prev_frame = None  # Reset motion detection
                print("Calibration mode: Click top-left corner of goal...")
            elif key == ord('r'):
                self.bucket_counts = [0] * NUM_BUCKETS
                self.cooldown_counters = [0] * NUM_BUCKETS
                self.glow_counters = [0] * NUM_BUCKETS
                self.ultra_long_exposure_canvas = None
                print("Histogram and ultra-long exposure reset")
            elif key == ord('s'):
                self.save_config()
            elif key == ord('p') or key == ord(' '):
                self.paused = not self.paused
                print("PAUSED" if self.paused else "RESUMED")
            elif key == ord('v'):
                if self.recording:
                    self.stop_recording()
                else:
                    self.start_recording(frame)
            elif key == ord('t'):
                # Cycle through trail modes: Off -> Trails -> Long Exp -> Ultra-Long Exp -> Off
                self.trail_mode = (self.trail_mode + 1) % 4
                # Clear canvases when switching modes
                self.trail_canvas = None
                self.long_exposure_canvas = None
                self.ultra_long_exposure_canvas = None
                self.prev_frame_full = None
                print(f"Trail mode: {self.trail_mode_names[self.trail_mode]}")
            elif key == ord('g'):
                # Cycle trail color
                self.trail_color_index = (self.trail_color_index + 1) % len(self.trail_colors)
                color_name = self.trail_colors[self.trail_color_index][1]
                print(f"Trail color: {color_name}")
            elif ord('0') <= key <= ord('9'):
                # Switch camera and save
                cam_index = key - ord('0')
                if self.switch_camera(cam_index):
                    self.save_config()

        # Stop recording if active
        if self.recording:
            self.stop_recording()

        self.cap.release()
        cv2.destroyAllWindows()
        print("Goodbye!")


def nothing(x):
    """Dummy callback for trackbars (not used but required by some OpenCV versions)."""
    pass


if __name__ == "__main__":
    app = GaltonGoalieApp(camera_index=0)
    app.run()
