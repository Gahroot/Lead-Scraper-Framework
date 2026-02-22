"""Email Discovery Module for PRESTYJ Lead Scraper.

Finds decision maker emails using three-tier approach.
"""

import re
import smtplib
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

# Email regex pattern
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)

# Decision maker email patterns (owner/executive focused, NOT generic info@)
DECISION_MAKER_PATTERNS = [
    # Owner/Founder patterns (highest priority)
    '{first}.{last}@{domain}',
    '{first}{last}@{domain}',
    '{f}{last}@{domain}',
    '{last}.{first}@{domain}',
    '{first}@{domain}',
    '{last}@{domain}',
    # C-Level/Executive patterns
    'ceo@{domain}',
    'founder@{domain}',
    'owner@{domain}',
    'president@{domain}',
    'director@{domain}',
    'principal@{domain}',
    # Management fallbacks
    'manager@{domain}',
    'admin@{domain}',
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def extract_domain_from_url(url: str) -> str:
    """Extract domain from website URL.

    Args:
        url: Website URL like 'https://www.example.com/page'

    Returns:
        Domain like 'example.com'
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain
    except Exception:
        return ""


def extract_emails_from_website(url: str, timeout: int = 10) -> List[str]:
    """Visit website and extract all email addresses using regex.

    Args:
        url: Website URL to scrape
        timeout: Request timeout in seconds

    Returns:
        List of found email addresses
    """
    if not url:
        return []

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    emails = set()

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        html = response.text

        # Find all emails in the HTML
        found = EMAIL_PATTERN.findall(html)
        for email in found:
            # Filter out common non-decision-maker emails
            email_lower = email.lower()
            if not any(prefix in email_lower for prefix in ['noreply', 'no-reply', 'support@', 'info@']):
                emails.add(email.lower())

    except Exception as e:
        print(f"Could not extract emails from {url}: {e}")

    return list(emails)


def extract_owner_name_from_google_places(place_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Try to extract owner name from Google Places data.

    Note: Google Places API typically doesn't include owner names directly.
    This is a placeholder for future enhancement if the API changes.

    Args:
        place_data: Raw Google Places data

    Returns:
        {'first': str, 'last': str, 'confidence': str} or None
    """
    # Currently, Google Places doesn't provide owner names
    # This could be enhanced in the future if the API changes
    return None


def extract_owner_name_from_website(url: str) -> Optional[Dict[str, str]]:
    """Scrape website's About, Team pages for owner/founder names.

    Args:
        url: Website URL

    Returns:
        {'first': str, 'last': str, 'confidence': 'high'|'medium'|'low'} or None
    """
    if not url:
        return None

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    # Pages to check for owner/founder names
    paths_to_check = ['', '/about', '/about-us', '/team', '/meet-the-team', '/our-team', '/founder', '/leadership']

    try:
        base_response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
            allow_redirects=True,
        )
        base_response.raise_for_status()
        base_url = str(base_response.url)

        for path in paths_to_check:
            full_url = urljoin(base_url, path)

            try:
                response = requests.get(
                    full_url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=10,
                )
                response.raise_for_status()
                html = response.text

                # Look for common owner/founder patterns in meta tags
                soup = BeautifulSoup(html, 'html.parser')

                # Check meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    content = meta_desc['content'].lower()
                    for keyword in ['founder', 'owner', 'ceo', 'president', 'started by']:
                        if keyword in content:
                            # This is a simplified heuristic
                            # In production, you'd want to use NLP to extract the actual name
                            pass

                # Check for schema.org Person data
                scripts = soup.find_all('script', type_='application/ld+json')
                for script in scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict):
                            if data.get('@type') == 'Person' or data.get('@type') == 'Founder':
                                name = data.get('name') or data.get('givenName', '')
                                if name:
                                    parts = name.split()
                                    if len(parts) >= 2:
                                        return {
                                            'first': parts[0],
                                            'last': ' '.join(parts[1:]),
                                            'confidence': 'high'
                                        }
                    except (json.JSONDecodeError, AttributeError, TypeError):
                        continue

            except Exception:
                continue

    except Exception as e:
        print(f"Could not extract owner name from {url}: {e}")

    return None


