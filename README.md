# SolarSentinel AI — Solar Panel Fault Detection

A professional AI-based Solar Panel Fault Detection & Inspection Platform powered by Computer Vision (OpenCV), Flask, and Python.

## Features

- **Multi-Image Upload** — Upload 1–20 images via drag-and-drop or file picker
- **AI Fault Detection** — Detects hotspots, overheating, cracks, dust, and shadows
- **Severity Classification** — High (red), Medium (orange), Low (blue) categorization
- **Zoomed Fault Views** — Cropped close-ups of each detected fault
- **EXIF Metadata Extraction** — Filename, date, GPS coordinates, altitude
- **GPS Integration** — "Open in Google Maps" for geotagged images
- **AI Predictions** — Risk assessment, maintenance recommendations, efficiency loss estimates
- **Dashboard Summary** — Health score, risk level, fault counts, severity breakdown
- **Fault Register Table** — Complete sortable fault table
- **PDF Report Generation** — Download comprehensive inspection reports

## Tech Stack

- **Backend:** Python Flask
- **Image Processing:** OpenCV (heuristic-based CV detection)
- **Metadata:** Pillow (EXIF)
- **PDF Reports:** ReportLab
- **Frontend:** HTML, CSS, JavaScript

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Deployment (Render)

1. Push this repo to GitHub
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repo
4. Render will auto-detect the `render.yaml` config
5. Deploy!

## License

MIT
