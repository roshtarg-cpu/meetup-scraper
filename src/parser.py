"""Parser functions for extracting data from Meetup pages."""

import json
import re
from datetime import datetime


def _extract_next_data(html):
    """Extract __NEXT_DATA__ JSON from Meetup page.
    
    Returns:
        dict: Parsed Next.js data or None
    """
    try:
        # Find __NEXT_DATA__ script tag
        match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            return data
    except Exception as e:
        print(f"Failed to extract __NEXT_DATA__: {e}")
    
    return None


def _parse_event(event_data):
    """Parse a single event from Meetup Apollo GraphQL data.
    
    Args:
        event_data (dict): Raw event data from Apollo state
        
    Returns:
        dict: Cleaned event data
    """
    try:
        # Extract event details
        event_id = event_data.get('id', None)
        event_name = event_data.get('title', None)
        
        # Event URL (Apollo provides it directly)
        event_url = event_data.get('eventUrl', None)
        
        # Group info
        group = event_data.get('group', {})
        group_name = group.get('name', None)
        group_urlname = group.get('urlname', None)
        group_url = f"https://www.meetup.com/{group_urlname}/" if group_urlname else None
        
        # Date/time (Apollo provides ISO format)
        date_time = event_data.get('dateTime', None)
        
        # Location/Venue
        venue = event_data.get('venue', {})
        venue_name = venue.get('name', None) if venue else None
        address = venue.get('address', None) if venue else None
        city = venue.get('city', None) if venue else None
        
        # Event type
        event_type = event_data.get('eventType', None)
        is_online = event_type == 'ONLINE' if event_type else False
        
        # Attendees (Apollo uses 'going' field)
        # Get from rsvps if available
        rsvps_data = event_data.get('rsvps', {})
        attendee_count = None
        if isinstance(rsvps_data, dict):
            attendee_count = rsvps_data.get('totalCount', None)
        
        # Description
        description = event_data.get('description', None)
        
        # Category - extract from group if available
        category = None
        if group and 'category' in group:
            cat_data = group.get('category', {})
            if isinstance(cat_data, dict):
                category = cat_data.get('name', None)
        
        return {
            'eventName': event_name,
            'eventUrl': event_url,
            'groupName': group_name,
            'groupUrl': group_url,
            'dateTime': date_time,
            'venue': venue_name,
            'address': address,
            'city': city,
            'attendeeCount': attendee_count,
            'description': description,
            'category': category,
            'isOnline': is_online,
            'scrapedAt': datetime.utcnow().isoformat() + 'Z'
        }
    
    except Exception as e:
        print(f"Error parsing event: {e}")
        # Return partial data with nulls
        return {
            'eventName': event_data.get('title', None),
            'eventUrl': event_data.get('eventUrl', None),
            'groupName': None,
            'groupUrl': None,
            'dateTime': event_data.get('dateTime', None),
            'venue': None,
            'address': None,
            'city': None,
            'attendeeCount': None,
            'description': None,
            'category': None,
            'isOnline': False,
            'scrapedAt': datetime.utcnow().isoformat() + 'Z'
        }
