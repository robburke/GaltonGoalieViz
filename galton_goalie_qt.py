"""
Galton's Goalie - Professional Qt Version
==========================================
A beautiful, market-ready computer vision application for tracking
balls through a Galton board and visualizing probability distributions.

Author: Claude & User
Version: 2.0 (Qt Professional Edition)
"""

import sys
import cv2
import numpy as np
import json
import os
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QRadioButton, QButtonGroup,
    QGroupBox, QDialog, QTabWidget, QTextEdit, QFileDialog,
    QMessageBox, QGraphicsOpacityEffect, QScrollArea, QComboBox, QCheckBox
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QThread, QPropertyAnimation,
    QEasingCurve, QRect, QSize, pyqtSlot
)
from PyQt5.QtGui import (
    QImage, QPixmap, QPainter, QColor, QPen, QBrush,
    QLinearGradient, QFont, QPalette, QIcon
)

# Configuration
CONFIG_FILE = "galton_config.json"
NUM_BUCKETS = 11
DEFAULT_COOLDOWN_FRAMES = 20
DEFAULT_MOTION_THRESHOLD = 30
DEFAULT_MIN_CONTOUR_AREA = 100

# Color Palette (Mark Rober inspired)
DARK_NAVY = QColor(7, 26, 47)        # #071A2F
DEEP_BLUE = QColor(10, 36, 99)       # #0A2463
ROYAL_BLUE = QColor(62, 146, 204)    # #3E92CC
BRIGHT_CYAN = QColor(28, 119, 195)   # #1C77C3
SKY_BLUE = QColor(93, 173, 226)      # #5DADE2
SLATE = QColor(44, 62, 80)           # #2C3E50
WHITE = QColor(255, 255, 255)
LIGHT_GRAY = QColor(189, 195, 199)   # #BDC3C7
SUCCESS_GREEN = QColor(39, 174, 96)  # #27AE60
WARNING_ORANGE = QColor(230, 126, 34)  # #E67E22
ERROR_RED = QColor(192, 57, 43)      # #C0392B


class VideoThread(QThread):
    """Background thread for video processing to keep UI responsive."""

    frame_ready = pyqtSignal(np.ndarray)
    detection_update = pyqtSignal(list)  # List of detected bucket indices
    fps_update = pyqtSignal(float)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        self.paused = False

        # Processing state
        self.goal_region = None
        self.prev_frame = None
        self.prev_frame_full = None

        # Visualization canvases
        self.trail_canvas = None
        self.long_exposure_canvas = None
        self.ultra_long_exposure_canvas = None

        # Settings
        self.trail_mode = 0  # 0=Off, 1=Trails, 2=Long Exp, 3=Ultra-Long Exp
        self.cooldown_frames = DEFAULT_COOLDOWN_FRAMES
        self.motion_threshold = DEFAULT_MOTION_THRESHOLD
        self.min_contour_area = DEFAULT_MIN_CONTOUR_AREA
        self.trail_fade = 70  # Fade rate for mode 1 (Motion Trails)
        self.trail_size = 3  # Thickness/dilation iterations for mode 1
        self.long_exposure_duration = 85  # Persistence for mode 2 (1-100)
        self.trail_color_index = 0
        self.show_bucket_overlay = True  # Show bucket dividers on video
        self.flip_horizontal = False  # Flip camera feed horizontally

        # Cooldown and glow tracking
        self.cooldown_counters = [0] * NUM_BUCKETS
        self.glow_counters = [0] * NUM_BUCKETS

        # Frame storage for clean recording
        self.clean_frame = None  # Frame before overlays for clean recording mode

        # Trail colors (BGR format)
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

        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.fps_start_time = time.time()

    def run(self):
        """Main thread loop."""
        self.running = True
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        while self.running:
            ret, frame = self.cap.read()
            if ret:
                # Flip horizontally if enabled
                if self.flip_horizontal:
                    frame = cv2.flip(frame, 1)

                # Update FPS
                self.update_fps()

                # Process frame based on mode (respects paused flag internally)
                processed_frame = self.process_frame(frame.copy())

                # Detect balls only if not paused
                if not self.paused:
                    detected_buckets = self.detect_ball(frame)
                    if detected_buckets:
                        self.detection_update.emit(detected_buckets)

                # Always emit processed frame (video keeps running)
                self.frame_ready.emit(processed_frame)

            self.msleep(16)  # ~60 FPS

        if self.cap:
            self.cap.release()

    def stop(self):
        """Stop the thread."""
        self.running = False
        self.wait()

    def update_fps(self):
        """Update FPS calculation."""
        self.frame_count += 1
        elapsed = time.time() - self.fps_start_time
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.fps_update.emit(self.fps)
            self.frame_count = 0
            self.fps_start_time = time.time()

    def process_frame(self, frame):
        """Process frame based on current mode."""
        # Update visualization based on mode
        if not self.paused and self.trail_mode > 0:
            if self.trail_mode == 1:  # Motion Trails
                self.update_trails(frame)
            elif self.trail_mode == 2:  # Long Exposure
                self.update_long_exposure(frame)
            elif self.trail_mode == 3:  # Ultra-Long Exposure
                self.update_ultra_long_exposure(frame)

        # Apply visualization
        if self.trail_mode == 1:
            frame = self.apply_trails(frame)
        elif self.trail_mode == 2:
            frame = self.apply_long_exposure(frame)
        elif self.trail_mode == 3:
            frame = self.apply_ultra_long_exposure(frame)

        # Save clean frame (camera + trails, no overlays) for clean recording mode
        self.clean_frame = frame.copy()

        # Draw bucket overlay if enabled
        if self.show_bucket_overlay and self.goal_region:
            frame = self.draw_bucket_overlay(frame)

        return frame

    def update_trails(self, frame):
        """Update motion trail visualization."""
        h, w = frame.shape[:2]
        if self.trail_canvas is None or self.trail_canvas.shape[:2] != (h, w):
            self.trail_canvas = np.zeros((h, w, 3), dtype=np.float32)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)

        if self.prev_frame_full is None:
            self.prev_frame_full = gray
            return

        frame_delta = cv2.absdiff(self.prev_frame_full, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=self.trail_size)

        motion_mask = thresh > 0
        color = self.trail_colors[self.trail_color_index][0]
        self.trail_canvas[motion_mask] = color

        fade_rate = self.trail_fade / 100.0
        self.trail_canvas *= fade_rate

        self.prev_frame_full = gray

    def apply_trails(self, frame):
        """Blend trail canvas onto frame."""
        if self.trail_canvas is None:
            return frame
        trail_uint8 = np.clip(self.trail_canvas, 0, 255).astype(np.uint8)
        return cv2.add(frame, trail_uint8)

    def update_long_exposure(self, frame):
        """Update long exposure visualization."""
        h, w = frame.shape[:2]
        if self.long_exposure_canvas is None or self.long_exposure_canvas.shape[:2] != (h, w):
            self.long_exposure_canvas = np.zeros((h, w, 3), dtype=np.float32)

        frame_float = frame.astype(np.float32)
        self.long_exposure_canvas = np.maximum(self.long_exposure_canvas, frame_float)

        # Use long_exposure_duration (1-100) to control persistence
        fade_rate = self.long_exposure_duration / 100.0
        self.long_exposure_canvas = (self.long_exposure_canvas * fade_rate +
                                     frame_float * (1 - fade_rate) * 0.5)

    def apply_long_exposure(self, frame):
        """Apply long exposure canvas."""
        if self.long_exposure_canvas is None:
            return frame
        return np.clip(self.long_exposure_canvas, 0, 255).astype(np.uint8)

    def update_ultra_long_exposure(self, frame):
        """Update ultra-long exposure visualization."""
        h, w = frame.shape[:2]
        if self.ultra_long_exposure_canvas is None or self.ultra_long_exposure_canvas.shape[:2] != (h, w):
            self.ultra_long_exposure_canvas = np.zeros((h, w, 3), dtype=np.float32)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)

        if self.prev_frame_full is None:
            self.prev_frame_full = gray
            return

        frame_delta = cv2.absdiff(self.prev_frame_full, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=1)

        motion_mask = thresh > 0
        self.ultra_long_exposure_canvas[motion_mask] += [15, 15, 15]
        self.ultra_long_exposure_canvas = np.clip(self.ultra_long_exposure_canvas, 0, 255)

        self.prev_frame_full = gray

    def apply_ultra_long_exposure(self, frame):
        """Blend accumulated trails on live feed."""
        if self.ultra_long_exposure_canvas is None:
            return frame
        trails = np.clip(self.ultra_long_exposure_canvas, 0, 255).astype(np.uint8)
        return cv2.add(frame, trails)

    def draw_bucket_overlay(self, frame):
        """Draw bucket dividers and labels on the frame."""
        if not self.goal_region:
            return frame

        x1, y1, x2, y2 = self.goal_region

        # Draw goal region rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Calculate bucket width
        region_width = x2 - x1
        bucket_width = region_width / NUM_BUCKETS

        # Draw vertical bucket dividers and glow effects
        for i in range(NUM_BUCKETS):
            # Draw bucket glow if active
            if self.glow_counters[i] > 0:
                # Calculate glow intensity (fade out over time)
                glow_intensity = self.glow_counters[i] / 30.0  # 30 frames = ~1 second

                # Create semi-transparent overlay for this bucket
                bucket_x1 = int(x1 + i * bucket_width)
                bucket_x2 = int(x1 + (i + 1) * bucket_width)

                # Draw filled rectangle with alpha blending
                overlay = frame.copy()
                cv2.rectangle(overlay, (bucket_x1, y1), (bucket_x2, y2),
                            (0, 255, 255), -1)  # Yellow fill
                alpha = 0.3 * glow_intensity
                cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

            # Draw divider line
            if i > 0:
                x = int(x1 + i * bucket_width)
                cv2.line(frame, (x, y1), (x, y2), (0, 255, 0), 1)

        # Draw bucket numbers above the goal region
        for i in range(NUM_BUCKETS):
            bucket_center_x = int(x1 + (i + 0.5) * bucket_width)
            label = str(i + 1)

            # Get text size for centering
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
            text_x = bucket_center_x - text_size[0] // 2
            text_y = y1 - 10

            # Draw text with background for visibility
            cv2.putText(frame, label, (text_x, text_y), font, font_scale,
                       (0, 255, 0), thickness, cv2.LINE_AA)

        return frame

    def detect_ball(self, frame):
        """Detect ball movement and return detected bucket indices."""
        # Decrement cooldowns and glows
        for i in range(NUM_BUCKETS):
            self.cooldown_counters[i] = max(0, self.cooldown_counters[i] - 1)
            self.glow_counters[i] = max(0, self.glow_counters[i] - 1)

        if self.paused or not self.goal_region:
            return []

        x1, y1, x2, y2 = self.goal_region
        roi = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_frame is None:
            self.prev_frame = gray
            return []

        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.prev_frame = gray

        detected_buckets = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_contour_area:
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"]) + x1
                    bucket = self.get_bucket_index(cx)
                    if bucket is not None and self.cooldown_counters[bucket] == 0:
                        self.cooldown_counters[bucket] = self.cooldown_frames
                        self.glow_counters[bucket] = 15
                        detected_buckets.append(bucket)

        return detected_buckets

    def get_bucket_index(self, x):
        """Determine which bucket an x-coordinate falls into."""
        if not self.goal_region:
            return None
        x1, y1, x2, y2 = self.goal_region
        if x < x1 or x > x2:
            return None
        bucket_width = (x2 - x1) / NUM_BUCKETS
        bucket = int((x - x1) / bucket_width)
        return min(bucket, NUM_BUCKETS - 1)

    def reset_ultra_long_exposure(self):
        """Reset ultra-long exposure canvas."""
        self.ultra_long_exposure_canvas = None


