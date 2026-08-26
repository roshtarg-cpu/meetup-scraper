"""Utility functions for Meetup scraper."""

import os
from urllib.parse import urlparse, parse_qs
from camoufox.async_api import AsyncCamoufox


def _parse_proxy(proxy_url):
    """Parse Apify proxy URL into components."""
    if not proxy_url:
        return None
    
    parsed = urlparse(proxy_url)
    return {
        'server': f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
        'username': parsed.username,
        'password': parsed.password
    }


async def _fetch(url, proxy_url=None):
    """Fetch a URL using Camoufox with optional proxy.
    
    Returns:
        str: Page HTML content or None if failed
    """
    proxy_config = _parse_proxy(proxy_url) if proxy_url else None
    
    try:
        async with AsyncCamoufox(
            headless=True,
            geoip=True,
            proxy=proxy_config
        ) as browser:
            page = await browser.new_page()
            
            # Navigate and wait for network idle
            await page.goto(url, wait_until='networkidle', timeout=90000)
            
            # Additional wait for dynamic content
            await page.wait_for_timeout(3000)
            
            # Get full HTML
            html = await page.content()
            
            await page.close()
            
            # Verify we got real content
            if len(html) < 500:
                return None
                
            return html
            
    except Exception as e:
        print(f"Fetch error for {url}: {e}")
        return None
