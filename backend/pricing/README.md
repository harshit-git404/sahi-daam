# Backend Pricing Engine

## Purpose
Handles the fair-price and haggle-verdict calculation logic, feeding the `/scan-produce` and `/haggle-check` APIs.

## Current Status
Typed interfaces (`calculate_fair_price`, `calculate_haggle_verdict`) are defined, but not yet implemented.

## Development Stages
- **Stage 1**: Interfaces defined (Done)
- **Stage 2**: Basic interpretable math (wholesale + markup range + quality adjustment).
- **Stage 3**: Confidence-aware refinement (handling thin-sample markup data via pooling, if time allows).

## Future Plans
- Introduce named deviation patterns and richer haggle reasoning.
