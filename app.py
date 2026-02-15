"""PRESTYJ Lead Scraper — Find local business leads in seconds."""

import pandas as pd
import streamlit as st

from scraper import ScraperError, search_leads
from website_scraper import enrich_leads

# Page setup
st.set_page_config(page_title="PRESTYJ Lead Scraper", layout="wide")
st.title("PRESTYJ Lead Scraper")
st.caption("Find local business leads with phone numbers, websites, and social media links.")

# Sidebar instructions
with st.sidebar:
    st.header("How To Use")
    st.markdown(
        "1. Type a **business type** (e.g. plumbers, dentists, restaurants)\n"
        "2. Type a **location** (e.g. Austin, TX)\n"
        "3. Pick how many results you want\n"
        "4. Click **Find Leads**\n"
        "5. Download your results as a CSV file"
    )
    st.divider()
    st.markdown("Built by [PRESTYJ](https://prestyj.com)")

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
    if not business_type or not location:
        st.warning("Please enter both a business type and a location.")
    else:
        try:
            with st.spinner(f"Searching for {business_type} in {location}..."):
                leads = search_leads(business_type, location, max_results)

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
        file_name=f"leads.csv",
        mime="text/csv",
    )

# Footer
st.divider()
st.caption("PRESTYJ Lead Scraper — prestyj.com")
