# Backend Data Module

## Purpose
This folder is responsible for wholesale/mandi price data and the quick-commerce comparison snapshot, which feed the `/scan-produce` API.

## Current Status
- Live-fetching via data.gov.in Agmarknet API is implemented for wholesale prices (using `httpx`).
- Quick-commerce data is provided via a mock snapshot.
- `markup_research.md`: Notes on typical markups.

### API Key & Configuration Setup
To test the live data fetching locally, you must provide your own API key.
1. Create a `.env` file in the `backend/` directory by copying `.env.example`.
2. Add your Open Government Data portal API key: `DATA_GOV_API_KEY=your_key`
3. (Optional) Customize the default search configuration:
   - `DEFAULT_STATE=Tamil Nadu`

*Note: The API client explicitly mimics a browser User-Agent to prevent the data.gov.in WAF from dropping requests.*

## Development Stages
- **Stage 1**: Schema defined, mock data (Done)
- **Stage 2**: Real researched static data for flagship commodities + markup research (Done)
- **Stage 3**: Live-fetching via data.gov.in Agmarknet API (Done)

## Future Plans
- Establish a community-verified pricing feedback loop (post-purchase price confirmation).
- Expand beyond the 3 flagship commodities.
- **Note**: Quick-commerce data will stay as a manually-refreshed daily snapshot. No official API exists, and live scraping was deliberately ruled out (see root README for reasoning).