class VisualizationWidget(QLabel):
    """Widget to display OpenCV frames."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #0F0F1F;
                border: 2px solid #1C77C3;
                border-radius: 4px;
            }
        """)

    @pyqtSlot(np.ndarray)
    def update_frame(self, frame):
        """Update the displayed frame."""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Scale to fit widget while maintaining aspect ratio
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled_pixmap)


class HistogramWidget(QWidget):
    """Custom widget to draw beautiful histogram."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bucket_counts = [0] * NUM_BUCKETS
        self.glow_counters = [0] * NUM_BUCKETS
        self.setMinimumHeight(180)
        self.show_gaussian = True
        self.show_stats_on_graph = True  # Show statistics text on histogram

        # Calculate statistics
        self.mean = 0.0
        self.std_dev = 0.0
        self.total = 0

    def update_counts(self, counts, glow_counters=None):
        """Update bucket counts and recalculate statistics."""
        self.bucket_counts = counts[:]
        if glow_counters:
            self.glow_counters = glow_counters[:]
        self.total = sum(counts)

        if self.total > 0:
            # Calculate mean
            weighted_sum = sum((i + 1) * count for i, count in enumerate(counts))
            self.mean = weighted_sum / self.total

            # Calculate standard deviation
            variance = sum(count * ((i + 1) - self.mean) ** 2
                          for i, count in enumerate(counts)) / self.total
            self.std_dev = variance ** 0.5
        else:
            # Reset to defaults when no data
            self.mean = 0.0
            self.std_dev = 0.0

        self.update()

    def paintEvent(self, event):
        """Draw the histogram."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(7, 26, 47, 217))  # 85% opacity

        # Draw border
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # Title
        painter.setPen(QPen(WHITE))
        title_font = QFont("Campton", 11, QFont.Bold)
        title_font.setStyleHint(QFont.SansSerif)
        title_font.setFamilies(["Campton", "Montserrat", "Arial Black", "sans-serif"])
        painter.setFont(title_font)
        painter.drawText(15, 25, "DISTRIBUTION HISTOGRAM")

        # Draw histogram bars
        margin = 40
        bar_area_width = self.width() - 2 * margin
        bar_area_height = self.height() - 60
        bar_width = bar_area_width // NUM_BUCKETS
        max_count = max(self.bucket_counts) if max(self.bucket_counts) > 0 else 1

        for i, count in enumerate(self.bucket_counts):
            bar_height = int((count / max_count) * (bar_area_height - 20))
            bar_x = margin + i * bar_width
            bar_y = self.height() - 30 - bar_height

            # Color gradient (blue to red)
            ratio = abs(i - (NUM_BUCKETS - 1) / 2) / ((NUM_BUCKETS - 1) / 2)
            r = int(255 * (1 - ratio))
            b = int(255 * ratio)
            g = int(100 * (1 - ratio))

            # Apply glow effect if active
            if self.glow_counters[i] > 0:
                glow_intensity = self.glow_counters[i] / 15.0  # 15 frames max
                # Brighten the color
                r = min(255, int(r + (255 - r) * glow_intensity * 0.8))
                g = min(255, int(g + (255 - g) * glow_intensity * 0.8))
                b = min(255, int(b + (255 - b) * glow_intensity * 0.8))

            # Draw bar with gradient
            gradient = QLinearGradient(bar_x, bar_y, bar_x, self.height() - 30)
            gradient.setColorAt(0, QColor(r, g, b, 200))
            gradient.setColorAt(1, QColor(r, g, b, 255))

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bar_x + 2, bar_y, bar_width - 8, bar_height, 3, 3)

            # Count label
            if count > 0:
                painter.setPen(WHITE)
                painter.setFont(QFont("Arial", 8))
                painter.drawText(bar_x, bar_y - 3, bar_width, 15,
                               Qt.AlignCenter, str(count))

            # Bucket number
            painter.setPen(LIGHT_GRAY)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(bar_x, self.height() - 18, bar_width, 15,
                           Qt.AlignCenter, str(i + 1))

        # Draw expected Gaussian curve if enabled
        if self.show_gaussian and self.total > 0:
            painter.setPen(QPen(BRIGHT_CYAN, 2, Qt.DashLine))

            # Expected distribution for Galton board
            # Mean at center (bucket 6.5 for 12 buckets)
            expected_mean = (NUM_BUCKETS + 1) / 2.0
            # Standard deviation for binomial distribution: sqrt(n*p*(1-p))
            # For a symmetric Galton board with equal probabilities
            # Using typical value for 12 buckets
            expected_std_dev = 1.7  # Approximation for 12-bucket Galton board

            # Calculate expected Gaussian points
            points = []
            expected_values = []
            for i in range(NUM_BUCKETS):
                x_val = i + 1
                # Gaussian function using EXPECTED parameters
                exponent = -((x_val - expected_mean) ** 2) / (2 * expected_std_dev ** 2)
                y_val = (1 / (expected_std_dev * (2 * 3.14159) ** 0.5)) * (2.71828 ** exponent)
                expected_values.append(y_val)

            # Normalize expected values to match total count
            total_expected = sum(expected_values)
            for i in range(NUM_BUCKETS):
                # Scale to match the total number of hits
                expected_count = (expected_values[i] / total_expected) * self.total

                # Scale to fit histogram display
                bar_h = int((expected_count / max_count) * (bar_area_height - 20)) if max_count > 0 else 0

                bar_x = margin + i * bar_width + bar_width // 2
                bar_y = self.height() - 30 - bar_h
                points.append((bar_x, bar_y))

            # Draw curve
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1],
                               points[i + 1][0], points[i + 1][1])

        # Statistics box (if enabled)
        if self.show_stats_on_graph and self.total > 0:
            stats_text = f"μ = {self.mean:.1f}  |  σ = {self.std_dev:.1f}  |  n = {self.total}"
            painter.setPen(LIGHT_GRAY)
            painter.setFont(QFont("Courier", 9))
            text_rect = painter.fontMetrics().boundingRect(stats_text)
            stats_x = (self.width() - text_rect.width()) // 2
            painter.drawText(stats_x, self.height() - 5, stats_text)


