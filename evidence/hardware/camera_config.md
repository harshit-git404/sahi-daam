# Camera Configuration Protocol

## 1. Video Capture Parameters
- **OpenCV Backend**: `cv2.CAP_DSHOW` (DirectShow on Windows)
- **Device Index**: `0`
- **Resolution**: Width = 640 px, Height = 480 px
- **Frame Rate**: 30.0 FPS
- **Color Space**: BGR (Blue-Green-Red) 3-channel unsigned 8-bit integer array (`uint8`)

## 2. Image Quality Metric Extraction
For each acquired physical frame, the following metrics are computed in real time:
- **Sharpness / Focus Quality**: Variance of Laplacian filter:
  $$\text{Var}(\nabla^2 I) = \frac{1}{N} \sum_{x,y} (\nabla^2 I(x,y) - \mu_{\nabla^2})^2$$
  Threshold: Value $> 100.0$ confirms clear focus; values $< 60.0$ indicate motion blur or occlusion.
- **Mean Luminance (Brightness)**: Mean grayscale intensity:
  $$\mu_Y = \frac{1}{N} \sum_{x,y} (0.299 R + 0.587 G + 0.114 B)$$
  Acceptable band: $80 \le \mu_Y \le 180$.
- **Produce Area Coverage**: Fraction of pixels within HSV potato/onion color bounds ($H \in [10, 35], S \ge 40$).
