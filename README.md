# Meetup Event Scraper — AI Agent Data Feed

Extract events from Meetup.com by location, category, and date. Get comprehensive event details including organizer info, attendee counts, venue data, and descriptions.

## Who It's For

- **AI Agents** (Claude, ChatGPT via Apify MCP) researching local events and communities
- **Event organizers** discovering competitive events and networking opportunities
- **Marketers** analyzing community engagement and event trends
- **Researchers** studying local community dynamics and social networks
- **Businesses** finding relevant industry events and meetups

## AI Agent Queries This Actor Handles

- "Find tech meetups in San Francisco this week"
- "What networking events are happening in New York tomorrow?"
- "Show me online business events this month"
- "Find health and wellness meetups within 10 miles of Austin, TX"
- "List upcoming learning events in Seattle"
- "What are the largest tech meetups in the Bay Area?"
- "Find all AI/ML community events in Boston"
- "Show me in-person social events near me"

## What Data You Get

Each event includes:

- **Event details**: Name, description, date/time, URL
- **Organizer info**: Group name and URL
- **Location data**: Venue name, address, city
- **Attendance**: Number of RSVPs/attendees
- **Type**: Online vs in-person indicator
- **Category**: Event topic/category
- **Timestamp**: When the data was scraped

## Example Input

```json
{
  "location": "San Francisco, CA",
  "radius": 25,
  "category": "Technology",
  "eventType": "both",
  "dateRange": "this-week",
  "maxResults": 50,
  "proxyConfiguration": {
    "useApifyProxy": true,
    "apifyProxyGroups": ["RESIDENTIAL"]
  }
}
```

## Example Output

```json
{
  "eventName": "AI & Machine Learning Meetup",
  "eventUrl": "https://www.meetup.com/ai-ml-sf/events/12345/",
  "groupName": "San Francisco AI/ML Community",
  "groupUrl": "https://www.meetup.com/ai-ml-sf/",
  "dateTime": "2026-08-28T18:00:00",
  "venue": "WeWork Market Street",
  "address": "123 Market St",
  "city": "San Francisco",
  "attendeeCount": 87,
  "description": "Join us for an evening of AI demos and networking...",
  "category": "Technology",
  "isOnline": false,
  "scrapedAt": "2026-08-26T21:30:00Z"
}
```

## Features

- **Comprehensive filtering**: Search by location, radius, category, event type, and date range
- **Rich data**: Full event details with organizer and venue information
- **Flexible output**: Structured JSON perfect for AI agent consumption
- **Reliable extraction**: Uses Playwright for robust SPA rendering
- **Claude/ChatGPT ready**: Designed for AI agents using Apify MCP integration

## MCP Integration

This actor works seamlessly with Claude Code, ChatGPT, and other AI agents through the Apify MCP server. Your AI assistant can discover and analyze local events on demand.

## Technical Notes

- Uses Camoufox (Firefox-based browser) for JavaScript rendering
- Extracts data from Meetup's Next.js application state
- Residential proxies recommended for reliability
- Handles both online and in-person events

## Tags

meetup, events, networking, community, ai-agent-ready, mcp-compatible
