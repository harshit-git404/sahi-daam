# Backend Data Module

## Purpose
This folder is responsible for wholesale/mandi price data and the quick-commerce comparison snapshot, which feed the `/scan-produce` API.

## Current Status
Currently, data is provided via mocked static JSON files.
- `wholesale_prices.json`: Mock data with predefined schemas.
- `quickcommerce_snapshot.json`: Mock quick-commerce data.
- `markup_research.md`: Notes on typical markups.

## Development Stages
- **Stage 1**: Schema defined, mock data (Done)
- **Stage 2**: Real researched static data for flagship commodities + markup research (Next)
- **Stage 3**: Live-fetching via data.gov.in Agmarknet API with a cache-and-daily-refresh pattern, replacing the static wholesale file.

## Future Plans
- Establish a community-verified pricing feedback loop (post-purchase price confirmation).
- Expand beyond the 3 flagship commodities.
- **Note**: Quick-commerce data will stay as a manually-refreshed daily snapshot. No official API exists, and live scraping was deliberately ruled out (see root README for reasoning).
