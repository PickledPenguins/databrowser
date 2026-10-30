# An image width cap of zero

Level: failure. max_image_width_px must be a positive number of pixels; leave it out for no cap.

Input:    `python build.py`
Expected: stderr ends `ValueError: max_image_width_px must be positive, got 0`; exit 1, no page written
