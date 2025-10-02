import sys, time, os, ffmpeg
from PIL import Image, ImageSequence
from pathlib import Path
import numpy as np

chars = "█"  #"█▓"

def image_to_ascii(img: Image.Image, new_width: int = 80) -> str:
    img = img.convert("RGB")
    aspect_ratio = img.height / img.width
    new_height = int(aspect_ratio * new_width * 0.5)
    resized = img.resize((new_width, new_height))

    pixels = list(resized.getdata())
    ascii_lines = []

    for y in range(new_height):
        line = ""
        prev_color = None
        char_group = ""
        for x in range(new_width):
            r, g, b = pixels[y * new_width + x]
            brightness = int((r + g + b) / 3)
            char = chars[brightness * (len(chars) - 1) // 255]
            color = (r, g, b)

            if color != prev_color:
                if char_group:
                    line += char_group
                    char_group = ""
                line += f"\033[38;2;{r};{g};{b}m{char}"
                prev_color = color
            else:
                char_group += char
        line += char_group
        ascii_lines.append(line)
    ascii_lines.append("\033[0m")  # reset at the very end
    return "\n".join(ascii_lines)

def play_gif_ascii(img_path: str, width=60, delay=0.05):
    img = Image.open(img_path)  # open image from path
    frames = [image_to_ascii(frame, width) for frame in ImageSequence.Iterator(img)]
    for ascii_art in frames:
        os.system("cls" if os.name == "nt" else "clear")
        sys.stdout.write(ascii_art)
        sys.stdout.flush()
        time.sleep(delay)

def play_video_ascii(video_path: str, width=60, delay=None):
    # Probe video to get width, height, fps
    probe = ffmpeg.probe(video_path)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    w, h = int(video_info['width']), int(video_info['height'])
    fps = eval(video_info.get('avg_frame_rate', '25/1'))  # fallback 25fps
    frame_time = 1 / fps if delay is None else delay

    # Start ffmpeg process
    process = (
        ffmpeg
        .input(video_path)
        .output("pipe:", format="rawvideo", pix_fmt="rgb24")
        .run_async(pipe_stdout=True, pipe_stderr=True)
    )

    frame_size = w * h * 3  # RGB24 = 3 bytes per pixel

    while True:
        in_bytes = process.stdout.read(frame_size)
        if not in_bytes:  # video ended
            break

        frame = np.frombuffer(in_bytes, np.uint8).reshape([h, w, 3])
        img = Image.fromarray(frame)

        # Convert to ASCII
        ascii_art = image_to_ascii(img, width)

        os.system("cls" if os.name == "nt" else "clear")
        sys.stdout.write(ascii_art)
        sys.stdout.flush()
        time.sleep(frame_time)

    process.wait()  # make sure ffmpeg closes


def play_normal_ascii(img_path: str, width=60, delay=0.05):
    img = Image.open(img_path)   # open inside the function
    ascii_art = image_to_ascii(img, width)
    os.system("cls" if os.name == "nt" else "clear")
    sys.stdout.write(ascii_art)