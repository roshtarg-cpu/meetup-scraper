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
    """Parse a single event from Meetup data.
    
    Args:
        event_data (dict): Raw event data from API/Next.js
        
    Returns:
        dict: Cleaned event data
    """
    try:
        # Extract event details
        event_id = event_data.get('id', None)
        event_name = event_data.get('title') or event_data.get('name', None)
        
        # Event URL
        event_url = None
        if 'link' in event_data:
            event_url = event_data['link']
        elif 'urlname' in event_data:
            event_url = f"https://www.meetup.com/{event_data['urlname']}/events/{event_id}/"
        
        # Group info
        group = event_data.get('group', {})
        group_name = group.get('name', None)
        group_url = None
        if 'urlname' in group:
            group_url = f"https://www.meetup.com/{group['urlname']}/"
        
        # Date/time
        date_time = event_data.get('dateTime') or event_data.get('time', None)
        if date_time and isinstance(date_time, (int, float)):
            # Convert timestamp to ISO format
            date_time = datetime.fromtimestamp(date_time / 1000).isoformat()
        
        # Location
        venue = event_data.get('venue', {})
        venue_name = venue.get('name', None)
        address = venue.get('address', None)
        city = venue.get('city', None)
        
        # Online vs in-person
        is_online = event_data.get('isOnline', False)
        
        # Attendees
        attendee_count = event_data.get('going') or event_data.get('rsvpCount', None)
        
        # Description
        description = event_data.get('description', None)
        
        # Category/topics
        topics = event_data.get('topics', [])
        category = topics[0].get('name') if topics else None
        
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
            'eventName': event_data.get('name') or event_data.get('title', None),
            'eventUrl': None,
            'groupName': None,
            'groupUrl': None,
            'dateTime': None,
            'venue': None,
            'address': None,
            'city': None,
            'attendeeCount': None,
            'description': None,
            'category': None,
            'isOnline': False,
            'scrapedAt': datetime.utcnow().isoformat() + 'Z'
        }
