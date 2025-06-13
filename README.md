# VISION__AI

## Live Dashboard Updates
All dashboard data (map, stats, tables) refreshes automatically every 5 seconds.

## 🛠️ Technologies Used
**Backend:** Python 3, Flask, SQLite3, requests, hashlib, math

**Telegram Bot:** python-telegram-bot library, OpenCV (cv2), numpy, Pillow (PIL)

**Frontend (Dashboard):** HTML, CSS, JavaScript, Leaflet.js (for maps), Jinja2 (templating in Flask)

**Deployment/Tunneling:** Ngrok (for exposing local Flask server to Telegram)

## 🚀 Getting Started
Follow these steps to set up and run the project.

### Prerequisites
- Python 3.8+ installed on your system
- pip (Python package installer)
- Ngrok account and authenticated Ngrok client
- A Telegram Bot Token (obtainable from BotFather on Telegram)

### 1. Clone the Project
Although not a git repository yet, create a dedicated folder and place all your project files (`app.py`, `telegram_bot.py`, `templates/dashboard.html`, `media/`) inside it.

```bash
# Create your project directory
mkdir haier_complaint_system
cd haier_complaint_system
# Place your app.py, telegram_bot.py, and templates/dashboard.html here
# Create a 'media' folder for bot uploads:
mkdir media
# Create a 'templates' folder for your HTML:
mkdir templates
# Move dashboard.html into the templates folder
mv dashboard.html templates/
```
### 2. Set up Virtual Environment (Recommended)
It's best practice to use a virtual environment to manage project dependencies.
```
bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```
### 3. Install Dependencies
With your virtual environment activated, install the required Python packages:
```
bash
pip install Flask Flask-Cors python-telegram-bot requests opencv-python numpy Pillow
```
###4. Obtain Telegram Bot Token
Open Telegram and search for @BotFather

Start a chat with BotFather and send /newbot

Follow the instructions to choose a name and a username for your bot

BotFather will give you an HTTP API Token - copy this token

### 5. Configure telegram_bot.py
Open telegram_bot.py and modify the following lines:

python
!!! IMPORTANT: REPLACE WITH YOUR ACTUAL BOT TOKEN !!!
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE" 

!!! IMPORTANT: UPDATE THIS WITH YOUR CURRENT NGROK FORWARDING URL !!!
You MUST get a new URL from ngrok each time you restart it
FLASK_SERVER_URL = "https://your-ngrok-url-here.ngrok-free.app/submit_complaint"
Replace "YOUR_TELEGRAM_BOT_TOKEN_HERE" with your actual Telegram Bot Token

The FLASK_SERVER_URL will change every time you restart Ngrok (unless you have a paid Ngrok plan)

### 6. Delete Old Database (CRITICAL!)
To ensure the database schema is up-to-date (especially for technician locations and complaint assignment fields), you MUST delete the existing database file before starting the Flask app.

Navigate to your project directory (haier_complaint_system) and delete any existing database.db file.

### 7. Start Ngrok Tunnel
Run the following command to expose your local Flask server:
```
bash
ngrok http 5000
Copy the HTTPS forwarding URL (it will look like https://<RANDOM_ID>.ngrok-free.app) and update the FLASK_SERVER_URL in telegram_bot.py.
```
### 8. Run the Flask Application
In a separate terminal (with your virtual environment activated), run:
```
bash
python app.py

```
### 9. Start the Telegram Bot
In another terminal (with virtual environment activated), run:
```
bash
python telegram_bot.py
Progress Tracking
Users can track their complaint status via the bot or a separate web page.
```
text


This README includes:
1. Project title
2. Key features
3. Technology stack
4. Detailed setup instructions
5. Important notes about configuration
6. Clear steps for running the application

The formatting uses proper Markdown syntax for GitHub readability, with code blocks, lists, and section headers. You can copy this directly into your repository's README.md file.

### The formatting uses proper Markdown syntax for GitHub readability, with code blocks, lists, and section headers. You can copy this directly into your repository's README.md file.
