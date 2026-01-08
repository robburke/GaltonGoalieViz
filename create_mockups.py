"""
Generate visual mockup images for Galton's Goalie UI
Creates PNG mockups showing the proposed interface design
"""
import cv2
import numpy as np

# Color palette (BGR format for OpenCV)
DARK_NAVY = (47, 26, 7)      # #071A2F
DEEP_BLUE = (99, 36, 10)     # #0A2463
ROYAL_BLUE = (204, 146, 62)  # #3E92CC
BRIGHT_CYAN = (195, 119, 28) # #1C77C3
SKY_BLUE = (226, 173, 93)    # #5DADE2
SLATE = (80, 62, 44)         # #2C3E50
WHITE = (255, 255, 255)
LIGHT_GRAY = (199, 195, 189) # #BDC3C7
SUCCESS_GREEN = (96, 174, 39) # #27AE60
WARNING_ORANGE = (34, 126, 230) # #E67E22
ERROR_RED = (43, 57, 192)    # #C0392B

def create_gradient(width, height, color1, color2, horizontal=True):
    """Create a gradient image."""
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    if horizontal:
        for x in range(width):
            ratio = x / width
            color = tuple(int(c1 * (1 - ratio) + c2 * ratio)
                         for c1, c2 in zip(color1, color2))
            gradient[:, x] = color
    else:
        for y in range(height):
            ratio = y / height
            color = tuple(int(c1 * (1 - ratio) + c2 * ratio)
                         for c1, c2 in zip(color1, color2))
            gradient[y, :] = color
    return gradient

def add_glass_effect(img, x, y, w, h, bg_color, opacity=0.6):
    """Add a glass morphism panel to the image."""
    overlay = img.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), bg_color, -1)

    # Border
    cv2.rectangle(overlay, (x, y), (x + w, y + h),
                 tuple(int(c * 1.2) for c in bg_color), 2)

    # Blend
    cv2.addWeighted(overlay, opacity, img, 1 - opacity, 0, img)
    return img

def draw_text(img, text, pos, font_scale=0.6, color=WHITE, thickness=1):
    """Draw text with better readability."""
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                font_scale, (0, 0, 0), thickness + 2)  # Shadow
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                font_scale, color, thickness)

