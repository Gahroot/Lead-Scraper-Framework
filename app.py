"""PRESTYJ Lead Scraper — Find local business leads in seconds."""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from scraper import ScraperError, search_leads
from website_scraper import enrich_leads

load_dotenv()

# Page setup
st.set_page_config(page_title="PRESTYJ Lead Scraper", layout="wide")
st.title("PRESTYJ Lead Scraper")
st.caption("Find local business leads with phone numbers, websites, and social media links.")

# Sidebar
with st.sidebar:
    # API Key section
    st.header("Google API Key")

    env_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
    has_env_key = bool(env_key and env_key != "your_key_here")

    if has_env_key:
        st.success("API key loaded from .env file")
    else:
        st.warning("No API key found in .env file")

    api_key_input = st.text_input(
        "Paste your API key here",
        type="password",
        placeholder="AIzaSy...",
        help="Your key is only used for this session and never stored online.",
    )

    col_get, col_help = st.columns(2)
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

    # Use the manually entered key, or fall back to .env
    active_key = api_key_input if api_key_input else (env_key if has_env_key else "")

    if active_key:
        st.success("API key active")
    else:
        st.info("Enter an API key above or add one to your .env file to get started.")

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
