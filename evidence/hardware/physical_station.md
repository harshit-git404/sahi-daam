# Tabletop Physical Inspection Station Specification

## 1. System Description
The inspection station is a benchtop apparatus designed for sequential, precedence-constrained access inspection of bulk perishable commodities (potatoes and onions). It physically enforces partial observability by housing commodities in stacked modular trays.

## 2. Mechanical Design & Partial Observability
- **Enclosure**: Multi-tiered opaque acrylic container ($40\text{ cm} \times 30\text{ cm} \times 25\text{ cm}$).
- **Trays**: Stack of 5 interlocking nesting perforated plastic trays ($S_0$ through $S_4$).
- **Access Gating**:
  - Initially, only tray $S_0$ is physically visible to the overhead camera.
  - Sub-surface strata ($S_1$ to $S_4$) are physically obstructed by upper trays.
  - To inspect stratum $k$, an operator must perform the physical action `REMOVE_LAYER` (unstacking tray $k-1$).
- **Operator Role**:
  - The human operator physically carries out tray removal, crate reclosure, and core sample extraction.
  - Per Criterion 4: The operator is strictly an operator following system prompts, NOT an automated actuator.

## 3. Station Interface Loop
```
Physical Produce Crate (Strata S0..S4)
       │
       ▼
Physical RGB Camera Capture (cv2.VideoCapture)
       │
       ▼
Visual Feature Extraction (OpenCV HSV Defect Segmenter)
       │
       ▼
Per-Stratum Bayesian Posterior Belief Update
       │
       ▼
Per-Stratum Exposure Ledger Update (Cumulative Exposure Seconds)
       │
       ▼
Receding-Horizon Inspection Controller (FB7)
       │
       ▼
Operator Instruction ("REMOVE TRAY 1 TO EXPOSE S2")
       │
       ▼
Operator Confirms Physical Tray Removal
       │
       ▼
New Physical State Reached -> Loop repeats until stopping criterion
       │
       ▼
Terminal Teardown & Independent Ground-Truth Evaluation
```
