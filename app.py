"""PRESTYJ Lead Scraper — Find local business leads in seconds."""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from scraper import ScraperError, search_leads
from website_scraper import enrich_leads

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(ENV_PATH)


def _read_env_key():
    """Read the API key fresh from the .env file."""
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                if line.startswith("GOOGLE_PLACES_API_KEY="):
                    val = line.split("=", 1)[1].strip()
                    if val and val != "your_key_here":
                        return val
    return ""


def _save_env_key(key):
    """Write the API key to the .env file."""
    with open(ENV_PATH, "w") as f:
        f.write(f"GOOGLE_PLACES_API_KEY={key}\n")


# Page setup
st.set_page_config(page_title="PRESTYJ Lead Scraper", layout="wide")
st.title("PRESTYJ Lead Scraper")
st.caption("Find local business leads with phone numbers, websites, and social media links.")

# Sidebar
with st.sidebar:
    # API Key section
    st.header("Google API Key")

    saved_key = _read_env_key()

    if saved_key:
        st.success("API key saved in .env file")
    else:
        st.warning("No API key found — paste one below")

    api_key_input = st.text_input(
        "Paste your API key here",
        key="api_key_field",
        type="password",
        placeholder="AIzaSy...",
        help="Click 'Save Key' to store it in your .env file so you don't have to paste it again.",
    )

    col_save, col_get, col_help = st.columns(3)
    with col_save:
        if st.button("Save Key"):
            key_to_save = st.session_state.get("api_key_field", "")
            if key_to_save:
                _save_env_key(key_to_save)
                st.session_state["key_just_saved"] = True
                st.rerun()
            else:
                st.warning("Paste a key first")
    with col_get:
        st.link_button(
            "Get a Key",
            "https://console.cloud.google.com/apis/credentials",
            type="primary",
        )
    with col_help:
        st.link_button(
            "Help",
            "https://developers.google.com/maps/documentation/places/web-service/get-api-key",
        )

    if st.session_state.pop("key_just_saved", False):
        st.success("API key saved! You're all set.")

    # Use the manually entered key, or fall back to saved .env key
    active_key = api_key_input if api_key_input else saved_key

    if active_key:
        st.success("API key active")
    else:
        st.info("Enter an API key above to get started.")

    st.divider()

    # Instructions
    st.header("How To Use")
    st.markdown(
        "1. Add your **Google API key** above\n"
        "2. Type a **business type** (e.g. plumbers, dentists)\n"
        "3. Type a **location** (e.g. Austin, TX)\n"
        "4. Pick how many results you want\n"
        "5. Click **Find Leads**\n"
        "6. Download your results as a CSV file"
    )
    st.divider()
    st.markdown("Built by [PRESTYJ](https://prestyj.com)")
    st.markdown("[Join The PRESTYJ Blueprint](https://www.skool.com/the-prestyj-blueprint-7395/about)")

# Search form
col1, col2 = st.columns(2)
with col1:
    business_type = st.text_input("Business Type", placeholder="e.g. plumbers, dentists, restaurants")
with col2:
    location = st.text_input("Location", placeholder="e.g. Austin, TX")

max_results = st.slider("Max Results", min_value=1, max_value=60, value=20)
enrich = st.checkbox("Find social media links (takes a bit longer)")

# Search button
if st.button("Find Leads", type="primary"):
    if not active_key:
        st.error("Please add your Google API key in the sidebar first.")
    elif not business_type or not location:
        st.warning("Please enter both a business type and a location.")
    else:
        try:
            with st.spinner(f"Searching for {business_type} in {location}..."):
                leads = search_leads(business_type, location, max_results, api_key=active_key)

            if not leads:
                st.warning("No results found. Try a different search.")
            else:
                if enrich:
                    with st.spinner("Checking websites for social media links..."):
                        leads = enrich_leads(leads)

                st.session_state["leads"] = leads
                st.success(f"Found {len(leads)} leads!")

        except ScraperError as e:
            st.error(str(e))

# Show results if we have them
if "leads" in st.session_state:
    leads = st.session_state["leads"]
    df = pd.DataFrame(leads)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="leads.csv",
        mime="text/csv",
    )

# Footer
st.divider()
st.caption("PRESTYJ Lead Scraper — prestyj.com")
