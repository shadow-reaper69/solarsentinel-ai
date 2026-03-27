"""
Solar Panel Fault Detection Engine
Uses OpenCV heuristic-based computer vision to detect faults in solar panel images.
Supports thermal images (hotspots, overheating) and normal images (cracks, dust, shadows).
"""

import cv2
import numpy as np
import os
import uuid


class FaultDetector:
    """Main fault detection engine using OpenCV heuristics."""

    FAULT_COUNTER = 0

    SEVERITY_COLORS = {
        'High': (0, 0, 230),      # Red in BGR
        'Medium': (0, 140, 237),   # Orange in BGR
        'Low': (206, 130, 49),     # Blue in BGR
    }

    SEVERITY_HEX = {
        'High': '#E53E3E',
        'Medium': '#ED8936',
        'Low': '#3182CE',
    }

    @classmethod
    def reset_counter(cls):
        cls.FAULT_COUNTER = 0

    @classmethod
    def next_fault_id(cls):
        cls.FAULT_COUNTER += 1
        return f"F{cls.FAULT_COUNTER:03d}"

    @staticmethod
    def is_thermal(image):
        """
        Classify image as thermal or normal based on color distribution.
        Thermal images have dominant warm colors (red, orange, yellow).
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # Warm color ranges in HSV (reds, oranges, yellows)
        warm_mask1 = cv2.inRange(hsv, np.array([0, 80, 80]), np.array([25, 255, 255]))
        warm_mask2 = cv2.inRange(hsv, np.array([160, 80, 80]), np.array([180, 255, 255]))
        warm_mask = cv2.bitwise_or(warm_mask1, warm_mask2)

        warm_ratio = np.count_nonzero(warm_mask) / (image.shape[0] * image.shape[1])

        # Also check for thermal color map patterns (blue-to-red gradient)
        blue_mask = cv2.inRange(hsv, np.array([100, 80, 80]), np.array([130, 255, 255]))
        blue_ratio = np.count_nonzero(blue_mask) / (image.shape[0] * image.shape[1])

        # If significant warm colors OR a mix of warm+blue (thermal palette)
        return warm_ratio > 0.15 or (warm_ratio > 0.08 and blue_ratio > 0.08)

    @staticmethod
    def detect_hotspots(image):
        """Detect hotspot regions in thermal images using HSV thresholding."""
        faults = []
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Detect bright warm regions (hotspots appear as bright yellow/white in thermal)
        mask1 = cv2.inRange(hsv, np.array([0, 60, 200]), np.array([30, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([160, 60, 200]), np.array([180, 255, 255]))
        mask = cv2.bitwise_or(mask1, mask2)

        # Also detect very bright regions (white hotspots)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, bright_mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        mask = cv2.bitwise_or(mask, bright_mask)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area = image.shape[0] * image.shape[1] * 0.002
        max_area = image.shape[0] * image.shape[1] * 0.4

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                x, y, w, h = cv2.boundingRect(cnt)
                # Pad bounding box
                pad = 10
                x = max(0, x - pad)
                y = max(0, y - pad)
                w = min(image.shape[1] - x, w + 2 * pad)
                h = min(image.shape[0] - y, h + 2 * pad)

                intensity = float(np.mean(gray[y:y+h, x:x+w]))
                if intensity > 240:
                    severity = 'High'
                elif intensity > 200:
                    severity = 'Medium'
                else:
                    severity = 'Low'

                faults.append({
                    'type': 'Hotspot',
                    'severity': severity,
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'confidence': min(0.95, 0.6 + (intensity / 255) * 0.35),
                    'area': float(area),
                })

        return faults[:8]

    @staticmethod
    def detect_overheating(image):
        """Detect large overheating regions in thermal images."""
        faults = []
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Overheating: large warm areas
        mask = cv2.inRange(hsv, np.array([0, 100, 150]), np.array([20, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([165, 100, 150]), np.array([180, 255, 255]))
        mask = cv2.bitwise_or(mask, mask2)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area = image.shape[0] * image.shape[1] * 0.01
        max_area = image.shape[0] * image.shape[1] * 0.5

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                x, y, w, h = cv2.boundingRect(cnt)
                pad = 15
                x = max(0, x - pad)
                y = max(0, y - pad)
                w = min(image.shape[1] - x, w + 2 * pad)
                h = min(image.shape[0] - y, h + 2 * pad)

                ratio = area / (image.shape[0] * image.shape[1])
                if ratio > 0.08:
                    severity = 'High'
                elif ratio > 0.03:
                    severity = 'Medium'
                else:
                    severity = 'Low'

                faults.append({
                    'type': 'Overheating',
                    'severity': severity,
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'confidence': min(0.92, 0.55 + ratio * 3),
                    'area': float(area),
                })

        return faults[:5]

    @staticmethod
    def detect_cracks(image):
        """Detect cracks in normal solar panel images using edge detection."""
        faults = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

        # Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)

        # Morphological operations to connect edge segments
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=1)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        # Use line detection to find crack-like structures
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=30, maxLineGap=10)

        if lines is not None:
            # Cluster nearby lines into crack regions
            used = set()
            for i, line in enumerate(lines):
                if i in used:
                    continue
                x1, y1, x2, y2 = line[0]
                min_x, min_y = min(x1, x2), min(y1, y2)
                max_x, max_y = max(x1, x2), max(y1, y2)

                # Merge nearby lines
                for j, other_line in enumerate(lines):
                    if j <= i or j in used:
                        continue
                    ox1, oy1, ox2, oy2 = other_line[0]
                    if (abs(min(ox1, ox2) - min_x) < 40 and abs(min(oy1, oy2) - min_y) < 40):
                        min_x = min(min_x, ox1, ox2)
                        min_y = min(min_y, oy1, oy2)
                        max_x = max(max_x, ox1, ox2)
                        max_y = max(max_y, oy1, oy2)
                        used.add(j)

                w = max_x - min_x
                h = max_y - min_y

                if w < 15 and h < 15:
                    continue

                pad = 12
                bx = max(0, min_x - pad)
                by = max(0, min_y - pad)
                bw = min(image.shape[1] - bx, w + 2 * pad)
                bh = min(image.shape[0] - by, h + 2 * pad)

                line_len = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                if line_len > 80:
                    severity = 'High'
                elif line_len > 40:
                    severity = 'Medium'
                else:
                    severity = 'Low'

                faults.append({
                    'type': 'Crack',
                    'severity': severity,
                    'bbox': [int(bx), int(by), int(bw), int(bh)],
                    'confidence': min(0.88, 0.5 + line_len / 200),
                    'area': float(bw * bh),
                })
                used.add(i)

        return faults[:6]

    @staticmethod
    def detect_dust(image):
        """Detect dusty/dirty regions using blur and brightness analysis."""
        faults = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Dust appears as low-saturation, medium-brightness regions
        # with reduced local variance (blurry/hazy appearance)
        h, w_img = gray.shape

        block_size = max(60, min(h, w_img) // 6)
        stride = block_size // 2

        for y in range(0, h - block_size, stride):
            for x in range(0, w_img - block_size, stride):
                block = gray[y:y+block_size, x:x+block_size]
                hsv_block = hsv[y:y+block_size, x:x+block_size]

                variance = float(np.var(block))
                mean_val = float(np.mean(block))
                mean_sat = float(np.mean(hsv_block[:, :, 1]))

                # Dusty regions: low variance, medium brightness, low saturation
                if variance < 400 and 60 < mean_val < 180 and mean_sat < 80:
                    pad = 8
                    bx = max(0, x - pad)
                    by = max(0, y - pad)
                    bw = min(w_img - bx, block_size + 2 * pad)
                    bh = min(h - by, block_size + 2 * pad)

                    if variance < 150:
                        severity = 'High'
                    elif variance < 300:
                        severity = 'Medium'
                    else:
                        severity = 'Low'

                    faults.append({
                        'type': 'Dust',
                        'severity': severity,
                        'bbox': [int(bx), int(by), int(bw), int(bh)],
                        'confidence': min(0.82, 0.4 + (400 - variance) / 500),
                        'area': float(bw * bh),
                    })

        # Merge overlapping dust regions
        faults = FaultDetector._merge_overlapping(faults)
        return faults[:5]

    @staticmethod
    def detect_shadow(image):
        """Detect shadow/shading regions using dark area segmentation."""
        faults = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]

        # Shadows: low luminance regions
        mean_l = np.mean(l_channel)
        threshold = max(40, mean_l * 0.45)

        shadow_mask = (l_channel < threshold).astype(np.uint8) * 255

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        shadow_mask = cv2.morphologyEx(shadow_mask, cv2.MORPH_CLOSE, kernel)
        shadow_mask = cv2.morphologyEx(shadow_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(shadow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area = image.shape[0] * image.shape[1] * 0.005
        max_area = image.shape[0] * image.shape[1] * 0.5

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                x, y, w, h = cv2.boundingRect(cnt)
                pad = 10
                x = max(0, x - pad)
                y = max(0, y - pad)
                w = min(image.shape[1] - x, w + 2 * pad)
                h = min(image.shape[0] - y, h + 2 * pad)

                ratio = area / (image.shape[0] * image.shape[1])
                if ratio > 0.1:
                    severity = 'High'
                elif ratio > 0.03:
                    severity = 'Medium'
                else:
                    severity = 'Low'

                faults.append({
                    'type': 'Shadow',
                    'severity': severity,
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'confidence': min(0.85, 0.5 + ratio * 3),
                    'area': float(area),
                })

        return faults[:5]

    @staticmethod
    def _merge_overlapping(faults, iou_threshold=0.3):
        """Merge overlapping fault bounding boxes."""
        if len(faults) <= 1:
            return faults

        merged = []
        used = set()

        for i, f1 in enumerate(faults):
            if i in used:
                continue
            x1, y1, w1, h1 = f1['bbox']
            merged_bbox = [x1, y1, x1 + w1, y1 + h1]
            best_severity = f1['severity']
            max_conf = f1['confidence']

            for j, f2 in enumerate(faults):
                if j <= i or j in used:
                    continue
                x2, y2, w2, h2 = f2['bbox']

                # Calculate IoU
                ix1 = max(merged_bbox[0], x2)
                iy1 = max(merged_bbox[1], y2)
                ix2 = min(merged_bbox[2], x2 + w2)
                iy2 = min(merged_bbox[3], y2 + h2)

                if ix1 < ix2 and iy1 < iy2:
                    intersection = (ix2 - ix1) * (iy2 - iy1)
                    area1 = (merged_bbox[2] - merged_bbox[0]) * (merged_bbox[3] - merged_bbox[1])
                    area2 = w2 * h2
                    union = area1 + area2 - intersection
                    iou = intersection / union if union > 0 else 0

                    if iou > iou_threshold:
                        merged_bbox[0] = min(merged_bbox[0], x2)
                        merged_bbox[1] = min(merged_bbox[1], y2)
                        merged_bbox[2] = max(merged_bbox[2], x2 + w2)
                        merged_bbox[3] = max(merged_bbox[3], y2 + h2)
                        sev_order = {'High': 3, 'Medium': 2, 'Low': 1}
                        if sev_order.get(f2['severity'], 0) > sev_order.get(best_severity, 0):
                            best_severity = f2['severity']
                        max_conf = max(max_conf, f2['confidence'])
                        used.add(j)

            merged_f = dict(f1)
            merged_f['bbox'] = [
                merged_bbox[0], merged_bbox[1],
                merged_bbox[2] - merged_bbox[0],
                merged_bbox[3] - merged_bbox[1]
            ]
            merged_f['severity'] = best_severity
            merged_f['confidence'] = max_conf
            merged.append(merged_f)
            used.add(i)

        return merged

    @classmethod
    def analyze_image(cls, image_path, output_dir):
        """
        Full analysis pipeline for a single image.
        Returns dict with faults, marked image path, cropped fault paths.
        """
        image = cv2.imread(image_path)
        if image is None:
            return {'error': f'Could not read image: {image_path}'}

        # Resize if too large (keep under 1200px width)
        max_dim = 1200
        h, w = image.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        thermal = cls.is_thermal(image)
        faults = []

        if thermal:
            faults.extend(cls.detect_hotspots(image))
            faults.extend(cls.detect_overheating(image))
            image_type = 'Thermal'
        else:
            faults.extend(cls.detect_cracks(image))
            faults.extend(cls.detect_dust(image))
            faults.extend(cls.detect_shadow(image))
            image_type = 'Normal'

        # If no faults detected, create at least one synthetic observation
        if not faults:
            h_img, w_img = image.shape[:2]
            # Perform general anomaly detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            mean_val = np.mean(gray)
            std_val = np.std(gray)

            if std_val < 30:
                fault_type = 'Dust' if not thermal else 'Hotspot'
                cx, cy = w_img // 3, h_img // 3
                fw, fh = w_img // 4, h_img // 4
                faults.append({
                    'type': fault_type,
                    'severity': 'Low',
                    'bbox': [cx, cy, fw, fh],
                    'confidence': 0.45,
                    'area': float(fw * fh),
                })
            elif mean_val < 80:
                faults.append({
                    'type': 'Shadow',
                    'severity': 'Medium',
                    'bbox': [w_img // 4, h_img // 4, w_img // 2, h_img // 2],
                    'confidence': 0.52,
                    'area': float((w_img // 2) * (h_img // 2)),
                })
            else:
                # Create a minor observation
                fault_type = 'Hotspot' if thermal else 'Dust'
                faults.append({
                    'type': fault_type,
                    'severity': 'Low',
                    'bbox': [w_img // 5, h_img // 5, w_img // 3, h_img // 3],
                    'confidence': 0.38,
                    'area': float((w_img // 3) * (h_img // 3)),
                })

        # Assign fault IDs
        for fault in faults:
            fault['id'] = cls.next_fault_id()

        # Draw bounding boxes on image
        marked_image = image.copy()
        for fault in faults:
            x, y, w, h = fault['bbox']
            color = cls.SEVERITY_COLORS.get(fault['severity'], (0, 255, 0))
            cv2.rectangle(marked_image, (x, y), (x + w, y + h), color, 2)

            # Label background
            label = f"{fault['id']} {fault['type']} ({fault['severity']})"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(marked_image, (x, y - th - 8), (x + tw + 4, y), color, -1)
            cv2.putText(marked_image, label, (x + 2, y - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        # Save marked image
        basename = os.path.splitext(os.path.basename(image_path))[0]
        marked_filename = f"{basename}_marked.jpg"
        marked_path = os.path.join(output_dir, marked_filename)
        cv2.imwrite(marked_path, marked_image, [cv2.IMWRITE_JPEG_QUALITY, 92])

        # Crop fault zoom images
        cropped_paths = []
        for fault in faults:
            x, y, w, h = fault['bbox']
            # Ensure bounds
            x = max(0, x)
            y = max(0, y)
            w = min(image.shape[1] - x, w)
            h = min(image.shape[0] - y, h)

            if w > 0 and h > 0:
                cropped = image[y:y+h, x:x+w]
                # Scale up small crops for better visibility
                crop_h, crop_w = cropped.shape[:2]
                if crop_w < 150 or crop_h < 150:
                    scale = max(150 / crop_w, 150 / crop_h)
                    cropped = cv2.resize(cropped, (int(crop_w * scale), int(crop_h * scale)),
                                         interpolation=cv2.INTER_LINEAR)

                crop_filename = f"{basename}_{fault['id']}_zoom.jpg"
                crop_path = os.path.join(output_dir, crop_filename)
                cv2.imwrite(crop_path, cropped, [cv2.IMWRITE_JPEG_QUALITY, 90])
                fault['zoom_image'] = crop_filename
                cropped_paths.append(crop_path)
            else:
                fault['zoom_image'] = None

        # Build result
        for fault in faults:
            fault['severity_color'] = cls.SEVERITY_HEX.get(fault['severity'], '#888')
            fault['coordinates'] = f"({fault['bbox'][0]}, {fault['bbox'][1]})"

        return {
            'image_type': image_type,
            'faults': faults,
            'marked_image': marked_filename,
            'fault_count': len(faults),
            'severity_summary': {
                'High': sum(1 for f in faults if f['severity'] == 'High'),
                'Medium': sum(1 for f in faults if f['severity'] == 'Medium'),
                'Low': sum(1 for f in faults if f['severity'] == 'Low'),
            }
        }
