# Standard Library
import os
import re
import asyncio
import logging
from datetime import datetime, timedelta
from collections import Counter # Not explicitly used for core logic, but good to keep if future analytics
import io # Not explicitly used, but good for byte streams

# Third-Party Packages
import requests
from telegram import Update, InputFile, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import cv2 # For image processing (used in error recognition)
import numpy as np # For numerical operations with cv2
import sqlite3 # For local database operations on the bot side
from PIL import Image # Potentially useful for image manipulation (e.g., resizing)

# --- Placeholder for AI Modules ---
class EasyOCRPlaceholder:
    def readtext(self, image_path, detail=0):
        """
        A placeholder for EasyOCR's readtext function.
        Simulates OCR output based on dummy logic.
        """
        logging.info(f"EasyOCR placeholder: Reading text from {image_path}")
        # Simulate different outputs based on image path
        if "error" in image_path.lower() or "e5" in image_path.lower():
            return ["E5", "ERROR", "CODE"]
        if "f0" in image_path.lower():
            return ["F0", "FAULT"]
        if "h1" in image_path.lower():
            return ["H1", "HIGH", "TEMP"]
        return ["NO", "CODE", "FOUND", "1234", "OK"] # Default for other cases

class ErrorRecognizer:
    def __init__(self):
        self.easyocr = EasyOCRPlaceholder() # Use the placeholder OCR
        logging.info("ErrorRecognizer initialized (placeholder).")

    def extract_codes(self, image_path: str) -> list:
        """
        Extracts potential error codes from an image using a placeholder OCR.
        Identifies common Haier-like error code patterns.
        """
        full_text_list = self.easyocr.readtext(image_path, detail=0)
        full_text = ' '.join(full_text_list).upper()
        logging.info(f"ErrorRecognizer: Detected text for code extraction: {full_text}")

        detected_codes = []
        # Regex to find patterns like E1, F0, H1, ERR123, 1234 (2-4 digits)
        pattern = r'\b(?:E\d{1,3}|F\d{1,3}|H\d{1,3}|ERR\d{1,3}|ER\d{1,3}|\d{2,4})\b'
        matches = re.findall(pattern, full_text)
        
        # A list of common Haier error codes for better filtering
        known_haier_codes = [
            'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E0',
            'F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F0',
            'H0', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9'
        ]
        
        for match in matches:
            cleaned_match = re.sub(r'[^A-Z0-9]', '', match).strip() # Remove non-alphanumeric
            if cleaned_match:
                # Prioritize known Haier codes
                if cleaned_match in known_haier_codes and cleaned_match not in detected_codes:
                    detected_codes.append(cleaned_match)
                # Allow general 2-4 digit numbers if not already captured
                elif cleaned_match.isdigit() and 2 <= len(cleaned_match) <= 4 and cleaned_match not in detected_codes:
                    detected_codes.append(cleaned_match)
                # Allow patterns like ERR/ER followed by digits
                elif re.match(r'(ERR|ER)\d{1,3}', cleaned_match) and cleaned_match not in detected_codes:
                    detected_codes.append(cleaned_match)

        logging.info(f"ErrorRecognizer: Extracted codes: {detected_codes}")
        return detected_codes if detected_codes else ["NOT_RECOGNIZED"]


class ComplaintPredictor:
    def __init__(self):
        logging.info("ComplaintPredictor initialized (placeholder).")

# --- End Placeholder ---

# Initialize AI/Utility Modules
recognizer = ErrorRecognizer()
predictor = ComplaintPredictor()

# Configure logging for bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# !!! IMPORTANT: REPLACE WITH YOUR ACTUAL BOT TOKEN !!!
TOKEN = "7922002419:AAGsGo2deXJC4P2IPAoOg7F_fT2GmjE2K_Q" 

# !!! IMPORTANT: UPDATE THIS WITH YOUR CURRENT NGROK FORWARDING URL (e.g., https://<RANDOM_ID>.ngrok-free.app) !!!
# You MUST get a new URL from ngrok each time you restart it (unless you have a paid fixed domain).
FLASK_SERVER_URL = "https://e6fa-2401-4900-57a1-c4ab-e180-a88f-9c4a-b215.ngrok-free.app/submit_complaint" 

TIMEOUT = timedelta(minutes=5) # Conversation timeout for `ConversationHandler`

