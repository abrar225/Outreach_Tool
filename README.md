# 📱 FireHox WhatsApp Outreach Tool

A professional, high-converting WhatsApp outreach automation tool designed for local business acquisition.

## 🚀 Key Features
- **Smart Anti-Ban:** Uses randomized human-like typing simulation and variable delays.
- **Google Reviews Angle:** High-converting message templates focusing on businesses with good reviews but no website.
- **Open-Close-Reopen Architecture:** Prevents browser session locking issues.
- **Data Cleaning:** Automatically cleans and formats phone numbers to international standards.
- **Regional Support:** Customizable country codes for global outreach.

---

## 🛠️ professional Setup Instructions

### 1. Prerequisites
- **Python 3.12** (Recommended for stability). [Download here](https://www.python.org/downloads/windows/).
- **Chromium Browser** (Installed automatically via Playwright).

### 2. Environment Setup
Open your terminal (PowerShell or CMD) in this folder and run:

```bash
# Create a virtual environment
python -m venv venv

# Activate the environment
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### 3. Launching the Application
Once the setup is done, always run the application with:

```bash
streamlit run app.py
```

---

## 📂 Project Structure
- `app.py`: The main Streamlit UI (3-step wizard).
- `whatsapp_engine.py`: The core automation logic and message generator.
- `firehox_wa_session/`: Local directory where your WhatsApp login session is securely stored.

## ⚠️ Safety Notes
- **Stay Logged In:** Once you scan the QR code in Step 1, the session is saved. You don't need to re-scan every time.
- **Avoid Manual Interaction:** While the bot is sending messages, do not click or type in the controlled browser window.
- **Account Health:** We recommend sending no more than 50-100 messages per day from a single account to keep it healthy.

---
© 2026 FireHox Web Solutions