class CalibrationDialog(QDialog):
    """Interactive calibration dialog for setting goal region."""

    calibration_complete = pyqtSignal(tuple)  # Emits (x1, y1, x2, y2)

    def __init__(self, frame, existing_region=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibration")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        self.current_frame = frame.copy()
        self.existing_region = existing_region
        self.click_points = []
        self.step = 0  # 0 = waiting for top-left, 1 = waiting for bottom-right

        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Image label for displaying frame
        self.image_label = QLabel()
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.on_mouse_click
        layout.addWidget(self.image_label)

        # Instruction label
        self.instruction_label = QLabel("Click the TOP-LEFT corner of the goal region")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet("""
            QLabel {
                background-color: rgba(10, 36, 99, 200);
                color: white;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.instruction_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C3E50;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495E;
            }
        """)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        self.reset_btn = QPushButton("Reset Points")
        self.reset_btn.clicked.connect(self.reset_calibration)
        self.reset_btn.setEnabled(False)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #3E92CC;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5DADE2;
            }
            QPushButton:disabled {
                background-color: #7F8C8D;
            }
        """)
        button_layout.addWidget(self.reset_btn)

        layout.addLayout(button_layout)

    def set_frame(self, frame):
        """Set the current frame to display."""
        self.current_frame = frame.copy()
        self.update_display()

    def update_display(self):
        """Update the displayed image with annotations."""
        if self.current_frame is None:
            return

        display_frame = self.current_frame.copy()

        # Draw existing points
        for i, point in enumerate(self.click_points):
            cv2.circle(display_frame, point, 8, (0, 255, 0), -1)
            cv2.circle(display_frame, point, 12, (0, 255, 0), 2)

        # Draw rectangle if we have both points
        if len(self.click_points) == 2:
            cv2.rectangle(display_frame, self.click_points[0], self.click_points[1],
                         (0, 255, 255), 3)

        # Convert to QPixmap
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)

        # Scale to fit
        scaled = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)

    def on_mouse_click(self, event):
        """Handle mouse click on image."""
        if self.current_frame is None or len(self.click_points) >= 2:
            return

        # Get click position relative to image
        pixmap = self.image_label.pixmap()
        if pixmap is None:
            return

        # Calculate offset due to centering
        label_rect = self.image_label.rect()
        pixmap_rect = pixmap.rect()

        x_offset = (label_rect.width() - pixmap_rect.width()) // 2
        y_offset = (label_rect.height() - pixmap_rect.height()) // 2

        click_x = event.x() - x_offset
        click_y = event.y() - y_offset

        # Check if click is within pixmap
        if click_x < 0 or click_y < 0 or click_x >= pixmap_rect.width() or click_y >= pixmap_rect.height():
            return

        # Scale to original frame coordinates
        scale_x = self.current_frame.shape[1] / pixmap_rect.width()
        scale_y = self.current_frame.shape[0] / pixmap_rect.height()

        frame_x = int(click_x * scale_x)
        frame_y = int(click_y * scale_y)

        self.click_points.append((frame_x, frame_y))
        self.reset_btn.setEnabled(True)

        if len(self.click_points) == 1:
            self.instruction_label.setText("Click the BOTTOM-RIGHT corner of the goal region")
        elif len(self.click_points) == 2:
            self.instruction_label.setText("Perfect! Click 'Save' or adjust points")
            # Add save button
            self.save_btn = QPushButton("✓ Save Calibration")
            self.save_btn.clicked.connect(self.save_calibration)
            self.save_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2ECC71;
                }
            """)
            self.layout().itemAt(2).addWidget(self.save_btn)

        self.update_display()

    def reset_calibration(self):
        """Reset calibration points."""
        self.click_points = []
        self.step = 0
        self.instruction_label.setText("Click the TOP-LEFT corner of the goal region")
        self.reset_btn.setEnabled(False)

        # Remove save button if it exists
        if hasattr(self, 'save_btn'):
            self.save_btn.deleteLater()
            delattr(self, 'save_btn')

        self.update_display()

    def save_calibration(self):
        """Save the calibration and close dialog."""
        if len(self.click_points) == 2:
            x1, y1 = self.click_points[0]
            x2, y2 = self.click_points[1]

            # Ensure proper ordering
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            self.calibration_complete.emit((x1, y1, x2, y2))
            self.accept()


