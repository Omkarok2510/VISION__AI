# test_ocr.py
from ai.error_recognition import ErrorRecognizer
import cv2

def test_image(path):
    recognizer = ErrorRecognizer()
    print(f"Testing {path}...")
    codes = recognizer.extract_codes(path)
    print(f"Detected codes: {codes}")
    
    # Visual verification
    img = cv2.imread(path)
    cv2.imshow("Test Image", img)
    cv2.waitKey(3000)  # Show for 3 seconds
    cv2.destroyAllWindows()

test_image("ai/error_dataset/A03/0.jpg")  # Add a test image
