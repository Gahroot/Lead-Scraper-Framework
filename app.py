"""PRESTYJ Lead Scraper — Find local business leads in seconds."""

import json
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from scraper import ScraperError, search_leads
from website_scraper import enrich_leads
from lead_scorer import calculate_lead_score
from email_discovery import discover_emails
from database import init_db, save_search, get_search_history, get_leads_for_search, delete_search, delete_all_searches

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(ENV_PATH)
init_db()


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


def _get_score_badge(score):
    """Return a color-coded badge for lead score."""
    if score >= 71:
        return "🟢 High"
    elif score >= 41:
        return "🟡 Medium"
    else:
        return "🔴 Low"


def _get_score_emoji(score):
    """Return an emoji for lead score."""
    if score >= 71:
        return "🟢"
    elif score >= 41:
        return "🟡"
    else:
        return "🔴"


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

    # Processing Mode Toggle
    st.header("Processing Mode")
    mode = st.radio(
        "Processing Mode",
        ["⚡ Fast", "🔍 Thorough"],
        horizontal=True,
        help="Fast: Scoring only | Thorough: Full email discovery"
    )
    is_thorough = mode == "🔍 Thorough"

    # Feature Checkboxes
    st.header("Features")
    include_scoring = st.checkbox("Include Lead Scoring", value=True)
    include_emails = st.checkbox("Discover Decision Maker Emails", value=False, disabled=not is_thorough)

    st.divider()

    # Instructions
    st.header("How To Use")
    st.markdown(
        "1. Add your **Google API key** above\n"
        "2. Select **Processing Mode** (Fast/Thorough)\n"
        "3. Choose **Features** (scoring, emails)\n"
        "4. Type a **business type** (e.g. plumbers, dentists)\n"
        "5. Type a **location** (e.g. Austin, TX)\n"
        "6. Click **Find Leads**\n"
        "7. Download your results as a CSV file"
    )
    st.info("💡 Tip: Email discovery requires Thorough mode and takes longer per lead.")

    st.divider()

    # Search History
    st.header("Search History")
    history = get_search_history()
    if history:
        for entry in history:
            tags = []
            if entry["enriched"]:
                tags.append("Social")
            if entry["scored"]:
                tags.append("Scored")
            if entry["emails_found"]:
                tags.append("Emails")
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            label = f"{entry['business_type']} in {entry['location']}{tag_str}"
            timestamp = entry["created_at"][:16]  # trim seconds
            st.markdown(f"**{label}**")
            st.caption(f"{entry['lead_count']} leads | {timestamp}")
            col_load, col_del = st.columns(2)
            with col_load:
                if st.button("Load", key=f"load_{entry['id']}"):
                    loaded = get_leads_for_search(entry["id"])
                    if loaded:
                        st.session_state["leads"] = loaded
                        st.session_state["loaded_search_meta"] = {
                            "enriched": bool(entry["enriched"]),
                            "scored": bool(entry["scored"]),
                            "emails_found": bool(entry["emails_found"]),
                        }
                        st.rerun()
            with col_del:
                if st.button("Delete", key=f"del_{entry['id']}"):
                    delete_search(entry["id"])
                    st.rerun()
        if len(history) >= 2:
            if st.button("Clear All History"):
                delete_all_searches()
                st.rerun()
    else:
        st.caption("No saved searches yet.")

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
                # Enrich with social media if requested
                if enrich:
                    with st.spinner("Checking websites for social media links..."):
                        leads = enrich_leads(leads)

                # Add lead scoring if requested
                if include_scoring:
                    with st.spinner("Calculating lead scores..."):
                        for lead in leads:
                            try:
                                score_result = calculate_lead_score(lead)
                                lead["lead_score"] = score_result["score"]
                                lead["score_breakdown"] = score_result["breakdown"]
                            except Exception as e:
                                lead["lead_score"] = 0
                                lead["score_breakdown"] = {}

                # Discover emails if requested (Thorough mode only)
                if include_emails and is_thorough:
                    with st.spinner("Discovering decision maker emails (this may take a while)..."):
                        for i, lead in enumerate(leads, 1):
                            try:
                                st.toast(f"Checking email {i}/{len(leads)}: {lead.get('Name', 'Unknown')}")
                                result = discover_emails(lead, thorough=True)
                                lead["email_discovery"] = result

                                # Format primary email for display
                                if result.get("primary_email"):
                                    lead["primary_email"] = result["primary_email"]
                                    # Get icon for first email
                                    first_email_info = result.get("emails", [{}])[0] if result.get("emails") else {}
                                    lead["email_icon"] = first_email_info.get("icon", "🟡")
                                else:
                                    lead["primary_email"] = ""
                                    lead["email_icon"] = "❌"
                            except Exception as e:
                                lead["email_discovery"] = {"emails": [], "primary_email": None}
                                lead["primary_email"] = ""
                                lead["email_icon"] = "❌"

                st.session_state["leads"] = leads
                st.session_state.pop("loaded_search_meta", None)
                search_id = save_search(
                    business_type, location, leads,
                    enriched=enrich,
                    scored=include_scoring,
                    emails_found=(include_emails and is_thorough),
                )
                st.session_state["last_search_id"] = search_id
                st.success(f"Found {len(leads)} leads! (auto-saved)")

        except ScraperError as e:
            st.error(str(e))

