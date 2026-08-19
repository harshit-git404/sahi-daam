# Frontend (Sahi Daam UI)

## Purpose
The Sahi Daam UI, built from the Stitch export. Features the following screens: `HomeScreen`, `ScanScreen`, `QualityResultScreen`, `PriceBreakdownScreen`, `BargainScreen`, and `HistoryScreen`.

## Current Status
Wired to the backend via `src/services/api.ts` and `adapter.ts`. All screens are functional against live (currently mocked) backend data.

## Development Stages
- **Stage 1**: Stitch UI integrated and wired to backend (Done)
- **Stage 2**: Reflect real data once backend folders complete their stages.
- **Stage 3**: Roadmap features (multi-item basket mode, regional haggling phrasebook, savings/history polish).

## How to Run
1. Install dependencies: `npm install`
2. Start the dev server: `npm run dev`

**Testing on a phone via ngrok:**
To test the app on a mobile device over the internet, set `VITE_API_BASE_URL` in `.env.local` to the backend's ngrok URL (obtained from running `ngrok http 8000`), restart the dev server, and access the app via the frontend's static ngrok domain.

## Future Plans
- Voice haggling (staged: phrasebook mode first, full negotiation later).
- General thrifting expansion (explicitly roadmap-only, not built).
