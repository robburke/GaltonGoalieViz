import cv2
from PIL import Image
import os

def video_to_gif(video_path, output_path, max_frames=100, resize_width=640, fps=10):
    """Convert a video to an optimized GIF"""

    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_count = 0

    # Calculate how many frames to skip to get desired output fps
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_skip = max(1, int(original_fps / fps))

    print(f"Reading video... (original fps: {original_fps})")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Only process every Nth frame
        if frame_count % frame_skip == 0:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Resize to reduce file size
            height, width = frame_rgb.shape[:2]
            new_height = int(height * (resize_width / width))
            frame_resized = cv2.resize(frame_rgb, (resize_width, new_height))

            # Convert to PIL Image
            pil_img = Image.fromarray(frame_resized)
            frames.append(pil_img)

            if len(frames) >= max_frames:
                break

        frame_count += 1

    cap.release()

    print(f"Creating GIF with {len(frames)} frames...")

    # Save as GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=int(1000/fps),  # milliseconds per frame
        loop=0
    )

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"GIF created: {output_path} ({file_size_mb:.2f} MB)")

if __name__ == "__main__":
    video_to_gif(
        "GaltonSampleVid.mp4",
        "demo.gif",
        max_frames=100,  # Limit frames to keep file size reasonable
        resize_width=500,  # Smaller width for GitHub
        fps=12  # Frame rate of output GIF
    )