class SettingsDialog(QDialog):
    """Settings dialog with tabs."""

    def __init__(self, parent=None, video_thread=None):
        super().__init__(parent)
        self.video_thread = video_thread
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(600, 500)

        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()

        # Detection tab
        tabs.addTab(self.create_detection_tab(), "🔍 Detection")

        # Visual tab
        tabs.addTab(self.create_visual_tab(), "🎨 Visual")

        # Recording tab
        tabs.addTab(self.create_recording_tab(), "🎬 Recording")

        # Camera tab
        tabs.addTab(self.create_camera_tab(), "📹 Camera")

        # About tab
        tabs.addTab(self.create_about_tab(), "ℹ️ About")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setStyleSheet("""
            * {
                font-family: 'Open Sans', 'Segoe UI', Arial, sans-serif;
            }
            QDialog {
                background-color: #071A2F;
            }
            QTabWidget::pane {
                border: 2px solid #1C77C3;
                background-color: #0A2463;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2C3E50;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-family: 'Campton', 'Montserrat', 'Arial Black', sans-serif;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #1C77C3;
            }
            QLabel {
                color: white;
            }
            QCheckBox {
                color: white;
            }
            QGroupBox {
                color: white;
                font-family: 'Campton', 'Montserrat', 'Arial Black', sans-serif;
                font-weight: bold;
            }
            QPushButton {
                background-color: #3E92CC;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5DADE2;
            }
        """)

    def create_detection_tab(self):
        """Create detection settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Presets
        presets_group = QGroupBox("Detection Presets")
        presets_layout = QHBoxLayout()

        high_sens_btn = QPushButton("High Sensitivity")
        high_sens_btn.clicked.connect(lambda: self.apply_preset("high"))
        presets_layout.addWidget(high_sens_btn)

        standard_btn = QPushButton("Standard")
        standard_btn.clicked.connect(lambda: self.apply_preset("standard"))
        presets_layout.addWidget(standard_btn)

        low_noise_btn = QPushButton("Low Noise")
        low_noise_btn.clicked.connect(lambda: self.apply_preset("low_noise"))
        presets_layout.addWidget(low_noise_btn)

        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)

        # Manual controls with sliders
        manual_group = QGroupBox("Manual Adjustment")
        manual_layout = QVBoxLayout()

        # Cooldown slider
        cooldown_label = QLabel(f"Cooldown: {self.video_thread.cooldown_frames if self.video_thread else 45} frames")
        manual_layout.addWidget(cooldown_label)

        self.cooldown_slider = QSlider(Qt.Horizontal)
        self.cooldown_slider.setMinimum(1)
        self.cooldown_slider.setMaximum(120)
        self.cooldown_slider.setValue(self.video_thread.cooldown_frames if self.video_thread else 45)
        self.cooldown_slider.valueChanged.connect(
            lambda v: self.update_detection_value('cooldown', v, cooldown_label)
        )
        manual_layout.addWidget(self.cooldown_slider)

        # Sensitivity slider
        sens_label = QLabel(f"Motion Threshold: {self.video_thread.motion_threshold if self.video_thread else 30}")
        manual_layout.addWidget(sens_label)

        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setMinimum(1)
        self.sensitivity_slider.setMaximum(100)
        self.sensitivity_slider.setValue(self.video_thread.motion_threshold if self.video_thread else 30)
        self.sensitivity_slider.valueChanged.connect(
            lambda v: self.update_detection_value('sensitivity', v, sens_label)
        )
        manual_layout.addWidget(self.sensitivity_slider)

        # Min size slider
        size_label = QLabel(f"Min Contour Size: {self.video_thread.min_contour_area if self.video_thread else 100} px")
        manual_layout.addWidget(size_label)

        self.minsize_slider = QSlider(Qt.Horizontal)
        self.minsize_slider.setMinimum(10)
        self.minsize_slider.setMaximum(1000)
        self.minsize_slider.setValue(self.video_thread.min_contour_area if self.video_thread else 100)
        self.minsize_slider.valueChanged.connect(
            lambda v: self.update_detection_value('minsize', v, size_label)
        )
        manual_layout.addWidget(self.minsize_slider)

        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)

        layout.addStretch()
        return widget

    def create_visual_tab(self):
        """Create visual settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Trail color selection with swatches
        trail_group = QGroupBox("Motion Trail Color (Modes 1 & 2)")
        trail_layout = QVBoxLayout()

        color_label = QLabel("Select trail color:")
        trail_layout.addWidget(color_label)

        # Create color swatches in a grid
        swatch_widget = QWidget()
        swatch_layout = QHBoxLayout(swatch_widget)
        swatch_layout.setSpacing(8)

        self.color_buttons = QButtonGroup()
        if self.video_thread:
            for i, (color_bgr, color_name) in enumerate(self.video_thread.trail_colors):
                btn = QPushButton()
                btn.setFixedSize(50, 50)
                r, g, b = color_bgr[2], color_bgr[1], color_bgr[0]  # BGR to RGB
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgb({r}, {g}, {b});
                        border: 3px solid {'#5DADE2' if i == self.video_thread.trail_color_index else '#2C3E50'};
                        border-radius: 25px;
                    }}
                    QPushButton:hover {{
                        border: 3px solid #1C77C3;
                    }}
                """)
                btn.setCheckable(True)
                btn.setChecked(i == self.video_thread.trail_color_index)
                self.color_buttons.addButton(btn, i)
                swatch_layout.addWidget(btn)

        self.color_buttons.buttonClicked[int].connect(self.update_trail_color)
        trail_layout.addWidget(swatch_widget)

        trail_group.setLayout(trail_layout)
        layout.addWidget(trail_group)

        # Mode-specific settings
        mode_settings_group = QGroupBox("Visualization Parameters")
        mode_settings_layout = QVBoxLayout()

        # Trail size (Mode 1)
        trail_size_label = QLabel(f"Trail Size (Mode 1): {self.video_thread.trail_size if self.video_thread else 3}")
        mode_settings_layout.addWidget(trail_size_label)

        self.trail_size_slider = QSlider(Qt.Horizontal)
        self.trail_size_slider.setMinimum(1)
        self.trail_size_slider.setMaximum(5)
        self.trail_size_slider.setValue(self.video_thread.trail_size if self.video_thread else 3)
        self.trail_size_slider.valueChanged.connect(
            lambda v: self.update_visual_value('trail_size', v, trail_size_label)
        )
        mode_settings_layout.addWidget(self.trail_size_slider)

        # Long exposure duration (Mode 2)
        exp_duration_label = QLabel(f"Streak Duration (Mode 2): {self.video_thread.long_exposure_duration if self.video_thread else 85}%")
        mode_settings_layout.addWidget(exp_duration_label)

        self.exp_duration_slider = QSlider(Qt.Horizontal)
        self.exp_duration_slider.setMinimum(1)
        self.exp_duration_slider.setMaximum(100)
        self.exp_duration_slider.setValue(self.video_thread.long_exposure_duration if self.video_thread else 85)
        self.exp_duration_slider.valueChanged.connect(
            lambda v: self.update_visual_value('exposure_duration', v, exp_duration_label)
        )
        mode_settings_layout.addWidget(self.exp_duration_slider)

        mode_settings_group.setLayout(mode_settings_layout)
        layout.addWidget(mode_settings_group)

        # Bucket overlay toggle
        overlay_group = QGroupBox("Display Overlays")
        overlay_layout = QVBoxLayout()

        self.show_buckets_check = QCheckBox("Show bucket dividers on video feed")
        # Load current state from video thread
        if self.video_thread:
            self.show_buckets_check.setChecked(self.video_thread.show_bucket_overlay)
        self.show_buckets_check.stateChanged.connect(self.toggle_bucket_overlay)
        overlay_layout.addWidget(self.show_buckets_check)

        self.show_gaussian_check = QCheckBox("Show Gaussian curve on histogram")
        # Load current state from histogram widget
        if self.parent() and hasattr(self.parent(), 'histogram_widget'):
            self.show_gaussian_check.setChecked(self.parent().histogram_widget.show_gaussian)
        self.show_gaussian_check.stateChanged.connect(self.toggle_gaussian_curve)
        overlay_layout.addWidget(self.show_gaussian_check)

        self.show_stats_check = QCheckBox("Show statistics (μ, σ, n) on histogram")
        # Load current state from histogram widget
        if self.parent() and hasattr(self.parent(), 'histogram_widget'):
            self.show_stats_check.setChecked(self.parent().histogram_widget.show_stats_on_graph)
        self.show_stats_check.stateChanged.connect(self.toggle_stats_on_graph)
        overlay_layout.addWidget(self.show_stats_check)

        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)

        layout.addStretch()
        return widget

    def create_recording_tab(self):
        """Create recording settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Output location
        location_group = QGroupBox("Output Location")
        location_layout = QVBoxLayout()

        location_label = QLabel("Recordings are saved to:")
        location_layout.addWidget(location_label)

        import os
        self.output_path_label = QLabel(os.path.abspath('.'))
        self.output_path_label.setStyleSheet("color: #5DADE2; font-weight: bold;")
        self.output_path_label.setWordWrap(True)
        location_layout.addWidget(self.output_path_label)

        browse_btn = QPushButton("Change Output Folder...")
        browse_btn.clicked.connect(self.change_output_folder)
        location_layout.addWidget(browse_btn)

        location_group.setLayout(location_layout)
        layout.addWidget(location_group)

        # Format info
        format_group = QGroupBox("Recording Format")
        format_layout = QVBoxLayout()

        format_info = QLabel("• Format: MP4 (mp4v codec)\n"
                            "• Resolution: Original camera resolution\n"
                            "• Frame Rate: Matches camera FPS (~30 FPS)\n"
                            "• Filename: galton_recording_YYYYMMDD_HHMMSS.mp4")
        format_info.setWordWrap(True)
        format_layout.addWidget(format_info)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # Recording mode
        mode_group = QGroupBox("Recording Mode")
        mode_layout = QVBoxLayout()

        self.record_full_ui_check = QCheckBox("Record Full UI (with bucket overlay)")
        # Load current state from parent
        if self.parent() and hasattr(self.parent(), 'record_full_ui'):
            self.record_full_ui_check.setChecked(self.parent().record_full_ui)
        else:
            self.record_full_ui_check.setChecked(True)  # Default to full UI
        self.record_full_ui_check.setToolTip(
            "Checked: Record camera feed with bucket dividers and overlays\n"
            "Unchecked: Record clean video (camera + trails only, no overlays)"
        )
        self.record_full_ui_check.stateChanged.connect(self.toggle_record_mode)
        mode_layout.addWidget(self.record_full_ui_check)

        mode_info = QLabel("Tip: Uncheck for clean videos perfect for sharing.\n"
                          "The histogram is never included in recordings.")
        mode_info.setWordWrap(True)
        mode_info.setStyleSheet("color: #BDC3C7; font-style: italic;")
        mode_layout.addWidget(mode_info)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        layout.addStretch()
        return widget

    def create_about_tab(self):
        """Create about tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
            <h2 style='color: #1C77C3;'>Galton's Goalie - Science Edition</h2>
            <p style='color: white;'><b>Version:</b> 2.0 (Qt Professional Edition)</p>

            <p style='color: #BDC3C7;'>
            A beautiful, market-ready computer vision application for tracking
            balls through a Galton board and visualizing probability distributions.
            </p>

            <h3 style='color: #3E92CC;'>Features:</h3>
            <ul style='color: #BDC3C7;'>
                <li>Real-time ball tracking with OpenCV</li>
                <li>4 visualization modes (Standard, Trails, Long Exposure, Ultra-Long Exposure)</li>
                <li>Live histogram with Gaussian curve overlay</li>
                <li>Statistical analysis (μ, σ, sample size)</li>
                <li>MP4 video recording</li>
                <li>CSV data export</li>
                <li>Interactive calibration</li>
            </ul>

            <h3 style='color: #3E92CC;'>Credits:</h3>
            <p style='color: #BDC3C7;'>
            <b>Design Inspiration:</b> Mark Rober's clean science communication aesthetic<br>
            <b>Concept:</b> Sir Francis Galton's original Galton Board (1889)<br>
            <b>Built with:</b> PyQt5, OpenCV, NumPy, Python
            </p>

            <p style='color: white; margin-top: 20px;'>
            <b>MIT License</b> - Free to use, modify, and distribute!
            </p>
        """)
        layout.addWidget(about_text)

        return widget

    def create_camera_tab(self):
        """Create camera settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Camera selection
        camera_group = QGroupBox("Camera Selection")
        camera_layout = QVBoxLayout()

        info_label = QLabel("Select which camera to use:")
        camera_layout.addWidget(info_label)

        # Camera dropdown - will populate when clicked
        self.camera_combo = QComboBox()
        self.camera_combo_populated = False

        # Add only the current camera initially for instant load
        if self.video_thread:
            self.camera_combo.addItem(f"Camera {self.video_thread.camera_index}", self.video_thread.camera_index)

        # Detect cameras when user opens the dropdown (lazy loading)
        self.camera_combo.showPopup = self.on_camera_dropdown_open

        camera_layout.addWidget(self.camera_combo)

        # Apply button
        apply_btn = QPushButton("Apply Camera Change")
        apply_btn.clicked.connect(self.apply_camera_change)
        camera_layout.addWidget(apply_btn)

        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)

        # Camera options
        options_group = QGroupBox("Camera Options")
        options_layout = QVBoxLayout()

        self.flip_horizontal_check = QCheckBox("Flip camera horizontally")
        if self.video_thread:
            self.flip_horizontal_check.setChecked(self.video_thread.flip_horizontal)
        self.flip_horizontal_check.stateChanged.connect(self.toggle_horizontal_flip)
        options_layout.addWidget(self.flip_horizontal_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Camera info
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout()

        info_text = QLabel(
            "• Changing cameras will restart the video feed\n"
            "• Current detection settings will be preserved\n"
            "• You may need to recalibrate the goal region\n"
            "• Default camera is usually Camera 0"
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()
        return widget

    def on_camera_dropdown_open(self):
        """Lazy load cameras when dropdown is opened."""
        # Only populate once
        if not self.camera_combo_populated:
            self.camera_combo_populated = True
            current_camera = self.video_thread.camera_index if self.video_thread else 0

            # Clear and repopulate
            self.camera_combo.clear()
            available_cameras = self.detect_cameras()

            for idx, name in available_cameras:
                self.camera_combo.addItem(name, idx)

            # Set current camera
            current_idx = self.camera_combo.findData(current_camera)
            if current_idx >= 0:
                self.camera_combo.setCurrentIndex(current_idx)

        # Call the original showPopup
        QComboBox.showPopup(self.camera_combo)

    def detect_cameras(self):
        """Detect available cameras on the system."""
        available_cameras = []

        # Try up to 10 camera indices
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Camera is available
                available_cameras.append((i, f"Camera {i}"))
                cap.release()
            else:
                # Stop checking after first unavailable camera
                if i > 0:  # Allow checking at least camera 0 and 1
                    break

        # If no cameras found, add default
        if not available_cameras:
            available_cameras.append((0, "Camera 0 (Default)"))

        return available_cameras

    def apply_camera_change(self):
        """Apply camera change and restart video thread."""
        new_camera_idx = self.camera_combo.currentData()

        if new_camera_idx is None:
            return

        # Confirm with user
        msg_box = create_styled_message_box(
            self,
            "Change Camera",
            f"Switch to Camera {new_camera_idx}?\n\nThis will restart the video feed.",
            QMessageBox.Question,
            QMessageBox.Yes | QMessageBox.No
        )
        reply = msg_box.exec_()

        if reply == QMessageBox.Yes:
            # Store new camera index
            if self.parent():
                self.parent().change_camera(new_camera_idx)

    def load_current_settings(self):
        """Load current settings from video thread."""
        pass  # Settings are already applied via sliders in main window

    def update_detection_value(self, param_type, value, label):
        """Update detection parameter and label."""
        if not self.video_thread:
            return

        if param_type == 'cooldown':
            self.video_thread.cooldown_frames = value
            label.setText(f"Cooldown: {value} frames")
        elif param_type == 'sensitivity':
            self.video_thread.motion_threshold = value
            label.setText(f"Motion Threshold: {value}")
        elif param_type == 'minsize':
            self.video_thread.min_contour_area = value
            label.setText(f"Min Contour Size: {value} px")

    def update_visual_value(self, param_type, value, label):
        """Update visual parameter and label."""
        if not self.video_thread:
            return

        if param_type == 'trail_size':
            self.video_thread.trail_size = value
            label.setText(f"Trail Size (Mode 1): {value}")
        elif param_type == 'exposure_duration':
            self.video_thread.long_exposure_duration = value
            label.setText(f"Streak Duration (Mode 2): {value}%")

    def update_trail_color(self, index):
        """Update trail color selection."""
        if self.video_thread:
            self.video_thread.trail_color_index = index
            # Update button styling
            for i, (color_bgr, _) in enumerate(self.video_thread.trail_colors):
                btn = self.color_buttons.button(i)
                if btn:
                    r, g, b = color_bgr[2], color_bgr[1], color_bgr[0]
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: rgb({r}, {g}, {b});
                            border: 3px solid {'#5DADE2' if i == index else '#2C3E50'};
                            border-radius: 25px;
                        }}
                        QPushButton:hover {{
                            border: 3px solid #1C77C3;
                        }}
                    """)

    def toggle_bucket_overlay(self, state):
        """Toggle bucket divider overlay on video feed."""
        if self.video_thread:
            self.video_thread.show_bucket_overlay = (state == Qt.Checked)

    def toggle_horizontal_flip(self, state):
        """Toggle horizontal flip of camera feed."""
        if self.video_thread:
            self.video_thread.flip_horizontal = (state == Qt.Checked)

    def toggle_gaussian_curve(self, state):
        """Toggle Gaussian curve on histogram."""
        # Need to access parent's histogram widget
        if self.parent():
            self.parent().histogram_widget.show_gaussian = (state == Qt.Checked)
            self.parent().histogram_widget.update()

    def toggle_stats_on_graph(self, state):
        """Toggle statistics display on histogram."""
        if self.parent():
            self.parent().histogram_widget.show_stats_on_graph = (state == Qt.Checked)
            self.parent().histogram_widget.update()

    def toggle_record_mode(self, state):
        """Toggle recording mode between full UI and clean video."""
        if self.parent():
            self.parent().record_full_ui = (state == Qt.Checked)

    def change_output_folder(self):
        """Change output folder for recordings."""
        from PyQt5.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_path_label.setText(folder)
            # Store for later use when recording
            if self.parent():
                self.parent().recording_output_folder = folder

    def apply_preset(self, preset_name):
        """Apply detection preset."""
        if not self.video_thread:
            return

        if preset_name == "high":
            cooldown, threshold, min_area = 10, 15, 50
        elif preset_name == "standard":
            cooldown, threshold, min_area = DEFAULT_COOLDOWN_FRAMES, DEFAULT_MOTION_THRESHOLD, DEFAULT_MIN_CONTOUR_AREA
        elif preset_name == "low_noise":
            cooldown, threshold, min_area = 30, 50, 200
        else:
            return

        self.video_thread.motion_threshold = threshold
        self.video_thread.min_contour_area = min_area
        self.video_thread.cooldown_frames = cooldown

        # Update sliders in dialog
        self.cooldown_slider.setValue(cooldown)
        self.sensitivity_slider.setValue(threshold)
        self.minsize_slider.setValue(min_area)

        msg_box = create_styled_message_box(
            self,
            "Preset Applied",
            f"Applied '{preset_name.replace('_', ' ').title()}' preset!"
        )
        msg_box.exec_()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        if self.video_thread:
            self.video_thread.motion_threshold = DEFAULT_MOTION_THRESHOLD
            self.video_thread.min_contour_area = DEFAULT_MIN_CONTOUR_AREA
            self.video_thread.cooldown_frames = DEFAULT_COOLDOWN_FRAMES

            # Update sliders
            self.cooldown_slider.setValue(DEFAULT_COOLDOWN_FRAMES)
            self.sensitivity_slider.setValue(DEFAULT_MOTION_THRESHOLD)
            self.minsize_slider.setValue(DEFAULT_MIN_CONTOUR_AREA)

        msg_box = create_styled_message_box(self, "Reset", "All settings reset to defaults!")
        msg_box.exec_()


