"""Website scraper — finds social media links from business websites."""

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Social media URL patterns (matches LinkedIn, Facebook, X/Twitter, Instagram, YouTube, TikTok)
SOCIAL_PATTERNS = {
    "LinkedIn": re.compile(
        r"https?://(?:www\.)?linkedin\.com/(?:company|in)/[^/\s\"\'<>]+",
        re.IGNORECASE,
    ),
    "Facebook": re.compile(
        r"https?://(?:www\.)?facebook\.com/[^/\s\"\'<>]+",
        re.IGNORECASE,
    ),
    "Twitter": re.compile(
        r"https?://(?:www\.)?(?:twitter\.com|x\.com)/[^/\s\"\'<>]+",
        re.IGNORECASE,
    ),
    "Instagram": re.compile(
        r"https?://(?:www\.)?instagram\.com/[^/\s\"\'<>]+",
        re.IGNORECASE,
    ),
    "YouTube": re.compile(
        r"https?://(?:www\.)?youtube\.com/(?:@|channel/|c/|user/)[^/\s\"\'<>]+",
        re.IGNORECASE,
    ),
    "TikTok": re.compile(
        r"https?://(?:www\.)?tiktok\.com/@[^/\s\"\'<>]+",
        re.IGNORECASE,
    ),
}

# Skip share/intent URLs — they aren't real profile links
EXCLUDED_PATTERNS = [
    r"/sharer",
    r"/share",
    r"/intent/",
    r"linkedin\.com/shareArticle",
    r"facebook\.com/sharer",
    r"twitter\.com/intent",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _is_excluded(url):
    """Check if a URL is a share/intent link we should skip."""
    return any(re.search(pattern, url, re.IGNORECASE) for pattern in EXCLUDED_PATTERNS)


def _clean_social_url(url, platform):
    """Clean up a social media URL — remove tracking params, validate it."""
    if not url or _is_excluded(url):
        return None

    parsed = urlparse(url)
    if not parsed.netloc:
        return None

    # Rebuild without query params and fragments
    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"

    # Make sure it still matches the pattern after cleaning
    pattern = SOCIAL_PATTERNS.get(platform)
    if pattern and pattern.match(clean):
        return clean

    return None


def get_social_links(url):
    """Visit a website and find all social media profile links.

    Args:
        url: The website to check (e.g. "https://example.com")

    Returns:
        A dictionary with keys like "LinkedIn", "Facebook", etc.
        Each value is either a URL string or None if not found.
    """
    if not url:
        return {platform: None for platform in SOCIAL_PATTERNS}

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    social_links = {platform: None for platform in SOCIAL_PATTERNS}

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
            allow_redirects=True,
        )
        response.raise_for_status()
        html = response.text
        base_url = str(response.url)

        soup = BeautifulSoup(html, "html.parser")

        # Pass 1: Check all <a href="..."> links on the page
        for link in soup.find_all("a", href=True):
            href = str(link["href"])
            if not href.startswith(("http://", "https://")):
                href = urljoin(base_url, href)

            for platform, pattern in SOCIAL_PATTERNS.items():
                if social_links[platform] is None:
                    match = pattern.search(href)
                    if match:
                        clean = _clean_social_url(match.group(0), platform)
                        if clean:
                            social_links[platform] = clean

        # Pass 2: Search the raw HTML for any links we missed
        for platform, pattern in SOCIAL_PATTERNS.items():
            if social_links[platform] is None:
                matches = pattern.findall(html)
                for match in matches:
                    clean = _clean_social_url(match, platform)
                    if clean:
                        social_links[platform] = clean
                        break

    except Exception as e:
        print(f"Could not check {url}: {e}")

    return social_links


def enrich_leads(leads):
    """Add social media links to a list of leads.

    Goes through each lead, visits its website, and adds columns
    for LinkedIn, Facebook, Twitter, Instagram, YouTube, and TikTok.

    Args:
        leads: A list of lead dictionaries (must have a "Website" key)

    Returns:
        The same list, with 6 new social media columns added to each lead.
    """
    total = len(leads)
    for i, lead in enumerate(leads, 1):
        website = lead.get("Website", "")
        print(f"Checking social links ({i}/{total}): {website or 'no website'}")

        if website:
            links = get_social_links(website)
        else:
            links = {platform: None for platform in SOCIAL_PATTERNS}

        for platform, url in links.items():
            lead[platform] = url or ""

    print(f"Done — checked {total} websites for social media links")
    return leads
