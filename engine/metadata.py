"""
EXIF Metadata Extraction for Solar Panel Images.
Extracts file name, date taken, GPS coordinates, and altitude using Pillow.
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os
from datetime import datetime


def _get_exif_data(image_path):
    """Extract all EXIF data from an image file."""
    try:
        img = Image.open(image_path)
        exif_raw = img._getexif()
        if exif_raw is None:
            return {}

        exif_data = {}
        for tag_id, value in exif_raw.items():
            tag = TAGS.get(tag_id, tag_id)
            exif_data[tag] = value

        return exif_data
    except Exception:
        return {}


def _convert_gps_to_degrees(gps_coords, gps_ref):
    """Convert GPS coordinates from EXIF format to decimal degrees."""
    try:
        d = float(gps_coords[0])
        m = float(gps_coords[1])
        s = float(gps_coords[2])

        degrees = d + (m / 60.0) + (s / 3600.0)

        if gps_ref in ['S', 'W']:
            degrees = -degrees

        return round(degrees, 6)
    except (TypeError, IndexError, ValueError, ZeroDivisionError):
        return None


def _extract_gps(exif_data):
    """Extract GPS information from EXIF data."""
    gps_info = exif_data.get('GPSInfo', None)
    if gps_info is None:
        return None, None, None

    gps_data = {}
    for key, val in gps_info.items():
        tag = GPSTAGS.get(key, key)
        gps_data[tag] = val

    latitude = None
    longitude = None
    altitude = None

    if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
        latitude = _convert_gps_to_degrees(gps_data['GPSLatitude'], gps_data['GPSLatitudeRef'])

    if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
        longitude = _convert_gps_to_degrees(gps_data['GPSLongitude'], gps_data['GPSLongitudeRef'])

    if 'GPSAltitude' in gps_data:
        try:
            altitude = round(float(gps_data['GPSAltitude']), 2)
        except (TypeError, ValueError):
            altitude = None

    return latitude, longitude, altitude


def extract_metadata(image_path):
    """
    Extract metadata from an image file.
    Returns dict with filename, date_taken, gps_latitude, gps_longitude, altitude.
    """
    filename = os.path.basename(image_path)

    exif_data = _get_exif_data(image_path)

    # Date taken
    date_taken = None
    for date_field in ['DateTimeOriginal', 'DateTimeDigitized', 'DateTime']:
        if date_field in exif_data:
            try:
                raw = str(exif_data[date_field])
                dt = datetime.strptime(raw, '%Y:%m:%d %H:%M:%S')
                date_taken = dt.strftime('%Y-%m-%d %H:%M:%S')
                break
            except (ValueError, TypeError):
                continue

    # GPS
    latitude, longitude, altitude = _extract_gps(exif_data)

    # File stats as fallback for date
    if date_taken is None:
        try:
            stat = os.stat(image_path)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            date_taken = mtime.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass

    return {
        'filename': filename,
        'date_taken': date_taken if date_taken else 'Not available',
        'gps_latitude': latitude if latitude is not None else 'Not available',
        'gps_longitude': longitude if longitude is not None else 'Not available',
        'altitude': f"{altitude} m" if altitude is not None else 'Not available',
        'has_gps': latitude is not None and longitude is not None,
    }
