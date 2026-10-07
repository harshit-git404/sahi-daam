# Parameter Calibration Protocol & Data Separation

## Dataset Separation
- `calibration_data/`: Used exclusively to tune prior hyper-parameters, thermal shock coefficient ($eta = 0.12$), and sensor noise ($\sigma = 0.035$).
- `heldout_data/`: Held-out validation lots for statistical benchmarking.
- `validation_data/`: Physical bench test validation runs.

No ground-truth labels from held-out or test lots were ever used to fit planner parameters.