# Show results if we have them
if "leads" in st.session_state:
    leads = st.session_state["leads"]

    # Determine which columns to show: use loaded metadata if available,
    # otherwise fall back to live sidebar checkboxes.
    meta = st.session_state.get("loaded_search_meta")
    if meta:
        show_social = meta["enriched"]
        show_scores = meta["scored"]
        show_emails = meta["emails_found"]
    else:
        show_social = enrich
        show_scores = include_scoring
        show_emails = include_emails and is_thorough

    # Prepare display data based on features used
    display_data = []
    for lead in leads:
        row = {
            "Name": lead.get("Name", ""),
            "Address": lead.get("Address", ""),
            "Phone": lead.get("Phone", ""),
            "Website": lead.get("Website", ""),
            "Rating": lead.get("Rating", ""),
            "Reviews": lead.get("Reviews", ""),
        }

        # Add social media if enriched
        if show_social:
            row["Facebook"] = lead.get("Facebook", "➖")
            row["Instagram"] = lead.get("Instagram", "➖")
            row["LinkedIn"] = lead.get("LinkedIn", "➖")
            row["Twitter"] = lead.get("Twitter", "➖")
            row["YouTube"] = lead.get("YouTube", "➖")
            row["TikTok"] = lead.get("TikTok", "➖")

        # Add lead score if calculated
        if show_scores and "lead_score" in lead:
            score = lead.get("lead_score", 0)
            row["Score"] = f"{_get_score_emoji(score)} {score}/100"
            row["Quality"] = _get_score_badge(score)

        # Add emails if discovered
        if show_emails and "email_discovery" in lead:
            discovery = lead.get("email_discovery", {})
            emails_info = discovery.get("emails", [])
            if emails_info and emails_info[0].get("email"):
                # Show first email with icon
                row["Email"] = f"{emails_info[0].get('icon', '🟡')} {emails_info[0].get('email', '')}"
            else:
                row["Email"] = "❌ Not found"

        display_data.append(row)

    df = pd.DataFrame(display_data)

    # Display the dataframe
    st.dataframe(df, use_container_width=True)

    # Score breakdown expander
    if show_scores and any("lead_score" in lead for lead in leads):
        with st.expander("📊 Lead Score Breakdown"):
            st.markdown("""
            **Lead Score Criteria (max 100):**
            - **Rating (25):** 4.5+ = 25, 4.0-4.4 = 20, 3.5-3.9 = 15, <3.5 = 5
            - **Reviews (20):** 100+ = 20, 50-99 = 15, 10-49 = 10, 1-9 = 5
            - **Website (15):** Has website = 15, No website = 0
            - **Social Media (20):** Each platform = 3.3 points (6 max)
            - **Status (10):** OPERATIONAL = 10, else = 0
            - **Category (10):** Service business bonus

            **Quality Levels:**
            - **🟢 High (71-100):** Excellent lead with strong indicators
            - **🟡 Medium (41-70):** Decent lead with some engagement
            - **🔴 Low (0-40):** Basic listing, needs verification
            """)

            # Show breakdown for each lead
            for lead in leads:
                if "lead_score" in lead:
                    score = lead.get("lead_score", 0)
                    breakdown = lead.get("score_breakdown", {})
                    name = lead.get("Name", "Unknown")

                    st.write(f"**{_get_score_emoji(score)} {name}** (Score: {score}/100)")
                    if breakdown:
                        for category, value in breakdown.items():
                            st.markdown(f"&nbsp;&nbsp;• {category}: {value}")
                    st.write("")

    # Export section
    col_csv, col_json = st.columns(2)
    with col_csv:
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="leads.csv",
            mime="text/csv",
        )
    with col_json:
        json_data = json.dumps(leads, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name="leads.json",
            mime="application/json",
        )

# Footer
st.divider()
st.caption("PRESTYJ Lead Scraper — prestyj.com")
