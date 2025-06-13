import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from ai.error_recognition import ErrorRecognizer

TOKEN = "7922002419:AAGsGo2deXJC4P2IPAoOg7F_fT2GmjE2K_Q"  # Replace with your actual token

async def handle_photo(update: Update, context):
    try:
        print("\n--- PHOTO RECEIVED ---")  # Debug 1: Check if trigger works
        photo = await update.message.photo[-1].get_file()
        path = "test_upload.jpg"
        await photo.download_to_drive(path)
        print("Image saved to:", os.path.abspath(path))  # Debug 2: Verify save location
        
        recognizer = ErrorRecognizer()
        codes = recognizer.extract_codes(path)
        print("Raw OCR output:", codes)  # Debug 3: Check OCR results
        
        await update.message.reply_text(f"Detected: {codes[0] if codes else 'Nothing'}")
    except Exception as e:
        print("CRASH:", str(e))  # Debug 4: See any errors
        await update.message.reply_text(f"Error: {str(e)}")

app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
print("Test bot started...")
app.run_polling()