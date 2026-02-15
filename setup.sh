#!/bin/bash
# PRESTYJ Lead Scraper — One-Click Setup (Mac/Linux)

echo "========================================="
echo "  PRESTYJ Lead Scraper — Setup"
echo "========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Download it from https://www.python.org/downloads/"
    exit 1
fi

echo "Python found: $(python3 --version)"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "Done."
echo ""

# Activate and install
echo "Installing requirements..."
source venv/bin/activate
pip install -r requirements.txt --quiet
echo "Done."
echo ""

# Copy .env if needed
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template."
else
    echo ".env file already exists — skipping."
fi

echo ""
echo "========================================="
echo "  Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Open the .env file and paste your Google Places API key"
echo "  2. Run the app:"
echo ""
echo "     source venv/bin/activate"
echo "     streamlit run app.py"
echo ""
echo "Your browser will open automatically."
echo ""
