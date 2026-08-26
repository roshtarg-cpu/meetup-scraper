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
        
        # Extract events from Apollo GraphQL state
        # Meetup uses Apollo Client which caches data in __APOLLO_STATE__
        events_data = []
        
        try:
            page_props = next_data.get('props', {}).get('pageProps', {})
            apollo_state = page_props.get('__APOLLO_STATE__', {})
            
            if not apollo_state:
                Actor.log.warning("No Apollo state found in __NEXT_DATA__")
                await Actor.set_value('DEBUG-NEXT-DATA', next_data)
                await Actor.exit()
                return
            
            root_query = apollo_state.get('ROOT_QUERY', {})
            
            # Find recommendedEvents key (has dynamic query params in key name)
            rec_events_key = None
            for key in root_query.keys():
                if key.startswith('recommendedEvents'):
                    rec_events_key = key
                    break
            
            if not rec_events_key:
                Actor.log.warning("No recommendedEvents query found in Apollo state")
                await Actor.set_value('DEBUG-NEXT-DATA', next_data)
                await Actor.exit()
                return
            
            rec_events = root_query[rec_events_key]
            edges = rec_events.get('edges', [])
            
            Actor.log.info(f"Found {len(edges)} event edges in Apollo state")
            
            # Dereference Apollo cache references to get actual event objects
            for edge in edges:
                if '__ref' in edge:
                    edge_obj = apollo_state[edge['__ref']]
                    if 'node' in edge_obj and '__ref' in edge_obj['node']:
                        event_ref = edge_obj['node']['__ref']
                        event_data = apollo_state[event_ref]
                        
                        # Dereference nested objects (group, venue)
                        if 'group' in event_data and isinstance(event_data['group'], dict) and '__ref' in event_data['group']:
                            group_ref = event_data['group']['__ref']
                            event_data['group'] = apollo_state.get(group_ref, {})
                        
                        if 'venue' in event_data and isinstance(event_data['venue'], dict) and '__ref' in event_data['venue']:
                            venue_ref = event_data['venue']['__ref']
                            event_data['venue'] = apollo_state.get(venue_ref, {})
                        
                        events_data.append(event_data)
                    
        except Exception as e:
            Actor.log.error(f"Error extracting events from Apollo state: {e}")
            await Actor.set_value('DEBUG-NEXT-DATA', next_data)
            await Actor.exit()
            return
        
        if not events_data:
            Actor.log.warning("No events found in Apollo state")
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