def create_main_window_mockup():
    """Create the main window mockup."""
    # Canvas
    width, height = 1280, 800
    canvas = create_gradient(width, height, DARK_NAVY, DEEP_BLUE, horizontal=False)

    # Top bar
    top_bar = create_gradient(width, 60, DEEP_BLUE, DARK_NAVY, horizontal=True)
    canvas[0:60, :] = top_bar

    # App title
    draw_text(canvas, "GALTON'S GOALIE", (20, 35), 0.8, WHITE, 2)
    draw_text(canvas, "Science Edition", (20, 52), 0.4, LIGHT_GRAY, 1)

    # Mode indicator (center)
    mode_bg_x, mode_bg_y = width // 2 - 120, 15
    cv2.rectangle(canvas, (mode_bg_x, mode_bg_y),
                 (mode_bg_x + 240, mode_bg_y + 30), BRIGHT_CYAN, -1)
    draw_text(canvas, "Mode: Ultra-Long Exp", (mode_bg_x + 10, mode_bg_y + 22),
             0.5, DARK_NAVY, 1)

    # Right side indicators
    draw_text(canvas, "60 FPS", (width - 120, 30), 0.5, LIGHT_GRAY)
    draw_text(canvas, "0:45", (width - 120, 50), 0.4, LIGHT_GRAY)

    # Recording indicator
    cv2.circle(canvas, (width - 160, 35), 8, ERROR_RED, -1)
    draw_text(canvas, "REC", (width - 145, 40), 0.4, ERROR_RED)

    # Left sidebar
    sidebar_width = 280
    add_glass_effect(canvas, 0, 60, sidebar_width, height - 60, SLATE, 0.85)

    # Sidebar sections
    y_offset = 80

    # Mode selection
    draw_text(canvas, "MODE SELECTION", (15, y_offset), 0.5, LIGHT_GRAY)
    y_offset += 30

    modes = ["Standard", "Motion Trails", "Long Exposure", "Ultra-Long Exp"]
    for i, mode in enumerate(modes):
        is_active = (i == 3)
        color = BRIGHT_CYAN if is_active else LIGHT_GRAY

        # Radio button
        center = (30, y_offset + 12)
        cv2.circle(canvas, center, 8, color, 2)
        if is_active:
            cv2.circle(canvas, center, 4, color, -1)

        draw_text(canvas, mode, (50, y_offset + 17), 0.45, color)
        y_offset += 35

    y_offset += 20

    # Controls section
    draw_text(canvas, "CONTROLS", (15, y_offset), 0.5, LIGHT_GRAY)
    y_offset += 30

    # Sliders (simplified representation)
    slider_names = ["Cooldown", "Sensitivity", "Min Size"]
    for slider_name in slider_names:
        draw_text(canvas, slider_name, (20, y_offset), 0.4, WHITE)
        y_offset += 20

        # Slider track
        cv2.rectangle(canvas, (20, y_offset - 5), (260, y_offset + 5),
                     DEEP_BLUE, -1)
        # Slider fill
        cv2.rectangle(canvas, (20, y_offset - 5), (140, y_offset + 5),
                     ROYAL_BLUE, -1)
        # Slider handle
        cv2.circle(canvas, (140, y_offset), 10, BRIGHT_CYAN, -1)

        y_offset += 30

    y_offset += 20

    # Statistics
    draw_text(canvas, "STATISTICS", (15, y_offset), 0.5, LIGHT_GRAY)
    y_offset += 30

    stats_bg_y = y_offset
    add_glass_effect(canvas, 15, stats_bg_y, 250, 100, DEEP_BLUE, 0.5)

    draw_text(canvas, "Total Hits: 1,247", (25, stats_bg_y + 25), 0.45, WHITE)
    draw_text(canvas, "Camera: #0", (25, stats_bg_y + 50), 0.45, WHITE)
    draw_text(canvas, "Mean: u = 6.2", (25, stats_bg_y + 75), 0.45, WHITE)

    y_offset += 120

    # Action buttons
    draw_text(canvas, "ACTIONS", (15, y_offset), 0.5, LIGHT_GRAY)
    y_offset += 30

    buttons = ["Calibrate", "Reset Data", "Export"]
    for btn_text in buttons:
        # Button background
        cv2.rectangle(canvas, (20, y_offset - 5), (260, y_offset + 25),
                     ROYAL_BLUE, -1)
        draw_text(canvas, btn_text, (90, y_offset + 15), 0.5, WHITE, 1)
        y_offset += 40

    # Main visualization area (placeholder)
    viz_x = sidebar_width + 20
    viz_y = 80
    viz_w = width - sidebar_width - 40
    viz_h = height - 280

    # Simulated camera feed
    viz_area = create_gradient(viz_w, viz_h, (30, 30, 30), (60, 60, 60), False)

    # Add ghostly trails effect (simulation)
    center_x, center_y = viz_w // 2, viz_h // 3
    for i in range(50):
        offset_x = np.random.randint(-100, 100)
        offset_y = np.random.randint(0, viz_h - center_y)
        intensity = int(255 * np.exp(-((offset_x ** 2) / 5000)))

        cv2.line(viz_area,
                (center_x + offset_x, center_y),
                (center_x + offset_x, center_y + offset_y),
                (intensity, intensity, intensity), 2)

    canvas[viz_y:viz_y + viz_h, viz_x:viz_x + viz_w] = viz_area

    # Bottom histogram panel
    hist_y = height - 180
    add_glass_effect(canvas, viz_x, hist_y, viz_w, 160, DARK_NAVY, 0.9)

    draw_text(canvas, "DISTRIBUTION HISTOGRAM", (viz_x + 15, hist_y + 25),
             0.5, WHITE, 1)

    # Simplified histogram bars
    bar_data = [52, 89, 124, 147, 126, 91, 54, 28, 17, 8, 3]
    bar_width = (viz_w - 60) // len(bar_data)
    max_height = 100
    max_val = max(bar_data)

    for i, val in enumerate(bar_data):
        bar_h = int((val / max_val) * max_height)
        bar_x = viz_x + 30 + i * bar_width
        bar_y = hist_y + 140 - bar_h

        # Color gradient (blue to red)
        ratio = abs(i - len(bar_data) // 2) / (len(bar_data) // 2)
        b = int(255 * ratio)
        r = int(255 * (1 - ratio))
        g = int(100 * (1 - ratio))

        cv2.rectangle(canvas, (bar_x, bar_y),
                     (bar_x + bar_width - 10, hist_y + 140),
                     (b, g, r), -1)

        # Count label
        draw_text(canvas, str(val), (bar_x + 5, bar_y - 5), 0.35, WHITE)

        # Bucket number
        draw_text(canvas, str(i + 1), (bar_x + 10, hist_y + 158), 0.35, LIGHT_GRAY)

    return canvas

def create_calibration_mockup():
    """Create the calibration overlay mockup."""
    # Base canvas
    width, height = 1280, 800
    canvas = create_gradient(width, height, DARK_NAVY, DEEP_BLUE, horizontal=False)

    # Simulated camera background (darker)
    camera_area = np.zeros((height, width, 3), dtype=np.uint8)
    camera_area[:, :] = (40, 40, 40)
    canvas = cv2.addWeighted(canvas, 0.3, camera_area, 0.7, 0)

    # Semi-transparent overlay
    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (width, height), DEEP_BLUE, -1)
    canvas = cv2.addWeighted(canvas, 0.2, overlay, 0.8, 0)

    # Instruction card
    card_w, card_h = 500, 300
    card_x = (width - card_w) // 2
    card_y = (height - card_h) // 2

    add_glass_effect(canvas, card_x, card_y, card_w, card_h, SLATE, 0.95)

    # Card content
    draw_text(canvas, "CALIBRATION - STEP 1 OF 2",
             (card_x + 80, card_y + 50), 0.7, WHITE, 2)

    draw_text(canvas, "Click the TOP-LEFT corner",
             (card_x + 100, card_y + 120), 0.6, LIGHT_GRAY, 1)
    draw_text(canvas, "of your goal region",
             (card_x + 120, card_y + 150), 0.6, LIGHT_GRAY, 1)

    # Icon/diagram
    corner_x, corner_y = card_x + 220, card_y + 180
    cv2.rectangle(canvas, (corner_x, corner_y), (corner_x + 60, corner_y + 40),
                 BRIGHT_CYAN, 3)
    cv2.circle(canvas, (corner_x, corner_y), 8, SUCCESS_GREEN, -1)

    # Buttons
    btn_y = card_y + card_h - 60
    # Cancel button
    cv2.rectangle(canvas, (card_x + 50, btn_y), (card_x + 200, btn_y + 35),
                 SLATE, -1)
    draw_text(canvas, "Cancel", (card_x + 110, btn_y + 23), 0.5, LIGHT_GRAY)

    # Next button
    cv2.rectangle(canvas, (card_x + 300, btn_y), (card_x + 450, btn_y + 35),
                 ROYAL_BLUE, -1)
    draw_text(canvas, "Continue", (card_x + 345, btn_y + 23), 0.5, WHITE)

    # Cursor crosshair (simulated)
    cursor_x, cursor_y = width // 2 + 100, height // 2 - 50
    cv2.line(canvas, (cursor_x - 20, cursor_y), (cursor_x + 20, cursor_y),
            BRIGHT_CYAN, 2)
    cv2.line(canvas, (cursor_x, cursor_y - 20), (cursor_x, cursor_y + 20),
            BRIGHT_CYAN, 2)
    cv2.circle(canvas, (cursor_x, cursor_y), 15, BRIGHT_CYAN, 2)

    return canvas

