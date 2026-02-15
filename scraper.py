"""Google Places lead scraper — finds businesses by type and location."""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
BASE_URL = "https://places.googleapis.com/v1"

FIELD_MASK = ",".join([
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.internationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.types",
    "places.businessStatus",
])


class ScraperError(Exception):
    """Something went wrong with the Google Places search."""
    pass


def _format_place(place):
    """Turn a raw Google Places result into a clean, friendly dictionary."""
    display_name = place.get("displayName", {})
    name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)

    phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")

    types = place.get("types", [])
    category = types[0].replace("_", " ").title() if types else ""

    status_raw = place.get("businessStatus", "OPERATIONAL")
    status = status_raw.replace("_", " ").title()

    return {
        "Name": name,
        "Phone": phone or "",
        "Address": place.get("formattedAddress", ""),
        "Website": place.get("websiteUri", ""),
        "Rating": place.get("rating", ""),
        "Reviews": place.get("userRatingCount", 0),
        "Category": category,
        "Status": status,
    }


def search_leads(business_type, location, max_results=20):
    """Search Google Places for businesses and return a list of leads.

    Args:
        business_type: What kind of business (e.g. "plumbers")
        location: City or area (e.g. "Austin, TX")
        max_results: How many results you want (1-60)

    Returns:
        A list of dictionaries, one per business found.

    Raises:
        ScraperError: If something goes wrong (bad API key, network issue, etc.)
    """
    if not API_KEY:
        raise ScraperError(
            "No API key found. Open your .env file and add your Google Places API key."
        )

    query = f"{business_type} in {location}"
    results = []
    next_page_token = None

    session = requests.Session()
    session.headers.update({
        "X-Goog-Api-Key": API_KEY,
        "Content-Type": "application/json",
        "X-Goog-FieldMask": FIELD_MASK,
    })

    while len(results) < max_results:
        payload = {
            "textQuery": query,
            "maxResultCount": min(max_results - len(results), 20),
        }
        if next_page_token:
            payload["pageToken"] = next_page_token

        # Simple 2-attempt retry
        last_error = None
        for attempt in range(2):
            try:
                response = session.post(f"{BASE_URL}/places:searchText", json=payload)

                if response.status_code in (401, 403):
                    raise ScraperError(
                        "Invalid API key. Double-check the key in your .env file."
                    )
                if response.status_code == 429:
                    raise ScraperError(
                        "Too many requests. Wait a minute and try again."
                    )
                if response.status_code >= 400:
                    raise ScraperError(f"Google API error: {response.text}")

                data = response.json()
                last_error = None
                break

            except ScraperError:
                raise
            except Exception as e:
                last_error = e
                if attempt == 0:
                    time.sleep(1)

        if last_error:
            raise ScraperError(f"Could not reach Google: {last_error}")

        places = data.get("places", [])
        if not places:
            break

        for place in places:
            if len(results) >= max_results:
                break
            results.append(_format_place(place))

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

        time.sleep(0.3)

    print(f"Found {len(results)} leads for '{business_type}' in {location}")
    return results
