# PRESTYJ Lead Scraper

**Find local business leads in seconds.** Type a business type and a city, get a list of real businesses with phone numbers, websites, ratings, and social media links. Download everything as a spreadsheet.

Built by [PRESTYJ](https://prestyj.com) — Luxury AI Sales Agents for Appointment Setting.

---

## Quick Start

### 1. Download this tool
Click the green **"Use this template"** button above, or click **Code → Download ZIP** and unzip the folder.

### 2. Install Python
If you don't have Python, download it from [python.org](https://www.python.org/downloads/). **Windows users:** check the "Add Python to PATH" box during installation.

### 3. Run the setup script
Open a terminal (Mac/Linux) or Command Prompt (Windows) in this folder, then run:

**Mac/Linux:**
```
chmod +x setup.sh
./setup.sh
```

**Windows:**
```
setup.bat
```

### 4. Add your Google API key
Open the `.env` file in any text editor and replace `your_key_here` with your actual Google Places API key (see below for how to get one).

### 5. Run the app
```
# Mac/Linux
source venv/bin/activate
streamlit run app.py

# Windows
venv\Scripts\activate.bat
streamlit run app.py
```

Your browser will open automatically with the lead scraper tool.

---

## Getting a Google Places API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Go to **APIs & Services → Library**
4. Search for **"Places API (New)"** and click **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → API Key**
7. Copy the key and paste it in your `.env` file

Google gives you **$200 of free credits every month** — that's enough for thousands of searches at no cost.

---

## Features

- **Business Search** — Find any type of business in any city
- **Contact Info** — Get phone numbers, addresses, and websites
- **Ratings & Reviews** — See Google ratings and review counts
- **Social Media Links** — Automatically find LinkedIn, Facebook, Instagram, Twitter/X, YouTube, and TikTok profiles
- **CSV Export** — Download everything as a spreadsheet
- **Easy to Use** — Simple web interface, no coding required

---

## Troubleshooting

**"No API key found"**
Open your `.env` file and make sure your Google Places API key is pasted after the `=` sign. No quotes, no spaces.

**"Invalid API key"**
Double-check that you enabled the **Places API (New)** (not the old "Places API") in Google Cloud Console.

**"Python is not installed"**
Download Python from [python.org](https://www.python.org/downloads/). Windows users: make sure to check **"Add Python to PATH"** during installation.

**0 results returned**
Try a broader search. Instead of "Joe's Plumbing" try "plumbers". Make sure the location is a real city or area.

**"command not found: streamlit"**
Make sure you activated the virtual environment first:
- Mac/Linux: `source venv/bin/activate`
- Windows: `venv\Scripts\activate.bat`

---

## Links

- [PRESTYJ Website](https://prestyj.com)
- [The PRESTYJ Blueprint (Skool Community)](https://skool.com/prestyj)
- [Google Cloud Console](https://console.cloud.google.com/)

---

MIT License — Copyright (c) 2026 PRESTYJ
