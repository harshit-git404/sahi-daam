# Backend ML Module

## Purpose
Responsible for freshness and quality assessment from a produce photo, feeding the `/scan-produce` API.

## Current Status
The typed interface (`predict_freshness` / `FreshnessResult`) is defined, but not yet implemented.

## Development Stages
- **Stage 1**: Interface defined (Done)
- **Stage 2**: Wire in a pretrained model (e.g., `jazzmacedo/fruits-and-vegetables-detector-36` or `RicardoPoleo/custom_cnn_model` from Hugging Face), validated against real photos of flagship commodities.
- **Stage 3**: Light fine-tuning on a fresh/rotten dataset if off-the-shelf accuracy isn't good enough for the 3 flagship commodities.

## Future Plans
- Extend freshness detection to general thrifting/goods. (Note: This is a much harder CV problem and is deliberately out of scope for now).
