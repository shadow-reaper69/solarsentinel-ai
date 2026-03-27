"""
SolarSentinel AI — Solar Panel Fault Detection System
Flask Backend Application
"""

import os
import json
import shutil
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file, url_for
from werkzeug.utils import secure_filename

from engine.detector import FaultDetector
from engine.metadata import extract_metadata
from engine.predictor import generate_predictions, calculate_health_score, get_risk_level
from engine.report import generate_pdf_report

# ── App Configuration ──
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max total
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'processed')
app.config['REPORTS_FOLDER'] = os.path.join(os.path.dirname(__file__), 'reports')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif', 'webp'}

# Create directories
for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER'], app.config['REPORTS_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Store latest analysis results for report generation
latest_results = []


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_images():
    """
    Process uploaded images through the fault detection pipeline.
    Accepts up to 20 images, returns JSON with analysis results.
    """
    global latest_results

    if 'images' not in request.files:
        return jsonify({'error': 'No images uploaded'}), 400

    files = request.files.getlist('images')

    if len(files) == 0:
        return jsonify({'error': 'No images selected'}), 400

    if len(files) > 20:
        return jsonify({'error': 'Maximum 20 images allowed'}), 400

    # Clean previous uploads and processed files
    for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER']]:
        for f in os.listdir(folder):
            fp = os.path.join(folder, f)
            if os.path.isfile(fp):
                os.remove(fp)

    # Reset fault counter
    FaultDetector.reset_counter()

    results = []
    all_faults = []

    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid collisions
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{int(datetime.now().timestamp() * 1000)}{ext}"
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(upload_path)

            # ── Run Analysis Pipeline ──
            # 1. Detect faults
            detection_result = FaultDetector.analyze_image(
                upload_path,
                app.config['PROCESSED_FOLDER']
            )

            if 'error' in detection_result:
                results.append({
                    'filename': filename,
                    'original_filename': filename,
                    'error': detection_result['error']
                })
                continue

            # 2. Extract metadata
            metadata = extract_metadata(upload_path)

            # 3. Generate predictions
            predictions = generate_predictions(detection_result['faults'])

            # 4. Build result
            image_result = {
                'filename': filename,
                'original_filename': filename,
                'stored_filename': unique_filename,
                'image_type': detection_result['image_type'],
                'faults': detection_result['faults'],
                'fault_count': detection_result['fault_count'],
                'severity_summary': detection_result['severity_summary'],
                'marked_image': detection_result['marked_image'],
                'metadata': metadata,
                'predictions': predictions,
                'upload_url': url_for('static', filename=f'uploads/{unique_filename}'),
                'marked_url': url_for('static', filename=f'processed/{detection_result["marked_image"]}'),
            }

            # Add zoom image URLs
            for fault in image_result['faults']:
                if fault.get('zoom_image'):
                    fault['zoom_url'] = url_for('static', filename=f'processed/{fault["zoom_image"]}')
                else:
                    fault['zoom_url'] = None

            results.append(image_result)
            all_faults.extend(detection_result['faults'])

    # ── Dashboard Summary ──
    health_score = calculate_health_score(all_faults)
    risk_level = get_risk_level(health_score)

    summary = {
        'total_images': len(results),
        'total_faults': len(all_faults),
        'hotspot_count': sum(1 for f in all_faults if f['type'] == 'Hotspot'),
        'overheating_count': sum(1 for f in all_faults if f['type'] == 'Overheating'),
        'crack_count': sum(1 for f in all_faults if f['type'] == 'Crack'),
        'dust_count': sum(1 for f in all_faults if f['type'] == 'Dust'),
        'shadow_count': sum(1 for f in all_faults if f['type'] == 'Shadow'),
        'severity_breakdown': {
            'High': sum(1 for f in all_faults if f['severity'] == 'High'),
            'Medium': sum(1 for f in all_faults if f['severity'] == 'Medium'),
            'Low': sum(1 for f in all_faults if f['severity'] == 'Low'),
        },
        'health_score': health_score,
        'risk_level': risk_level,
    }

    # Store for PDF report
    latest_results = results

    return jsonify({
        'success': True,
        'summary': summary,
        'results': results,
    })


@app.route('/report', methods=['GET'])
def generate_report():
    """Generate and download PDF report from latest analysis."""
    global latest_results

    if not latest_results:
        return jsonify({'error': 'No analysis results available. Please upload and analyze images first.'}), 400

    report_filename = f"solar_inspection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    report_path = os.path.join(app.config['REPORTS_FOLDER'], report_filename)

    try:
        generate_pdf_report(
            latest_results,
            report_path,
            app.config['PROCESSED_FOLDER']
        )

        return send_file(
            report_path,
            as_attachment=True,
            download_name=report_filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  ☀️  SolarSentinel AI — Fault Detection System")
    print("=" * 60)
    print(f"  Server starting at http://127.0.0.1:5000")
    print(f"  Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"  Processed folder: {app.config['PROCESSED_FOLDER']}")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
