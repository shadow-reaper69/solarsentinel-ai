"""
PDF Report Generator for Solar Panel Fault Detection.
Creates professional multi-page PDF reports using ReportLab.
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def _get_styles():
    """Create custom styles for the PDF report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1A202C'),
        spaceAfter=6,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#718096'),
        spaceAfter=20,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2D3748'),
        spaceBefore=16,
        spaceAfter=8,
        borderWidth=0,
        borderPadding=0,
    ))

    styles.add(ParagraphStyle(
        name='SubSection',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#4A5568'),
        spaceBefore=12,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name='BodyText2',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name='FaultHigh',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#E53E3E'),
    ))

    styles.add(ParagraphStyle(
        name='FaultMedium',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#ED8936'),
    ))

    styles.add(ParagraphStyle(
        name='FaultLow',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#3182CE'),
    ))

    return styles


def _severity_color(severity):
    """Get reportlab Color for a severity level."""
    mapping = {
        'High': colors.HexColor('#FED7D7'),
        'Medium': colors.HexColor('#FEFCBF'),
        'Low': colors.HexColor('#BEE3F8'),
    }
    return mapping.get(severity, colors.white)


def _severity_text_color(severity):
    mapping = {
        'High': colors.HexColor('#C53030'),
        'Medium': colors.HexColor('#C05621'),
        'Low': colors.HexColor('#2B6CB0'),
    }
    return mapping.get(severity, colors.black)