class HelpOverlay(QDialog):
    """Help overlay showing keyboard shortcuts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setModal(False)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(500, 600)

        self.setup_ui()

    def setup_ui(self):
        """Setup the help UI."""
        layout = QVBoxLayout(self)

        # Apply dialog-wide stylesheet
        self.setStyleSheet("""
            * {
                font-family: 'Open Sans', 'Segoe UI', Arial, sans-serif;
            }
            QDialog {
                background-color: #071A2F;
            }
        """)

        # Title
        title = QLabel("⌨️ KEYBOARD SHORTCUTS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-family: 'Campton', 'Montserrat', 'Arial Black', sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #1C77C3;
                padding: 15px;
            }
        """)
        layout.addWidget(title)

        # Shortcuts content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        content = QWidget()
        content_layout = QVBoxLayout(content)

        shortcuts = [
            ("GENERAL", [
                ("H or ?", "Show this help"),
                ("Esc", "Close dialogs"),
                ("Ctrl+S", "Save configuration"),
                ("Ctrl+Q", "Quit application"),
            ]),
            ("Modes", [
                ("1", "Standard mode"),
                ("2", "Motion trails mode"),
                ("3", "Long exposure mode"),
                ("4", "Ultra-long exposure mode"),
            ]),
            ("Controls", [
                ("Space / P", "Pause/Resume counting"),
                ("R", "Reset all data"),
                ("C", "Open calibration dialog"),
                ("S", "Open settings dialog"),
            ]),
            ("Recording", [
                ("V", "Start/Stop recording"),
                ("E", "Export session to CSV"),
            ]),
        ]

        for category, items in shortcuts:
            # Category header
            cat_label = QLabel(category)
            cat_label.setStyleSheet("""
                QLabel {
                    font-family: 'Campton', 'Montserrat', 'Arial Black', sans-serif;
                    font-size: 13px;
                    font-weight: bold;
                    color: #3E92CC;
                    padding: 10px 5px 5px 5px;
                }
            """)
            content_layout.addWidget(cat_label)

            # Shortcuts in category
            for key, description in items:
                shortcut_widget = QWidget()
                shortcut_layout = QHBoxLayout(shortcut_widget)
                shortcut_layout.setContentsMargins(10, 5, 10, 5)

                key_label = QLabel(key)
                key_label.setStyleSheet("""
                    QLabel {
                        background-color: #2C3E50;
                        color: white;
                        padding: 5px 10px;
                        border-radius: 4px;
                        font-family: 'Courier New';
                        font-weight: bold;
                        min-width: 80px;
                    }
                """)

                desc_label = QLabel(description)
                desc_label.setStyleSheet("""
                    QLabel {
                        color: #BDC3C7;
                        padding-left: 15px;
                    }
                """)

                shortcut_layout.addWidget(key_label)
                shortcut_layout.addWidget(desc_label)
                shortcut_layout.addStretch()

                content_layout.addWidget(shortcut_widget)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3E92CC;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5DADE2;
            }
        """)
        layout.addWidget(close_btn)

        self.setStyleSheet("""
            QDialog {
                background-color: #071A2F;
            }
        """)

    def keyPressEvent(self, event):
        """Handle key presses."""
        if event.key() in (Qt.Key_Escape, Qt.Key_H, Qt.Key_Question):
            self.accept()
        else:
            super().keyPressEvent(event)


def create_styled_message_box(parent, title, text, icon=QMessageBox.Information, buttons=QMessageBox.Ok):
    """Create a QMessageBox with dark theme styling."""
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setStandardButtons(buttons)
    msg_box.setIcon(icon)

    # Apply dark theme styling
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #071A2F;
        }
        QMessageBox QLabel {
            color: white;
            font-size: 13px;
            min-width: 300px;
        }
        QPushButton {
            background-color: #2C3E50;
            color: white;
            border: 1px solid #3E92CC;
            border-radius: 4px;
            padding: 8px 16px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #1C77C3;
        }
    """)

    return msg_box


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Galton's Goalie - Science Edition")
        self.setGeometry(100, 100, 1400, 900)

        # Application state
        self.bucket_counts = [0] * NUM_BUCKETS
        self.goal_region = None
        self.calibrating = False
        self.recording = False
        self.sidebar_collapsed = False
        self.video_writer = None
        self.record_filename = None
        self.current_frame = None  # Store latest frame for calibration
        self.recording_output_folder = "."  # Default to current directory
        self.record_full_ui = True  # True = record with overlays, False = clean video only

        # Load camera index from config before creating video thread
        camera_index = 0  # Default camera
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    camera_index = config.get('camera_index', 0)
            except Exception as e:
                print(f"Could not load camera index from config: {e}")

        # Video thread
        self.video_thread = VideoThread(camera_index=camera_index)
        self.video_thread.frame_ready.connect(self.on_frame_ready)
        self.video_thread.detection_update.connect(self.on_detection)
        self.video_thread.fps_update.connect(self.on_fps_update)

        # Load full configuration
        self.load_config()

        # Setup UI
        self.init_ui()
        self.apply_stylesheet()

        # Timer for histogram glow updates
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.update_histogram_glow)
        self.glow_timer.start(33)  # ~30 FPS for smooth glow animation

        # Start video thread
        self.video_thread.start()

    def init_ui(self):
        """Initialize the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar
        self.create_top_bar(main_layout)

        # Content area (sidebar + visualization + histogram)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.create_sidebar(content_layout)

        # Right side (visualization + histogram)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        # Visualization widget
        self.viz_widget = VisualizationWidget()
        right_layout.addWidget(self.viz_widget, stretch=1)

        # Histogram widget
        self.histogram_widget = HistogramWidget()
        right_layout.addWidget(self.histogram_widget)

        content_layout.addLayout(right_layout, stretch=1)
        main_layout.addLayout(content_layout, stretch=1)

    def create_top_bar(self, parent_layout):
        """Create the top bar with branding and status."""
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(60)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 10, 20, 10)

        # App title
        title_label = QLabel("Galton's Goalie")
        title_label.setObjectName("appTitle")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title_label)

        subtitle_label = QLabel("Science Edition")
        subtitle_label.setObjectName("appSubtitle")
        subtitle_label.setFont(QFont("Arial", 9))
        layout.addWidget(subtitle_label)

        layout.addStretch()

        # Mode indicator
        self.mode_label = QLabel("Mode: Standard")
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.mode_label)

        layout.addSpacing(30)

        # FPS counter
        self.fps_label = QLabel("60 FPS")
        self.fps_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.fps_label)

        # Recording indicator
        self.rec_label = QLabel("REC")
        self.rec_label.setObjectName("recLabel")
        self.rec_label.setVisible(False)
        layout.addWidget(self.rec_label)

        parent_layout.addWidget(top_bar)

    def create_sidebar(self, parent_layout):
        """Create the left sidebar with controls."""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Mode Selection
        mode_group = QGroupBox("Mode Selection")
        mode_group.setObjectName("sidebarGroup")
        mode_layout = QVBoxLayout()

        self.mode_buttons = QButtonGroup(self)
        mode_names = ["Standard", "Motion Trails", "Long Exposure", "Ultra-Long Exp"]

        for i, name in enumerate(mode_names):
            radio = QRadioButton(name)
            radio.setObjectName("modeRadio")
            self.mode_buttons.addButton(radio, i)
            mode_layout.addWidget(radio)

        self.mode_buttons.button(0).setChecked(True)
        self.mode_buttons.buttonClicked.connect(self.on_mode_changed)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Controls
        controls_group = QGroupBox("Controls")
        controls_group.setObjectName("sidebarGroup")
        controls_layout = QVBoxLayout()

        # Cooldown slider
        controls_layout.addWidget(QLabel("Cooldown (frames)"))
        self.cooldown_slider = QSlider(Qt.Horizontal)
        self.cooldown_slider.setRange(1, 120)
        self.cooldown_slider.setValue(DEFAULT_COOLDOWN_FRAMES)
        self.cooldown_slider.valueChanged.connect(self.on_cooldown_changed)
        controls_layout.addWidget(self.cooldown_slider)

        self.cooldown_label = QLabel(f"{DEFAULT_COOLDOWN_FRAMES} frames")
        self.cooldown_label.setObjectName("sliderValue")
        controls_layout.addWidget(self.cooldown_label)

        controls_layout.addSpacing(10)

        # Sensitivity slider
        controls_layout.addWidget(QLabel("Sensitivity"))
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setRange(1, 100)
        self.sensitivity_slider.setValue(DEFAULT_MOTION_THRESHOLD)
        self.sensitivity_slider.valueChanged.connect(self.on_sensitivity_changed)
        controls_layout.addWidget(self.sensitivity_slider)

        self.sensitivity_label = QLabel(str(DEFAULT_MOTION_THRESHOLD))
        self.sensitivity_label.setObjectName("sliderValue")
        controls_layout.addWidget(self.sensitivity_label)

        controls_layout.addSpacing(10)

        # Min Size slider
        controls_layout.addWidget(QLabel("Min Size (pixels)"))
        self.min_size_slider = QSlider(Qt.Horizontal)
        self.min_size_slider.setRange(10, 1000)
        self.min_size_slider.setValue(DEFAULT_MIN_CONTOUR_AREA)
        self.min_size_slider.valueChanged.connect(self.on_min_size_changed)
        controls_layout.addWidget(self.min_size_slider)

        self.min_size_label = QLabel(f"{DEFAULT_MIN_CONTOUR_AREA} px")
        self.min_size_label.setObjectName("sliderValue")
        controls_layout.addWidget(self.min_size_label)

        controls_group.setLayout(controls_layout)
        controls_group.hide()  # Hide controls panel
        layout.addWidget(controls_group)

        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_group.setObjectName("sidebarGroup")
        actions_layout = QVBoxLayout()

        self.calibrate_btn = QPushButton("🎯 Calibrate (C)")
        self.calibrate_btn.setObjectName("primaryButton")
        self.calibrate_btn.clicked.connect(self.on_calibrate_clicked)
        actions_layout.addWidget(self.calibrate_btn)

        self.pause_btn = QPushButton("⏸ Pause (P)")
        self.pause_btn.setObjectName("secondaryButton")
        self.pause_btn.clicked.connect(self.on_pause_clicked)
        actions_layout.addWidget(self.pause_btn)

        self.reset_btn = QPushButton("🔄 Reset Data (R)")
        self.reset_btn.setObjectName("secondaryButton")
        self.reset_btn.clicked.connect(self.on_reset_clicked)
        actions_layout.addWidget(self.reset_btn)

        self.export_btn = QPushButton("💾 Export Session (E)")
        self.export_btn.setObjectName("secondaryButton")
        self.export_btn.clicked.connect(self.on_export_clicked)
        actions_layout.addWidget(self.export_btn)

        self.record_btn = QPushButton("🎬 Start Recording (V)")
        self.record_btn.setObjectName("secondaryButton")
        self.record_btn.clicked.connect(self.on_record_clicked)
        actions_layout.addWidget(self.record_btn)

        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.setObjectName("secondaryButton")
        self.settings_btn.clicked.connect(self.on_settings_clicked)
        actions_layout.addWidget(self.settings_btn)

        self.help_btn = QPushButton("❓ Help (H)")
        self.help_btn.setObjectName("secondaryButton")
        self.help_btn.clicked.connect(self.on_help_clicked)
        actions_layout.addWidget(self.help_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_group.setObjectName("sidebarGroup")
        stats_layout = QVBoxLayout()

        self.total_label = QLabel("Total Hits: 0")
        self.camera_label = QLabel(f"Camera: #{self.video_thread.camera_index}")
        self.mean_label = QLabel("Mean: μ = 0.0")
        self.stddev_label = QLabel("Std Dev: σ = 0.0")

        for label in [self.total_label, self.camera_label, self.mean_label, self.stddev_label]:
            label.setObjectName("statLabel")
            stats_layout.addWidget(label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

        parent_layout.addWidget(sidebar)

    def apply_stylesheet(self):
        """Apply custom Qt stylesheet."""
        stylesheet = """
            * {
                font-family: 'Open Sans', 'Segoe UI', Arial, sans-serif;
            }

            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #071A2F, stop:1 #0A2463);
            }

            #topBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0A2463, stop:1 #071A2F);
                border-bottom: 2px solid #1C77C3;
            }

            #appTitle {
                color: white;
                font-family: 'Campton', 'Montserrat', 'Arial Black', sans-serif;
            }

            #appSubtitle {
                color: #BDC3C7;
                font-family: 'Campton', 'Montserrat', 'Arial Black', sans-serif;
            }

            #modeLabel {
                background-color: #1C77C3;
                color: #071A2F;
                padding: 5px 15px;
                border-radius: 4px;
                font-family: 'Campton', 'Montserrat', 'Arial Black', sans-serif;
            }

            #recLabel {
                background-color: #C0392B;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            }

            #sidebar {
                background-color: rgba(44, 62, 80, 0.85);
                border-right: 2px solid #1C77C3;
            }

            QGroupBox {
                color: #BDC3C7;
                font-family: 'Campton', 'Montserrat', 'Arial Black', sans-serif;
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #34495E;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                font-family: 'Campton', 'Montserrat', 'Arial Black', sans-serif;
            }

            #sidebarGroup {
                background-color: rgba(10, 36, 99, 0.5);
            }

            QRadioButton {
                color: white;
                spacing: 8px;
            }

            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #3E92CC;
                background-color: transparent;
            }

            QRadioButton::indicator:checked {
                background-color: #1C77C3;
                border: 2px solid #5DADE2;
            }

            QLabel {
                color: white;
            }

            #sliderValue {
                color: #5DADE2;
                font-family: 'Courier New';
                font-weight: bold;
            }

            #statLabel {
                color: #BDC3C7;
                font-family: 'Courier New';
                font-size: 10px;
            }

            QSlider::groove:horizontal {
                border: 1px solid #071A2F;
                height: 6px;
                background: #0A2463;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #1C77C3;
                border: 2px solid #5DADE2;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }

            QSlider::handle:horizontal:hover {
                background: #5DADE2;
            }

            QSlider::sub-page:horizontal {
                background: #3E92CC;
                border-radius: 3px;
            }

            QPushButton {
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }

            #primaryButton {
                background-color: #3E92CC;
            }

            #primaryButton:hover {
                background-color: #5DADE2;
            }

            #primaryButton:pressed {
                background-color: #1C77C3;
            }

            #secondaryButton {
                background-color: #2C3E50;
            }

            #secondaryButton:hover {
                background-color: #34495E;
            }

            #secondaryButton:pressed {
                background-color: #1C77C3;
            }
        """
        self.setStyleSheet(stylesheet)

    @pyqtSlot(np.ndarray)
    def on_frame_ready(self, frame):
        """Handle new frame from video thread."""
        self.current_frame = frame.copy()  # Store for calibration dialog

        # Add pause indicator overlay if paused
        display_frame = frame.copy()
        if self.video_thread.paused:
            # Draw semi-transparent overlay
            overlay = display_frame.copy()
            h, w = display_frame.shape[:2]

            # Draw pause symbol (two vertical bars)
            bar_width = 40
            bar_height = 120
            bar_gap = 30
            center_x = w // 2
            center_y = h // 2

            # Left bar
            cv2.rectangle(overlay,
                         (center_x - bar_gap - bar_width, center_y - bar_height // 2),
                         (center_x - bar_gap, center_y + bar_height // 2),
                         (255, 255, 255), -1)

            # Right bar
            cv2.rectangle(overlay,
                         (center_x + bar_gap, center_y - bar_height // 2),
                         (center_x + bar_gap + bar_width, center_y + bar_height // 2),
                         (255, 255, 255), -1)

            # Blend overlay with original frame
            cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0, display_frame)

            # Add "PAUSED" text
            font = cv2.FONT_HERSHEY_SIMPLEX
            text = "PAUSED"
            font_scale = 2.0
            thickness = 4
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = (w - text_size[0]) // 2
            text_y = center_y + bar_height // 2 + 80

            # Draw text with black outline
            cv2.putText(display_frame, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness + 2)
            cv2.putText(display_frame, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)

        self.viz_widget.update_frame(display_frame)

        # Write to video file if recording (write original frame without pause overlay)
        if self.recording and self.video_writer is not None:
            # Choose which frame to record based on mode
            if self.record_full_ui:
                # Record full UI - capture entire application window
                self.record_full_ui_frame()
            else:
                # Record clean video (camera + trails only, no overlays)
                if self.video_thread.clean_frame is not None:
                    self.video_writer.write(self.video_thread.clean_frame)
                else:
                    # Fallback to regular frame if clean frame not available
                    self.video_writer.write(frame)

    @pyqtSlot(list)
    def on_detection(self, buckets):
        """Handle ball detection."""
        for bucket in buckets:
            self.bucket_counts[bucket] += 1

        self.histogram_widget.update_counts(self.bucket_counts, self.video_thread.glow_counters)
        self.update_statistics()

    @pyqtSlot(float)
    def on_fps_update(self, fps):
        """Update FPS display."""
        self.fps_label.setText(f"{fps:.0f} FPS")

    def update_statistics(self):
        """Update statistics display."""
        total = sum(self.bucket_counts)
        self.total_label.setText(f"Total Hits: {total:,}")

        if total > 0:
            weighted_sum = sum((i + 1) * count for i, count in enumerate(self.bucket_counts))
            mean = weighted_sum / total
            variance = sum(count * ((i + 1) - mean) ** 2
                          for i, count in enumerate(self.bucket_counts)) / total
            std_dev = variance ** 0.5

            self.mean_label.setText(f"Mean: μ = {mean:.2f}")
            self.stddev_label.setText(f"Std Dev: σ = {std_dev:.2f}")

    def update_histogram_glow(self):
        """Update histogram with current glow counters for animation."""
        self.histogram_widget.update_counts(self.bucket_counts, self.video_thread.glow_counters)

    def on_mode_changed(self, button):
        """Handle mode change."""
        mode_id = self.mode_buttons.id(button)
        self.video_thread.trail_mode = mode_id

        mode_names = ["Standard", "Motion Trails", "Long Exposure", "Ultra-Long Exp"]
        self.mode_label.setText(f"Mode: {mode_names[mode_id]}")

        # Hide histogram in ultra-long exposure mode
        if mode_id == 3:
            self.histogram_widget.hide()
        else:
            self.histogram_widget.show()

    def on_cooldown_changed(self, value):
        """Handle cooldown slider change."""
        self.video_thread.cooldown_frames = value
        fps = self.video_thread.fps if self.video_thread.fps > 0 else 30
        seconds = value / fps
        self.cooldown_label.setText(f"{value} frames ({seconds:.2f}s)")

    def on_sensitivity_changed(self, value):
        """Handle sensitivity slider change."""
        self.video_thread.motion_threshold = value
        self.sensitivity_label.setText(str(value))

    def on_min_size_changed(self, value):
        """Handle min size slider change."""
        self.video_thread.min_contour_area = value
        self.min_size_label.setText(f"{value} px")

    def on_pause_clicked(self):
        """Toggle pause state."""
        self.video_thread.paused = not self.video_thread.paused

        if self.video_thread.paused:
            self.pause_btn.setText("▶ Resume (P)")
            self.pause_btn.setObjectName("primaryButton")
        else:
            self.pause_btn.setText("⏸ Pause (P)")
            self.pause_btn.setObjectName("secondaryButton")

        # Reapply stylesheet to update button appearance
        self.pause_btn.style().unpolish(self.pause_btn)
        self.pause_btn.style().polish(self.pause_btn)

    def on_calibrate_clicked(self):
        """Handle calibrate button click."""
        if self.current_frame is None:
            msg_box = create_styled_message_box(
                self,
                "No Frame",
                "Waiting for camera feed... Please try again in a moment.",
                QMessageBox.Warning
            )
            msg_box.exec_()
            return

        # Pause video thread during calibration
        was_paused = self.video_thread.paused
        self.video_thread.paused = True

        # Open calibration dialog
        dialog = CalibrationDialog(self.current_frame, self.goal_region, self)
        dialog.calibration_complete.connect(self.on_calibration_complete)
        dialog.exec_()

        # Resume video thread (restore previous state)
        self.video_thread.paused = was_paused
        if not was_paused:
            self.pause_btn.setText("⏸ Pause (P)")
            self.pause_btn.setObjectName("secondaryButton")
            self.pause_btn.style().unpolish(self.pause_btn)
            self.pause_btn.style().polish(self.pause_btn)

    def on_calibration_complete(self, goal_region):
        """Handle calibration completion."""
        self.goal_region = goal_region
        self.video_thread.goal_region = goal_region
        # Reset prev_frame to avoid size mismatch errors
        self.video_thread.prev_frame = None
        self.save_config()

    def on_reset_clicked(self):
        """Reset all data."""
        msg_box = create_styled_message_box(
            self,
            "Reset Data",
            "Are you sure you want to reset all data?",
            QMessageBox.Question,
            QMessageBox.Yes | QMessageBox.No
        )
        reply = msg_box.exec_()

        if reply == QMessageBox.Yes:
            self.bucket_counts = [0] * NUM_BUCKETS
            self.histogram_widget.update_counts(self.bucket_counts)
            self.video_thread.reset_ultra_long_exposure()
            self.update_statistics()

    def on_export_clicked(self):
        """Export session data."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Session", "", "CSV Files (*.csv)"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("Bucket,Count\n")
                    for i, count in enumerate(self.bucket_counts):
                        f.write(f"{i + 1},{count}\n")

                msg_box = create_styled_message_box(
                    self,
                    "Success",
                    f"Session data exported to:\n{filename}"
                )
                msg_box.exec_()
            except Exception as e:
                msg_box = create_styled_message_box(
                    self,
                    "Error",
                    f"Failed to export data:\n{str(e)}",
                    QMessageBox.Critical
                )
                msg_box.exec_()

    def record_full_ui_frame(self):
        """Capture and record the entire UI window."""
        try:
            from PyQt5.QtGui import QImage

            # Grab the central widget as a pixmap
            pixmap = self.centralWidget().grab()

            # Convert QPixmap to QImage in RGB888 format (consistent format)
            qimage = pixmap.toImage().convertToFormat(QImage.Format_RGB888)

            # Convert QImage to numpy array
            width = qimage.width()
            height = qimage.height()
            ptr = qimage.bits()
            ptr.setsize(height * width * 3)  # 3 bytes per pixel (RGB)
            arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 3))

            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

            # Write to video
            if self.video_writer is not None:
                self.video_writer.write(frame_bgr)
        except Exception as e:
            print(f"Error capturing full UI: {e}")

    def on_record_clicked(self):
        """Toggle recording."""
        self.recording = not self.recording

        if self.recording:
            # Start recording - create video writer
            from datetime import datetime
            import os
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"galton_recording_{timestamp}.mp4"
            self.record_filename = os.path.join(self.recording_output_folder, filename)

            # Get frame dimensions based on recording mode
            if self.record_full_ui:
                # Get dimensions from central widget for full UI recording
                width = self.centralWidget().width()
                height = self.centralWidget().height()
            else:
                # Get dimensions from current frame for clean video recording
                if self.current_frame is not None:
                    height, width = self.current_frame.shape[:2]
                else:
                    width = height = 0

            if width > 0 and height > 0:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                fps = self.video_thread.fps if self.video_thread.fps > 0 else 30.0
                self.video_writer = cv2.VideoWriter(
                    self.record_filename, fourcc, fps, (width, height)
                )

                if self.video_writer.isOpened():
                    self.record_btn.setText("⏹ Stop Recording (V)")
                    self.rec_label.setVisible(True)
                    print(f"Recording started: {self.record_filename}")
                else:
                    msg_box = create_styled_message_box(
                        self,
                        "Recording Error",
                        "Failed to initialize video writer.",
                        QMessageBox.Critical
                    )
                    msg_box.exec_()
                    self.recording = False
            else:
                msg_box = create_styled_message_box(
                    self,
                    "No Frame",
                    "Waiting for camera feed... Please try again.",
                    QMessageBox.Warning
                )
                msg_box.exec_()
                self.recording = False
        else:
            # Stop recording - release video writer
            self.record_btn.setText("🎬 Start Recording (V)")
            self.rec_label.setVisible(False)

            if self.video_writer is not None:
                self.video_writer.release()
                self.video_writer = None
                print(f"Recording stopped: {self.record_filename}")
                self.record_filename = None

    def change_camera(self, camera_index):
        """Change to a different camera."""
        # Stop current video thread
        self.video_thread.stop()

        # Create new video thread with new camera
        self.video_thread = VideoThread(camera_index=camera_index)
        self.video_thread.frame_ready.connect(self.on_frame_ready)
        self.video_thread.detection_update.connect(self.on_detection)
        self.video_thread.fps_update.connect(self.on_fps_update)

        # Restore settings
        self.load_config()

        # Update camera label
        self.camera_label.setText(f"Camera: #{camera_index}")

        # Start new video thread
        self.video_thread.start()

        # Save the new camera index
        self.save_config()

        msg_box = create_styled_message_box(
            self,
            "Camera Changed",
            f"Successfully switched to Camera {camera_index}"
        )
        msg_box.exec_()

    def load_config(self):
        """Load configuration from file."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)

                    # Goal region
                    goal_region = config.get('goal_region')
                    if goal_region and len(goal_region) == 4:
                        self.goal_region = tuple(goal_region)
                        self.video_thread.goal_region = self.goal_region

                    # Camera index
                    if 'camera_index' in config:
                        # This is loaded when creating VideoThread, so just store it
                        pass

                    # Detection settings
                    if 'cooldown_frames' in config:
                        self.video_thread.cooldown_frames = config['cooldown_frames']
                    if 'motion_threshold' in config:
                        self.video_thread.motion_threshold = config['motion_threshold']
                    if 'min_contour_area' in config:
                        self.video_thread.min_contour_area = config['min_contour_area']

                    # Visual settings
                    if 'trail_color_index' in config:
                        self.video_thread.trail_color_index = config['trail_color_index']
                    if 'trail_size' in config:
                        self.video_thread.trail_size = config['trail_size']
                    if 'long_exposure_duration' in config:
                        self.video_thread.long_exposure_duration = config['long_exposure_duration']
                    if 'show_bucket_overlay' in config:
                        self.video_thread.show_bucket_overlay = config['show_bucket_overlay']
                    if 'show_gaussian' in config:
                        self.histogram_widget.show_gaussian = config['show_gaussian']
                    if 'show_stats_on_graph' in config:
                        self.histogram_widget.show_stats_on_graph = config['show_stats_on_graph']
                    if 'flip_horizontal' in config:
                        self.video_thread.flip_horizontal = config['flip_horizontal']

                    # Recording settings
                    if 'recording_output_folder' in config:
                        self.recording_output_folder = config['recording_output_folder']
                    if 'record_full_ui' in config:
                        self.record_full_ui = config['record_full_ui']

            except Exception as e:
                print(f"Could not load config: {e}")

    def save_config(self):
        """Save configuration to file."""
        config = {}

        # Goal region
        if self.goal_region:
            config['goal_region'] = list(self.goal_region)

        # Camera settings
        config['camera_index'] = self.video_thread.camera_index

        # Detection settings
        config['cooldown_frames'] = self.video_thread.cooldown_frames
        config['motion_threshold'] = self.video_thread.motion_threshold
        config['min_contour_area'] = self.video_thread.min_contour_area

        # Visual settings
        config['trail_color_index'] = self.video_thread.trail_color_index
        config['trail_size'] = self.video_thread.trail_size
        config['long_exposure_duration'] = self.video_thread.long_exposure_duration
        config['show_bucket_overlay'] = self.video_thread.show_bucket_overlay
        config['show_gaussian'] = self.histogram_widget.show_gaussian
        config['show_stats_on_graph'] = self.histogram_widget.show_stats_on_graph
        config['flip_horizontal'] = self.video_thread.flip_horizontal

        # Recording settings
        config['recording_output_folder'] = self.recording_output_folder
        config['record_full_ui'] = self.record_full_ui

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Configuration saved to {CONFIG_FILE}")
        except Exception as e:
            print(f"Could not save config: {e}")

    def on_settings_clicked(self):
        """Open settings dialog."""
        dialog = SettingsDialog(parent=self, video_thread=self.video_thread)
        dialog.exec_()
        # Auto-save settings after dialog closes
        self.save_config()

    def on_help_clicked(self):
        """Show help overlay."""
        help_overlay = HelpOverlay(self)
        help_overlay.exec_()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()
        modifiers = event.modifiers()

        # Ctrl+Q - Quit
        if modifiers == Qt.ControlModifier and key == Qt.Key_Q:
            self.close()

        # Ctrl+S - Save config
        elif modifiers == Qt.ControlModifier and key == Qt.Key_S:
            self.save_config()
            msg_box = create_styled_message_box(self, "Saved", "Configuration saved successfully!")
            msg_box.exec_()

        # H or ? - Help
        elif key == Qt.Key_H or key == Qt.Key_Question:
            self.on_help_clicked()

        # S - Settings
        elif key == Qt.Key_S and modifiers == Qt.NoModifier:
            self.on_settings_clicked()

        # C - Calibrate
        elif key == Qt.Key_C:
            self.on_calibrate_clicked()

        # R - Reset
        elif key == Qt.Key_R:
            self.on_reset_clicked()

        # E - Export
        elif key == Qt.Key_E:
            self.on_export_clicked()

        # V - Video recording
        elif key == Qt.Key_V:
            self.on_record_clicked()

        # Space or P - Pause/Resume
        elif key == Qt.Key_Space or key == Qt.Key_P:
            self.video_thread.paused = not self.video_thread.paused

        # 1-4 - Direct mode selection
        elif key == Qt.Key_1:
            self.mode_buttons.button(0).click()
        elif key == Qt.Key_2:
            self.mode_buttons.button(1).click()
        elif key == Qt.Key_3:
            self.mode_buttons.button(2).click()
        elif key == Qt.Key_4:
            self.mode_buttons.button(3).click()

        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Handle window close."""
        # Stop recording if active
        if self.recording and self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

        self.video_thread.stop()
        self.save_config()
        event.accept()


def load_custom_fonts():
    """Load custom fonts from the fonts directory."""
    from PyQt5.QtGui import QFontDatabase
    import glob

    fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')

    if os.path.exists(fonts_dir):
        font_files = []

        # Look for font files
        for ext in ['*.ttf', '*.otf']:
            font_files.extend(glob.glob(os.path.join(fonts_dir, ext)))

        # Load each font
        for font_file in font_files:
            font_id = QFontDatabase.addApplicationFont(font_file)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                print(f"Loaded font: {', '.join(families)} from {os.path.basename(font_file)}")
            else:
                print(f"Failed to load font: {font_file}")
    else:
        print(f"Fonts directory not found: {fonts_dir}")
        print("Using system fallback fonts (Montserrat, Arial Black, Segoe UI)")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Galton's Goalie")
    app.setOrganizationName("Science Edition")

    # Load custom fonts before creating windows
    load_custom_fonts()

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