def generate_decision_maker_emails(first_name: str, last_name: str, domain: str) -> List[Dict[str, str]]:
    """Generate possible email addresses for decision makers.

    Args:
        first_name: First name
        last_name: Last name
        domain: Domain name (e.g., 'example.com')

    Returns:
        Ordered list of dicts with {'email': str, 'confidence': str}
    """
    if not domain:
        return []

    emails = []
    first = first_name.lower().strip()
    last = last_name.lower().strip()
    f_initial = first[0] if first else ''

    # High confidence patterns (name-based)
    name_patterns = [
        ('{first}.{last}@{domain}', 'high'),
        ('{first}{last}@{domain}', 'high'),
        ('{f}{last}@{domain}', 'medium'),
        ('{last}.{first}@{domain}', 'medium'),
        ('{first}@{domain}', 'medium'),
        ('{last}@{domain}', 'low'),
    ]

    for pattern, confidence in name_patterns:
        if first and last or pattern.endswith('{first}@{domain}'):
            email = pattern.format(first=first, last=last, f=f_initial, domain=domain)
            emails.append({'email': email, 'confidence': confidence, 'source': 'pattern'})

    # Executive/role-based patterns (lower confidence without name verification)
    role_patterns = [
        'ceo', 'founder', 'owner', 'president', 'director', 'principal', 'manager', 'admin'
    ]

    for role in role_patterns:
        email = f'{role}@{domain}'
        emails.append({'email': email, 'confidence': 'low', 'source': 'role'})

    return emails


def verify_email_smtp(email: str) -> Dict[str, Any]:
    """Verify if email exists using SMTP VRFY or RCPT TO.

    Note: Many mail servers disable VRFY for privacy, so this often returns
    'low' confidence even for valid emails.

    Args:
        email: Email address to verify

    Returns:
        {'valid': bool, 'confidence': str}
    """
    if not email or '@' not in email:
        return {'valid': False, 'confidence': 'none'}

    domain = email.split('@')[1]

    try:
        # Get MX records for the domain
        import dns.resolver
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_host = str(mx_records[0].exchange)

        # Try SMTP connection
        with smtplib.SMTP(timeout=10) as smtp:
            smtp.set_debuglevel(0)
            smtp.connect(mx_host)
            smtp.helo()

            # Try VRFY (often disabled)
            try:
                code, msg = smtp.verify(email)
                if code == 250:
                    return {'valid': True, 'confidence': 'high'}
            except smtplib.SMTPResponseException:
                pass

            # Try RCPT TO (more reliable but still can be blocked)
            try:
                smtp.mail('')
                code, msg = smtp.rcpt(email)
                if code == 250:
                    return {'valid': True, 'confidence': 'medium'}
            except smtplib.SMTPResponseException:
                pass

    except Exception as e:
        # DNS or connection failure - doesn't mean email is invalid
        return {'valid': False, 'confidence': 'none', 'error': str(e)}

    return {'valid': False, 'confidence': 'none'}


def discover_emails(lead: Dict[str, Any], thorough: bool = True) -> Dict[str, Any]:
    """Main function to discover decision maker emails for a lead.

    Args:
        lead: Lead dictionary with website and other info
        thorough: If True, does full website scraping. If False, just generates patterns.

    Returns:
        Dict with emails and status information:
        {
            'emails': [{'email': str, 'icon': str, 'source': str}],
            'primary_email': str or None
        }
        Icons: ✅ Verified, 🔵 Found on website, 🟡 Pattern-generated, ❌ Not found
    """
    result = {
        'emails': [],
        'primary_email': None
    }

    website = lead.get('Website', '')
    domain = extract_domain_from_url(website)

    if not domain:
        result['emails'] = [{'email': '', 'icon': '❌', 'source': 'No domain'}]
        return result

    # Tier 1: Extract emails from website
    website_emails = []
    if thorough and website:
        website_emails = extract_emails_from_website(website)

    # Tier 2: Try to get owner name and generate patterns
    owner_name = None
    if thorough:
        owner_name = extract_owner_name_from_website(website)

    generated_emails = []
    if owner_name:
        generated_emails = generate_decision_maker_emails(
            owner_name['first'],
            owner_name['last'],
            domain
        )
    else:
        # Generate role-based patterns without name
        for role in ['ceo', 'founder', 'owner', 'president', 'manager']:
            generated_emails.append({
                'email': f'{role}@{domain}',
                'confidence': 'low',
                'source': 'role'
            })

    # Combine and deduplicate results
    seen_emails = set()

    # Add website emails (highest confidence)
    for email in website_emails:
        if email not in seen_emails:
            seen_emails.add(email)
            result['emails'].append({
                'email': email,
                'icon': '🔵',
                'source': 'website'
            })
            if not result['primary_email']:
                result['primary_email'] = email

    # Add generated emails
    for email_info in generated_emails:
        email = email_info['email']
        if email not in seen_emails:
            seen_emails.add(email)
            icon = '🟡' if email_info['confidence'] in ['high', 'medium'] else '⚪'
            result['emails'].append({
                'email': email,
                'icon': icon,
                'source': email_info['source']
            })
            if not result['primary_email'] and email_info['confidence'] == 'high':
                result['primary_email'] = email

    # If no emails found, mark as not found
    if not result['emails']:
        result['emails'] = [{'email': '', 'icon': '❌', 'source': 'Not found'}]
    elif not result['primary_email'] and result['emails']:
        result['primary_email'] = result['emails'][0]['email']

    return result
