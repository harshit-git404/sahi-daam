# Backend ML Module

## Purpose
Responsible for freshness and quality assessment from a produce photo, feeding the `/scan-produce` API.

## Current Status
The local pipeline uses `jazzmacedo/fruits-and-vegetables-detector-36` for produce classification and `models/rottenvsfresh98pval.h5` for freshness inference.

## Development Stages
- **Stage 1**: Interface defined (Done)
- **Stage 2**: Wire in a pretrained produce classifier and the existing H5 freshness model (Done).
- **Stage 3**: Validate and improve the local models against real photos of flagship commodities.

## Future Plans
- Extend freshness detection to general thrifting/goods. (Note: This is a much harder CV problem and is deliberately out of scope for now).
