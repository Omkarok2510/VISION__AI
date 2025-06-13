# ai/error_recognition.py
import logging
import re
import os
# import easyocr # You would uncomment and import this if you have it installed and want to use it
# import cv2
# import numpy as np

logger = logging.getLogger(__name__)

# Placeholder for easyocr if not installed or to avoid direct dependency
class EasyOCRPlaceholder:
    def readtext(self, image_path, detail=0):
        logger.info(f"EasyOCR Placeholder: Simulating text reading from {image_path}")
        # Simulate some text reading for demonstration
        if "error" in os.path.basename(image_path).lower():
            return ["E5", "EROR", "C0DE", "H3", "F8"] # Simulate detection
        return ["No", "display", "on", "screen"]

class ErrorRecognizer:
    def __init__(self):
        # try:
        #     # If easyocr is installed, use it. Otherwise, fallback to placeholder.
        #     import easyocr
        #     self.easyocr = easyocr.Reader(['en']) # 'en' for English
        #     logger.info("EasyOCR loaded successfully for ErrorRecognizer.")
        # except ImportError:
        self.easyocr = EasyOCRPlaceholder()
        logger.warning("EasyOCR not found or failed to load. Using placeholder for text recognition.")
        
        self.haier_error_patterns = [
            r'\bE\d\b', # E1, E2, E3, E5 etc.
            r'\bF\d\b', # F1, F8 etc.
            r'\bH\d\b', # H1, H3 etc.
            r'\b\d{2,}\b', # Any two or more digits (e.g., 21, 88)
            # Add more specific patterns if Haier uses unique codes like 'CH01', 'LO'
            r'\bCH\d+\b', # e.g., CH01
            r'\bLO\b', # e.g., LO for low voltage
        ]
        logger.info("ErrorRecognizer initialized.")

    def extract_codes(self, image_path: str) -> list:
        """
        Extracts potential error codes from an image using OCR.
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return []

        try:
            # The readtext method will be called on either the actual easyocr Reader or the placeholder
            results = self.easyocr.readtext(image_path, detail=0) # detail=0 returns only recognized text
            full_text = " ".join(results).upper()
            logger.info(f"OCR Full Text: '{full_text}' from image: {os.path.basename(image_path)}")

            found_codes = set()
            for pattern in self.haier_error_patterns:
                matches = re.findall(pattern, full_text)
                for match in matches:
                    found_codes.add(match)

            logger.info(f"Extracted error codes: {list(found_codes)}")
            return sorted(list(found_codes)) # Return sorted list of unique codes
        except Exception as e:
            logger.error(f"Error during error code extraction from {image_path}: {e}", exc_info=True)
            return []