def generate_pdf_report(results, output_path, processed_dir):
    """
    Generate a full PDF report from analysis results.

    Args:
        results: list of per-image result dicts from the analyzer
        output_path: path to save the PDF file
        processed_dir: directory containing processed/marked images
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=40,
    )

    styles = _get_styles()
    elements = []

    # ── Title Page ──
    elements.append(Spacer(1, 80))
    elements.append(Paragraph("☀️ Solar Panel Fault Detection Report", styles['ReportTitle']))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}",
        styles['ReportSubtitle']
    ))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor('#E2E8F0')))
    elements.append(Spacer(1, 20))

    # ── Summary Section ──
    total_images = len(results)
    all_faults = []
    for r in results:
        all_faults.extend(r.get('faults', []))

    total_faults = len(all_faults)
    hotspot_count = sum(1 for f in all_faults if f['type'] == 'Hotspot')
    overheating_count = sum(1 for f in all_faults if f['type'] == 'Overheating')
    crack_count = sum(1 for f in all_faults if f['type'] == 'Crack')
    dust_count = sum(1 for f in all_faults if f['type'] == 'Dust')
    shadow_count = sum(1 for f in all_faults if f['type'] == 'Shadow')
    high_count = sum(1 for f in all_faults if f['severity'] == 'High')
    medium_count = sum(1 for f in all_faults if f['severity'] == 'Medium')
    low_count = sum(1 for f in all_faults if f['severity'] == 'Low')

    elements.append(Paragraph("Executive Summary", styles['SectionTitle']))

    summary_data = [
        ['Metric', 'Value'],
        ['Total Images Analyzed', str(total_images)],
        ['Total Faults Detected', str(total_faults)],
        ['Hotspots', str(hotspot_count)],
        ['Overheating Regions', str(overheating_count)],
        ['Cracks', str(crack_count)],
        ['Dust/Soiling', str(dust_count)],
        ['Shadows', str(shadow_count)],
        ['High Severity', str(high_count)],
        ['Medium Severity', str(medium_count)],
        ['Low Severity', str(low_count)],
    ]

    summary_table = Table(summary_data, colWidths=[250, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F7FAFC'), colors.white]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # ── Fault Details Table ──
    elements.append(Paragraph("Fault Details", styles['SectionTitle']))

    if all_faults:
        fault_table_data = [['Fault ID', 'Image', 'Type', 'Severity', 'Coordinates']]

        for r in results:
            for fault in r.get('faults', []):
                sev = fault['severity']
                fault_table_data.append([
                    fault['id'],
                    r.get('filename', 'N/A'),
                    fault['type'],
                    sev,
                    fault.get('coordinates', 'N/A'),
                ])

        fault_table = Table(fault_table_data, colWidths=[65, 130, 85, 75, 100])

        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]

        # Color-code severity rows
        for i, row in enumerate(fault_table_data[1:], start=1):
            sev = row[3]
            style_commands.append(('BACKGROUND', (3, i), (3, i), _severity_color(sev)))
            style_commands.append(('TEXTCOLOR', (3, i), (3, i), _severity_text_color(sev)))

        fault_table.setStyle(TableStyle(style_commands))
        elements.append(fault_table)
    else:
        elements.append(Paragraph("No faults detected in any analyzed images.", styles['BodyText2']))

    elements.append(PageBreak())

    # ── Per-Image Reports ──
    for idx, r in enumerate(results):
        elements.append(Paragraph(
            f"Image {idx + 1}: {r.get('filename', 'Unknown')}",
            styles['SectionTitle']
        ))

        # Metadata
        meta = r.get('metadata', {})
        elements.append(Paragraph("Metadata", styles['SubSection']))
        meta_items = [
            f"<b>File:</b> {meta.get('filename', 'N/A')}",
            f"<b>Date Taken:</b> {meta.get('date_taken', 'Not available')}",
            f"<b>GPS Latitude:</b> {meta.get('gps_latitude', 'Not available')}",
            f"<b>GPS Longitude:</b> {meta.get('gps_longitude', 'Not available')}",
            f"<b>Altitude:</b> {meta.get('altitude', 'Not available')}",
            f"<b>Image Type:</b> {r.get('image_type', 'N/A')}",
        ]
        for item in meta_items:
            elements.append(Paragraph(item, styles['BodyText2']))
        elements.append(Spacer(1, 10))

        # Marked image
        marked_path = os.path.join(processed_dir, r.get('marked_image', ''))
        if os.path.exists(marked_path):
            elements.append(Paragraph("Detected Faults (Marked Image)", styles['SubSection']))
            try:
                img = RLImage(marked_path, width=420, height=300)
                img.hAlign = 'CENTER'
                elements.append(img)
            except Exception:
                elements.append(Paragraph("[Image could not be embedded]", styles['BodyText2']))
            elements.append(Spacer(1, 10))

        # Fault list
        faults = r.get('faults', [])
        if faults:
            elements.append(Paragraph("Detected Faults", styles['SubSection']))
            for fault in faults:
                sev = fault['severity']
                style_name = f'Fault{sev}' if f'Fault{sev}' in [s.name for s in styles.byName.values()] else 'BodyText2'
                elements.append(Paragraph(
                    f"<b>{fault['id']}</b> — {fault['type']} | Severity: <b>{sev}</b> | "
                    f"Coords: {fault.get('coordinates', 'N/A')}",
                    styles.get(style_name, styles['BodyText2'])
                ))

            elements.append(Spacer(1, 8))

            # Zoomed faults
            elements.append(Paragraph("Zoomed Fault Views", styles['SubSection']))
            for fault in faults:
                zoom_file = fault.get('zoom_image')
                if zoom_file:
                    zoom_path = os.path.join(processed_dir, zoom_file)
                    if os.path.exists(zoom_path):
                        elements.append(Paragraph(
                            f"{fault['id']} — {fault['type']} ({fault['severity']})",
                            styles['BodyText2']
                        ))
                        try:
                            zoom_img = RLImage(zoom_path, width=180, height=140)
                            zoom_img.hAlign = 'LEFT'
                            elements.append(zoom_img)
                        except Exception:
                            pass
                        elements.append(Spacer(1, 6))

        # Predictions
        predictions = r.get('predictions', [])
        if predictions:
            elements.append(Paragraph("Predictions & Insights", styles['SubSection']))
            for pred in predictions:
                elements.append(Paragraph(
                    f"<b>{pred.get('icon', '•')} {pred['fault_id']}:</b> {pred['prediction']}",
                    styles['BodyText2']
                ))
                elements.append(Paragraph(
                    f"&nbsp;&nbsp;&nbsp;Problem: {pred.get('problem', 'N/A')}",
                    styles['BodyText2']
                ))
                elements.append(Paragraph(
                    f"&nbsp;&nbsp;&nbsp;Action: {pred.get('recommended_action', 'N/A')} | "
                    f"Est. Efficiency Loss: {pred.get('estimated_efficiency_loss', 'N/A')}",
                    styles['BodyText2']
                ))
                elements.append(Spacer(1, 4))

        if idx < len(results) - 1:
            elements.append(PageBreak())

    # ── Footer ──
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0')))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Report generated by SolarSentinel AI — Solar Panel Fault Detection System",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#A0AEC0'), alignment=TA_CENTER)
    ))

    # Build PDF
    doc.build(elements)
    return output_path