def create_ultra_mode_mockup():
    """Create ultra-long exposure mode mockup (minimal UI)."""
    width, height = 1280, 800

    # Simulated accumulated trails
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[:, :] = (20, 20, 20)  # Dark background

    # Simulate bell curve distribution of trails
    center_x = width // 2
    for _ in range(200):
        # Gaussian distribution for x position
        x = int(np.random.normal(center_x, 100))
        x = np.clip(x, 0, width - 1)

        # Random y position (full height)
        y_start = np.random.randint(0, height // 3)
        y_end = np.random.randint(height // 2, height)

        # Brightness based on distance from center
        dist_from_center = abs(x - center_x)
        brightness = int(255 * np.exp(-(dist_from_center ** 2) / 20000))

        # Draw trail
        cv2.line(canvas, (x, y_start), (x, y_end),
                (brightness, brightness, brightness), 2)

    # Minimal top bar
    top_bar = create_gradient(width, 50, DEEP_BLUE, DARK_NAVY, horizontal=True)
    canvas[0:50, :] = cv2.addWeighted(canvas[0:50, :], 0.3, top_bar, 0.7, 0)

    draw_text(canvas, "GALTON'S GOALIE", (20, 32), 0.6, WHITE, 1)
    draw_text(canvas, "Ultra-Long Exp", (width - 200, 32), 0.5, BRIGHT_CYAN, 1)
    draw_text(canvas, "60 FPS", (width - 90, 32), 0.4, LIGHT_GRAY)

    return canvas

# Generate all mockups
print("Generating UI mockups...")

mockup1 = create_main_window_mockup()
cv2.imwrite("E:/projects/GaltonGoalieViz/mockup_main_window.png", mockup1)
print("[OK] Main window mockup saved")

mockup2 = create_calibration_mockup()
cv2.imwrite("E:/projects/GaltonGoalieViz/mockup_calibration.png", mockup2)
print("[OK] Calibration mockup saved")

mockup3 = create_ultra_mode_mockup()
cv2.imwrite("E:/projects/GaltonGoalieViz/mockup_ultra_mode.png", mockup3)
print("[OK] Ultra-long exposure mode mockup saved")

print("\nAll mockups generated successfully!")
print("Check the project folder for:")
print("  - mockup_main_window.png")
print("  - mockup_calibration.png")
print("  - mockup_ultra_mode.png")
