#!/usr/bin/env python3
"""
Create a simple icon for the translator app.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a blue circle
    circle_color = (66, 133, 244, 255)  # Google blue
    draw.ellipse([2, 2, size-2, size-2], fill=circle_color)
    
    # Draw a white 'T' in the middle
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    text = "T"
    bbox = draw.textbbox((0,0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    # Save to icons directory
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    os.makedirs(icons_dir, exist_ok=True)
    icon_path = os.path.join(icons_dir, "translate.png")
    img.save(icon_path, "PNG")
    print(f"Icon saved to {icon_path}")
    
    # Also create a 32x32 version for tray
    img_small = img.resize((32, 32), Image.Resampling.LANCZOS)
    icon_small_path = os.path.join(icons_dir, "translate32.png")
    img_small.save(icon_small_path, "PNG")
    print(f"Small icon saved to {icon_small_path}")

if __name__ == "__main__":
    create_icon()