import cv2
import numpy as np
import os
import random

# List your error codes here
error_codes = [
    'C15', 'E12', 'A03', 'B01',       # Existing ones
    'F01', 'F02', 'U04', 'H03',       # Fridge-related
    'E05', 'CH05', 'E6', 'H6',        # AC-related
    'UE', 'LE', 'OE', 'dE',           # Washing machine
    'E10', 'E11', 'E20', 'E30',       # TV-related
    'ERR1', 'ERR2', 'FAULT3', 'CODE9' # General/fake samples
]

output_dir = 'ai/error_dataset'

# Create image with text function
def create_image_with_text(text, image_size=(200, 100), font_scale=2, thickness=3):
    # Black background
    image = np.zeros((image_size[1], image_size[0], 3), dtype=np.uint8)

    # Choose font and color
    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (0, 0, 255)  # Red

    # Get text size
    (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)

    # Center text
    x = (image_size[0] - text_width) // 2
    y = (image_size[1] + text_height) // 2

    # Put text on image
    cv2.putText(image, text, (x, y), font, font_scale, color, thickness)

    return image

# Generate and save images
for code in error_codes:
    code_path = os.path.join(output_dir, code)
    os.makedirs(code_path, exist_ok=True)

    for i in range(10):
        img = create_image_with_text(code)
        
        # Optional: add slight variations (noise, lines, etc.)
        if random.random() > 0.5:
            cv2.line(img, (0, 0), (img.shape[1], img.shape[0]), (255, 255, 255), 1)

        save_path = os.path.join(code_path, f"{i}.jpg")
        cv2.imwrite(save_path, img)

print("✅ Images generated successfully.")
