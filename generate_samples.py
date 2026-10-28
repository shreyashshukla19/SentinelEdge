import os
from PIL import Image, ImageDraw

def create_sample_images():
    os.makedirs("sample_data", exist_ok=True)
    
    # 1. Create a safe zone mock image (Green background)
    img_safe = Image.new('RGB', (640, 480), color=(40, 120, 40))
    draw_safe = ImageDraw.Draw(img_safe)
    draw_safe.text((50, 220), "ZONE A: SAFE - WORKERS WITH PPE", fill=(255, 255, 255))
    img_safe.save("sample_data/safe_zone.jpg")
    
    # 2. Create a violation zone mock image (Red background representing danger/violation)
    img_violation = Image.new('RGB', (640, 480), color=(140, 40, 40))
    draw_violation = ImageDraw.Draw(img_violation)
    draw_violation.text((50, 220), "ZONE B: VIOLATION - NO HARD HAT DETECTED", fill=(255, 255, 255))
    img_violation.save("sample_data/violation_zone.jpg")
    
    print("Successfully generated sample images in 'sample_data/' folder!")

if __name__ == "__main__":
    create_sample_images()