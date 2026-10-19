"""Validate YOLO detection labels, not segmentation or pose labels."""
import math
import re

def validate_yolo(text: str, class_count: int) -> dict:
    if not isinstance(text, str) or len(text) > 100000:
        raise ValueError('Label text must be at most 100,000 characters')
    if isinstance(class_count, bool) or not isinstance(class_count, int) or class_count < 1:
        raise ValueError('class_count must be a positive integer')
    issues, boxes, seen = [], [], set()
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        tokens = line.split()
        if len(tokens) != 5:
            issues.append({'line': number, 'code': 'wrong_column_count'})
            continue
        if not re.fullmatch(r'\d+', tokens[0]) or not 0 <= int(tokens[0]) < class_count:
            issues.append({'line': number, 'code': 'invalid_class'})
            continue
        try:
            x, y, width, height = map(float, tokens[1:])
        except ValueError:
            issues.append({'line': number, 'code': 'invalid_number'})
            continue
        values = (x, y, width, height)
        if not all(math.isfinite(v) for v in values):
            issues.append({'line': number, 'code': 'nonfinite_coordinate'})
            continue
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < width <= 1 and 0 < height <= 1):
            issues.append({'line': number, 'code': 'coordinate_out_of_range'})
            continue
        tolerance = 1e-9
        if (x-width/2 < -tolerance or y-height/2 < -tolerance
                or x+width/2 > 1+tolerance or y+height/2 > 1+tolerance):
            issues.append({'line': number, 'code': 'box_outside_image'})
            continue
        key = (int(tokens[0]), *values)
        if key in seen:
            issues.append({'line': number, 'code': 'duplicate_box'})
            continue
        seen.add(key)
        boxes.append({'line': number, 'class_id': key[0], 'x': x, 'y': y,
                      'width': width, 'height': height})
    return {'valid': not issues, 'valid_box_count': len(boxes), 'boxes': boxes,
            'issues': issues, 'empty_label': not text.strip()}
