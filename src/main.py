"""Main entry point for Meetup scraper actor."""

import asyncio
import os
from apify import Actor
from .utils import _fetch
from .parser import _extract_next_data, _parse_event


async def main():
    """Main scraper logic."""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        # Extract parameters
        location = actor_input.get('location', 'San Francisco, CA')
        radius = actor_input.get('radius', 25)
        category = actor_input.get('category', '')
        event_type = actor_input.get('eventType', 'both')
        date_range = actor_input.get('dateRange', 'upcoming')
        max_results = actor_input.get('maxResults', 50)
        
        # Proxy configuration
        proxy_config = actor_input.get('proxyConfiguration', {})
        proxy_url = None
        
        if proxy_config.get('useApifyProxy'):
            # Get proxy password from environment
            proxy_password = os.getenv('APIFY_PROXY_PASSWORD') or Actor.get_env().get('proxy_password')
            
            if proxy_password:
                proxy_groups = proxy_config.get('apifyProxyGroups', ['RESIDENTIAL'])
                group = proxy_groups[0] if proxy_groups else 'RESIDENTIAL'
                proxy_url = f"http://groups-{group}:{proxy_password}@proxy.apify.com:8000"
        
        Actor.log.info(f"Starting Meetup scraper")
        Actor.log.info(f"Location: {location}, Radius: {radius}mi")
        Actor.log.info(f"Max results: {max_results}")
        
        # Build search URL
        # Meetup search URL format
        base_url = "https://www.meetup.com/find/"
        
        # Add location and filters as query params
        url = f"{base_url}?location={location}&source=EVENTS"
        
        if category:
            url += f"&categoryId={category}"
        
        if event_type == 'online':
            url += "&eventType=online"
        elif event_type == 'in-person':
            url += "&eventType=physical"
        
        Actor.log.info(f"Fetching: {url}")
        
        # Fetch the page
        html = await _fetch(url, proxy_url)
        
        if not html:
            Actor.log.error("Failed to fetch Meetup page")
            await Actor.exit()
            return
        
        Actor.log.info(f"Page fetched: {len(html)} bytes")
        
        # Extract Next.js data
        next_data = _extract_next_data(html)
        
        if not next_data:
            Actor.log.error("Failed to extract __NEXT_DATA__")
            await Actor.exit()
            return
        
        Actor.log.info("__NEXT_DATA__ extracted successfully")
        
        # Navigate the Next.js data structure to find events
        # The structure varies, but events are typically under props.pageProps
        events_data = []
        
        try:
            page_props = next_data.get('props', {}).get('pageProps', {})
            
            # Try different possible locations for events data
            if 'events' in page_props:
                events_data = page_props['events']
            elif 'data' in page_props and isinstance(page_props['data'], dict):
                if 'events' in page_props['data']:
                    events_data = page_props['data']['events']
                elif 'results' in page_props['data']:
                    events_data = page_props['data']['results']
            
            # Also check if there's a query result structure
            if not events_data and 'query' in next_data.get('props', {}):
                query_data = next_data['props'].get('query', {})
                if 'events' in query_data:
                    events_data = query_data['events']
                    
        except Exception as e:
            Actor.log.error(f"Error navigating Next.js data: {e}")
        
        if not events_data:
            Actor.log.warning("No events found in __NEXT_DATA__ structure")
            # Save the raw data for debugging
            await Actor.set_value('DEBUG-NEXT-DATA', next_data)
            await Actor.exit()
            return
        
        Actor.log.info(f"Found {len(events_data)} events in data")
        
        # Parse and push events
        item_count = 0
        
        for event_raw in events_data[:max_results]:
            try:
                event = _parse_event(event_raw)
                
                # Push to dataset
                await Actor.push_data(event)
                item_count += 1
                
                if item_count % 10 == 0:
                    Actor.log.info(f"Scraped {item_count} events...")
                    
            except Exception as e:
                Actor.log.error(f"Error processing event: {e}")
                continue
        
        Actor.log.info(f"Scraping complete: {item_count} events scraped")
        
        # Save task context (MANDATORY)
        await Actor.set_value('SAVED-TASK', {
            'actorId': Actor.get_env().get('actor_id'),
            'actorRunId': Actor.get_env().get('actor_run_id'),
            'defaultDatasetId': Actor.get_env().get('default_dataset_id'),
            'startedAt': Actor.get_env().get('started_at'),
            'input': actor_input,
            'stats': {
                'itemsScraped': item_count,
                'requestsMade': 1,
                'errors': 0
            }
        })


if __name__ == '__main__':
    asyncio.run(main())