# Conversation states - used to manage the flow of the conversation
PROBLEM, CONTACT, LOCATION_OR_ADDRESS, MEDIA = range(4)

# Helper functions

def init_db():
    """
    Initialize SQLite database for complaints on the bot's side.
    This local DB acts as a cache/queue for complaints that might not immediately sync to the server.
    """
    conn = sqlite3.connect("complaints.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            problem TEXT,
            error_code TEXT,
            address TEXT,
            complaint_latitude REAL,  -- Store latitude locally
            complaint_longitude REAL, -- Store longitude locally
            contact_no TEXT,
            media_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            synced_to_server BOOLEAN DEFAULT 0 -- Flag to track successful sync
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Bot's local database initialized/checked.")

def validate_phone(phone: str) -> bool:
    """
    Validates if the provided phone number is a valid 10-digit Indian mobile number.
    """
    cleaned_phone = re.sub(r'[^0-9]', '', phone) # Remove non-digits
    # Check for 10 digits and starts with 6, 7, 8, or 9 (standard Indian mobile prefixes)
    return len(cleaned_phone) == 10 and cleaned_phone[0] in "6789"

async def reverse_geocode_placeholder(latitude: float, longitude: float) -> str:
    """
    A placeholder for a reverse geocoding API call.
    Simulates fetching an address from coordinates for Pune region.
    """
    logger.info(f"Simulating reverse geocoding for Lat: {latitude}, Lon: {longitude}")
    
    # Define approximate bounding box for Pune city
    pune_min_lat, pune_max_lat = 18.40, 18.70
    pune_min_lon, pune_max_lon = 73.70, 74.10

    if pune_min_lat <= latitude <= pune_max_lat and pune_min_lon <= longitude <= pune_max_lon:
        # Simulate addresses for some well-known areas in Pune
        if 18.51 <= latitude <= 18.53 and 73.84 <= longitude <= 73.86:
            return "Shivajinagar, Pune, Maharashtra, India"
        elif 18.60 <= latitude <= 18.64 and 73.78 <= longitude <= 73.82:
            return "Pimpri-Chinchwad, Pune, Maharashtra, India"
        elif 18.50 <= latitude <= 18.52 and 73.92 <= longitude <= 73.94:
            return "Hadapsar, Pune, Maharashtra, India"
        elif 18.58 <= latitude <= 18.60 and 73.72 <= longitude <= 73.75:
            return "Hinjewadi, Pune, Maharashtra, India"
        elif 18.55 <= latitude <= 18.57 and 73.91 <= longitude <= 73.93:
            return "Viman Nagar, Pune, Maharashtra, India"
        elif 18.50 <= latitude <= 18.52 and 73.78 <= longitude <= 73.80:
            return "Kothrud, Pune, Maharashtra, India"
        # Adding some village approximations
        elif 18.70 <= latitude <= 18.75 and 73.65 <= longitude <= 73.70:
            return "Talegaon Dabhade (Rural), Pune, Maharashtra, India"
        elif 18.40 <= latitude <= 18.43 and 74.00 <= longitude <= 74.07:
            return "Uruli Kanchan (Village), Pune, Maharashtra, India"
        elif 18.48 <= latitude <= 18.50 and 73.65 <= longitude <= 73.68:
            return "Pirangut (Village), Pune, Maharashtra, India"
        else:
            return f"Pune, Maharashtra, India (Approx. Lat: {latitude:.4f}, Lon: {longitude:.4f})"
    else:
        return f"Outside Pune region (Approx. Lat: {latitude:.4f}, Lon: {longitude:.4f})"

# Conversation Handlers (each function corresponds to a state in the conversation flow)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the conversation when the user sends /start.
    Asks the user to describe their problem.
    """
    await update.message.reply_text(
        "👋 Welcome to Haier Service Bot! Please describe your appliance problem (e.g., 'AC not cooling', 'Refrigerator making strange noise'):"
    )
    return PROBLEM # Transition to the PROBLEM state

async def problem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Stores the user's problem description and asks for their contact number.
    """
    context.user_data["problem"] = update.message.text # Save problem description to user_data
    await update.message.reply_text("📱 Please share your 10-digit mobile number for contact:")
    return CONTACT # Transition to the CONTACT state

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Validates the provided phone number. If valid, asks for location or manual address.
    If invalid, prompts for re-entry.
    """
    phone = update.message.text
    if not validate_phone(phone):
        await update.message.reply_text("❌ Invalid phone number. Please enter a 10-digit mobile number starting with 6, 7, 8, or 9:")
        return CONTACT # Stay in CONTACT state for re-entry
    
    context.user_data["contact_no"] = phone # Save contact number
    
    # Offer a keyboard button for location sharing
    keyboard = [[KeyboardButton("Share My Location", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "📍 Now, please share your current location or type your full address manually (include house/flat number, street, landmark, and city):",
        reply_markup=reply_markup # Show the location sharing keyboard
    )
    return LOCATION_OR_ADDRESS # Transition to LOCATION_OR_ADDRESS state

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the location shared by the user.
    Stores raw coordinates and attempts reverse geocoding to get an address string.
    Then prompts for media upload.
    """
    location = update.message.location
    latitude = location.latitude
    longitude = location.longitude
    
    context.user_data["complaint_latitude"] = latitude  # Store raw latitude
    context.user_data["complaint_longitude"] = longitude # Store raw longitude
    
    # Remove the custom keyboard once location is received
    await update.message.reply_text("Processing your location...", reply_markup=ReplyKeyboardRemove()) 
    
    # Simulate reverse geocoding to get a human-readable address
    address = await reverse_geocode_placeholder(latitude, longitude)
    context.user_data["address"] = address # Store the resolved address
    logger.info(f"User shared location: Lat={latitude}, Lon={longitude}, Address={address}")
    
    await update.message.reply_text(
        f"✅ We've detected your address as: `{address}`\n\n"
        "📸 Optional: If there's an error code displayed on your appliance, please upload a photo of it. This helps us diagnose faster.\n"
        "Otherwise, type /skip to proceed."
    )
    return MEDIA # Transition to the MEDIA state

async def address_manual_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles a manually typed address.
    Sets coordinates to None as they are not available for manual entry.
    Then prompts for media upload.
    """
    context.user_data["address"] = update.message.text # Store the manually typed address
    context.user_data["complaint_latitude"] = None  # Explicitly set to None for manual address
    context.user_data["complaint_longitude"] = None # Explicitly set to None for manual address
    logger.info(f"User manually provided address: {update.message.text}")
    
    # Remove the custom keyboard if user types address instead of sharing location
    await update.message.reply_text(
        "📸 Optional: If there's an error code displayed on your appliance, please upload a photo of it. This helps us diagnose faster.\n"
        "Otherwise, type /skip to proceed.",
        reply_markup=ReplyKeyboardRemove() 
    )
    return MEDIA # Transition to the MEDIA state

async def media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles media (photo/video) upload.
    If a photo, attempts to recognize error codes using the ErrorRecognizer.
    Then calls submit_complaint to finalize the process.
    """
    media_path = ""
    error_code = "NOT_PROVIDED" # Default error code if no media or no code recognized

    try:
        if update.message.photo:
            # Get the largest photo file
            photo_file = await update.message.photo[-1].get_file()
            
            # Create 'media' directory if it doesn't exist
            os.makedirs("media", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Define temporary path to save the photo
            temp_media_path = os.path.join("media", f'{update.message.chat_id}_{timestamp}.jpg')
            
            # Download photo as bytes, convert to numpy array for OpenCV, then save
            img_bytes = await photo_file.download_as_bytearray()
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                cv2.imwrite(temp_media_path, img) # Save the image
                logger.info(f"Received and saved photo to: {temp_media_path}")
                media_path = temp_media_path
                
                # Attempt to extract error codes from the saved photo
                detected_codes = recognizer.extract_codes(temp_media_path)
                
                if detected_codes and detected_codes != ["NOT_RECOGNIZED"]:
                    error_code = ",".join(detected_codes) # Join multiple codes if found
                    await update.message.reply_text(
                        f"✅ Detected Error Code(s): `{error_code}`\n"
                        "We've added this to your complaint. Submitting now..."
                    )
                else:
                    await update.message.reply_text(
                        f"⚠️ No standard error codes found in the photo. Your complaint will be processed without a specific code.\n"
                        "Submitting complaint..."
                    )
            else:
                logger.error("Failed to decode image bytes from Telegram.")
                await update.message.reply_text("❌ Failed to process the image. Please try again or /skip.")
                return MEDIA # Stay in MEDIA state to allow retry

        elif update.message.video:
            # Handle video upload (currently not processed for error codes)
            await update.message.reply_text(
                "Thank you for the video! We currently only process error codes from photos. "
                "Your complaint will be submitted based on your description."
            )
            video_file = await update.message.video.get_file()
            os.makedirs("media", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_media_path = os.path.join("media", f'{update.message.chat_id}_{timestamp}.mp4')
            await video_file.download_to_drive(custom_path=temp_media_path)
            media_path = temp_media_path
            error_code = "VIDEO_UPLOADED" # Mark as video uploaded

        else:
            # Handle other file types not supported for error code recognition
            await update.message.reply_text(
                "I received a file, but it's not a photo or video. "
                "Please upload a photo/video of the error code or /skip."
            )
            return MEDIA # Stay in MEDIA state

        context.user_data["error_code"] = error_code # Save determined error code
        context.user_data["media_path"] = media_path # Save path to media (if any)
        
        await submit_complaint(update, context) # Proceed to complaint submission
        return ConversationHandler.END # End the conversation
            
    except Exception as e:
        logger.error(f"Error in media handler: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred while processing your media. Please try again or /skip."
        )
        return ConversationHandler.END # End or allow retry, depending on desired flow

async def skip_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the /skip command for media upload.
    Sets default values for error_code and media_path, then proceeds to submission.
    """
    context.user_data["error_code"] = "NOT_PROVIDED"
    context.user_data["media_path"] = ""
    await update.message.reply_text("Media upload skipped. Submitting your complaint...")
    await submit_complaint(update, context) # Submit complaint
    return ConversationHandler.END # End the conversation

async def submit_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Submits the collected complaint data to the Flask backend.
    Includes local saving (as a queue) and retry logic for server submission.
    """
    chat_id = update.message.chat_id
    problem = context.user_data.get("problem", "N/A")
    address = context.user_data.get("address", "N/A")
    complaint_latitude = context.user_data.get("complaint_latitude") 
    complaint_longitude = context.user_data.get("complaint_longitude")
    contact_no = context.user_data.get("contact_no", "N/A")
    error_code = context.user_data.get("error_code", "UNKNOWN")
    media_path = context.user_data.get("media_path", "")

    # Prepare data for submission to Flask server
    data_to_submit = {
        "chat_id": chat_id,
        "problem": problem,
        "address": address,
        "complaint_latitude": complaint_latitude,  # Send coordinates
        "complaint_longitude": complaint_longitude, # Send coordinates
        "contact_no": contact_no,
        "error_code": error_code,
        "media_path": media_path
    }

    complaint_id = None # To store local DB ID if saved
    try:
        # Save complaint locally first (as a temporary queue/backup)
        conn = sqlite3.connect("complaints.db")
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO complaints 
            (chat_id, problem, error_code, address, complaint_latitude, complaint_longitude, contact_no, media_path, timestamp, synced_to_server) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (chat_id, problem, error_code, address, complaint_latitude, complaint_longitude, contact_no, media_path, datetime.now().isoformat(), 0) # 0 for not synced yet
        )
        complaint_id = cursor.lastrowid # Get the ID of the locally saved complaint
        conn.commit()
        conn.close()
        logger.info(f"Complaint saved locally with ID: {complaint_id}")
    except sqlite3.Error as e:
        logger.error(f"Local DB error saving complaint: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ A local database error occurred. Your complaint might not be fully saved locally. "
            "Attempting to submit to server anyway."
        )

    max_retries = 3 # Number of attempts to send to Flask server
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to send complaint to Flask server at {FLASK_SERVER_URL}.")
            response = requests.post(
                FLASK_SERVER_URL,
                json=data_to_submit,
                headers={'Content-Type': 'application/json'},
                timeout=45 # Increased timeout for server processing (DB, blockchain, assignment)
            )
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            api_response = response.json() # Parse JSON response from Flask

            # If successfully sent to server, update local DB status
            if complaint_id:
                try:
                    conn = sqlite3.connect("complaints.db")
                    cursor = conn.cursor()
                    cursor.execute("UPDATE complaints SET synced_to_server = 1 WHERE id = ?", (complaint_id,))
                    conn.commit()
                    conn.close()
                    logger.info(f"Local complaint ID {complaint_id} marked as synced.")
                except sqlite3.Error as e:
                    logger.warning(f"Failed to update synced_to_server for ID {complaint_id}: {e}", exc_info=True)

            # Construct the success message for the user
            message = (
                "✅ Complaint Registered Successfully!\n\n"
                f"Complaint ID: #{api_response.get('complaint_id', 'N/A')}\n"
                f"Problem: {problem}\n"
                f"Address: {address}\n"
                f"Contact No: {contact_no}\n"
                f"Error Code: {api_response.get('details', {}).get('error_code', 'N/A')}\n"
            )
            
            assigned_tech = api_response.get('assigned_technician')
            if assigned_tech and assigned_tech.get('status') == 'assigned':
                message += f"👨‍🔧 Assigned Technician: {assigned_tech['name']} (Contact: {assigned_tech['contact_no']})\n"
                message += "They will contact you shortly!"
            elif assigned_tech and assigned_tech.get('message'): # If assignment failed with a specific message
                message += f"⚠️ Assignment Info: {assigned_tech['message']}\n"
                message += "We'll manually review and assign a technician soon."
            else: # Generic pending assignment
                message += "⚠️ Technician assignment is pending. We'll assign one shortly."

            if 'blockchain_hash' in api_response:
                message += f"\nBlockchain Receipt: `{api_response['blockchain_hash'][:12]}...`\n" # Show a truncated hash
            
            await update.message.reply_text(message)
            logger.info("Complaint successfully sent to Flask server.")
            return # Exit function after successful submission
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Attempt {attempt + 1} failed to connect to Flask server (ConnectionError): {e}")
            if attempt < max_retries - 1: # If not the last attempt, wait and retry
                await asyncio.sleep(2) # Wait for 2 seconds before retrying
            else:
                await update.message.reply_text(
                    "❌ Failed to connect to the backend server after multiple attempts. "
                    "Your complaint has been saved locally and will be synced later."
                )
                logger.error("Max retries reached. Could not connect to Flask server.")
        except requests.exceptions.Timeout:
            logger.warning(f"Attempt {attempt + 1} timed out connecting to Flask server.")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            else:
                await update.message.reply_text(
                    "❌ The backend server timed out. "
                    "Your complaint has been saved locally and will be synced later."
                )
                logger.error("Max retries reached. Flask server timeout.")
        except requests.exceptions.HTTPError as e:
            # Catch HTTP errors (e.g., 400 Bad Request, 500 Internal Server Error from Flask)
            logger.error(f"HTTP Error from Flask server: {e.response.status_code} - {e.response.text}", exc_info=True)
            await update.message.reply_text(
                f"❌ The server returned an error: {e.response.status_code}. "
                "Your complaint has been saved locally. Please try again later or contact support."
            )
            return # Exit function on HTTP error as retries won't help here
        except Exception as e:
            # Catch any other unexpected errors during submission
            logger.error(f"Unexpected error during server submission: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ An unexpected error occurred during complaint submission. "
                "Your complaint has been saved locally and will be synced later."
            )
            return

    logger.error("All server submission attempts failed.") # This line is reached if all retries failed

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels the current complaint submission conversation.
    Clears user data for the conversation.
    """
    await update.message.reply_text(
        "🚫 Complaint submission cancelled. You can start a new one anytime with /start."
    )
    context.user_data.clear() # Clear all data stored for the current user
    return ConversationHandler.END # End the conversation


def main() -> None:
    """Start the bot."""
    init_db() # Initialize the bot's local database on startup

    # Build the Telegram Application instance
    application = Application.builder().token(TOKEN).build()

    # Define the conversation handler with states and fallbacks
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)], # Entry point: /start command
        states={
            PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, problem)], # Expect text, not commands
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
            LOCATION_OR_ADDRESS: [
                MessageHandler(filters.LOCATION, location_handler), # Handles shared location
                MessageHandler(filters.TEXT & ~filters.COMMAND, address_manual_handler) # Handles manually typed address
            ],
            MEDIA: [
                MessageHandler(filters.PHOTO | filters.VIDEO, media), # Handles photos or videos
                CommandHandler("skip", skip_media) # Handles /skip command
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)], # Fallback command to cancel the conversation
        conversation_timeout=TIMEOUT # Set a timeout for inactivity in the conversation
    )

    # Add the conversation handler to the application
    application.add_handler(conv_handler)

    logger.info("Bot is running...")
    # Start polling for updates from Telegram
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()