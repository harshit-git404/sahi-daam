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
2. Start the dev server: `npm run dev -- --host`

**Testing on a phone via ngrok:**
Because the frontend Vite server proxies `/api` requests directly to the local backend, you only need a single ngrok tunnel. 
Start both servers locally, then run: `ngrok http 5173` (or `ngrok http 5173 --domain=your-domain.ngrok-free.app`). Access the resulting URL on your mobile device.
*(Note: Do not set `VITE_API_BASE_URL` in `.env.local` for ngrok testing unless you are explicitly bypassing the proxy.)*

## Future Plans
- Voice haggling (staged: phrasebook mode first, full negotiation later).
- General thrifting expansion (explicitly roadmap-only, not built).
