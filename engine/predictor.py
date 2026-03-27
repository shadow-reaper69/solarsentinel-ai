"""
Prediction Engine for Solar Panel Fault Detection.
Generates human-readable insights and risk assessments based on detected faults.
"""


FAULT_INSIGHTS = {
    'Hotspot': {
        'High': {
            'prediction': 'Critical overheating detected — immediate inspection required',
            'risk': 'Panel may suffer permanent cell damage if not addressed within 48 hours',
            'action': 'Shut down affected panel and schedule emergency maintenance',
            'efficiency_loss': '25-40%',
            'icon': '🔴'
        },
        'Medium': {
            'prediction': 'Moderate hotspot activity — potential cell degradation',
            'risk': 'Continued operation may lead to accelerated panel aging',
            'action': 'Schedule inspection within 1 week',
            'efficiency_loss': '10-20%',
            'icon': '🟠'
        },
        'Low': {
            'prediction': 'Minor thermal anomaly detected — monitor regularly',
            'risk': 'Low risk, but may indicate developing cell issues',
            'action': 'Include in next routine maintenance check',
            'efficiency_loss': '2-8%',
            'icon': '🔵'
        },
    },
    'Overheating': {
        'High': {
            'prediction': 'Severe overheating across panel region — failure imminent',
            'risk': 'High probability of panel failure within 30 days',
            'action': 'Immediate shutdown and replacement recommended',
            'efficiency_loss': '35-50%',
            'icon': '🔴'
        },
        'Medium': {
            'prediction': 'Elevated temperature in panel section — degradation likely',
            'risk': 'Panel lifespan may be reduced by 2-5 years',
            'action': 'Improve ventilation and schedule cooling system check',
            'efficiency_loss': '15-25%',
            'icon': '🟠'
        },
        'Low': {
            'prediction': 'Slight overheating observed — within acceptable range',
            'risk': 'Minimal impact under current conditions',
            'action': 'Monitor during peak temperature days',
            'efficiency_loss': '3-10%',
            'icon': '🔵'
        },
    },
    'Crack': {
        'High': {
            'prediction': 'Major structural crack detected — panel integrity compromised',
            'risk': 'Panel may fail completely, potential electrical hazard',
            'action': 'Replace panel immediately — do not operate',
            'efficiency_loss': '30-60%',
            'icon': '🔴'
        },
        'Medium': {
            'prediction': 'Visible crack pattern detected — structural weakness',
            'risk': 'Crack may propagate under thermal stress',
            'action': 'Schedule panel replacement within 2 weeks',
            'efficiency_loss': '15-30%',
            'icon': '🟠'
        },
        'Low': {
            'prediction': 'Micro-crack detected — early-stage structural issue',
            'risk': 'May worsen over time but currently operational',
            'action': 'Document and monitor in subsequent inspections',
            'efficiency_loss': '5-12%',
            'icon': '🔵'
        },
    },
    'Dust': {
        'High': {
            'prediction': 'Heavy soiling/dust accumulation — cleaning required urgently',
            'risk': 'Significant energy output reduction',
            'action': 'Clean panels immediately using approved methods',
            'efficiency_loss': '20-35%',
            'icon': '🔴'
        },
        'Medium': {
            'prediction': 'Moderate dust buildup detected — cleaning recommended',
            'risk': 'Gradual decrease in energy output',
            'action': 'Schedule cleaning within 1 week',
            'efficiency_loss': '10-20%',
            'icon': '🟠'
        },
        'Low': {
            'prediction': 'Light dust present — minor impact on performance',
            'risk': 'Minimal effect, normal accumulation',
            'action': 'Include in next scheduled cleaning cycle',
            'efficiency_loss': '2-8%',
            'icon': '🔵'
        },
    },
    'Shadow': {
        'High': {
            'prediction': 'Significant shading detected — major output blockage',
            'risk': 'Persistent shading causes hot spots and bypass diode stress',
            'action': 'Remove obstruction or re-position panels',
            'efficiency_loss': '25-45%',
            'icon': '🔴'
        },
        'Medium': {
            'prediction': 'Partial shading observed — output reduction likely',
            'risk': 'May cause uneven cell loading and accelerated wear',
            'action': 'Evaluate surrounding obstructions and trim vegetation',
            'efficiency_loss': '10-20%',
            'icon': '🟠'
        },
        'Low': {
            'prediction': 'Minor shadow detected — likely time-of-day dependent',
            'risk': 'Temporary and seasonal, minimal long-term impact',
            'action': 'No immediate action required — log for reference',
            'efficiency_loss': '3-8%',
            'icon': '🔵'
        },
    },
}


def generate_predictions(faults):
    """
    Generate predictions and insights for a list of detected faults.
    Returns a list of prediction objects.
    """
    predictions = []

    for fault in faults:
        fault_type = fault.get('type', 'Unknown')
        severity = fault.get('severity', 'Low')

        insight = FAULT_INSIGHTS.get(fault_type, {}).get(severity, {
            'prediction': f'{fault_type} detected — further analysis needed',
            'risk': 'Unable to assess risk level',
            'action': 'Manual inspection recommended',
            'efficiency_loss': 'Unknown',
            'icon': '⚪'
        })

        predictions.append({
            'fault_id': fault.get('id', 'N/A'),
            'fault_type': fault_type,
            'severity': severity,
            'prediction': insight['prediction'],
            'risk': insight['risk'],
            'recommended_action': insight['action'],
            'estimated_efficiency_loss': insight['efficiency_loss'],
            'icon': insight['icon'],
            'problem': _get_problem_statement(fault_type, severity),
        })

    return predictions


def _get_problem_statement(fault_type, severity):
    """Generate a clear problem statement for each fault."""
    problems = {
        'Hotspot': {
            'High': 'Localized excessive heat generation in solar cells, indicating potential PID (Potential Induced Degradation) or cell bypass failure.',
            'Medium': 'Moderate thermal irregularity suggesting early-stage cell degradation or poor solder joint.',
            'Low': 'Minor temperature variation detected, possibly due to manufacturing variance or ambient conditions.',
        },
        'Overheating': {
            'High': 'Widespread thermal stress across panel section, indicating systemic cooling failure or electrical mismatch.',
            'Medium': 'Elevated operating temperature in panel region, suggesting inadequate ventilation or partial electrical fault.',
            'Low': 'Slight temperature elevation within operational limits, possibly due to high ambient temperature.',
        },
        'Crack': {
            'High': 'Visible structural fracture compromising cell integrity, causing electrical isolation of cell segments.',
            'Medium': 'Detectable crack pattern indicating mechanical stress damage, possibly from transport, installation, or thermal cycling.',
            'Low': 'Micro-crack detected at cell level, potentially caused by thermal expansion/contraction cycles.',
        },
        'Dust': {
            'High': 'Heavy particulate accumulation blocking significant light absorption area, drastically reducing photovoltaic conversion.',
            'Medium': 'Moderate soiling layer reducing light transmission to solar cells.',
            'Low': 'Light surface contamination with minimal impact on energy conversion.',
        },
        'Shadow': {
            'High': 'Large shadow coverage causing significant mismatch in cell string output, risking bypass diode overload.',
            'Medium': 'Partial obstruction creating uneven illumination across panel surface.',
            'Low': 'Minor transient shading, likely from time-of-day sun angle or small obstruction.',
        },
    }

    return problems.get(fault_type, {}).get(severity,
        f'{fault_type} detected at {severity.lower()} severity level. Manual inspection recommended.')


def calculate_health_score(all_faults):
    """
    Calculate overall panel health score (0-100) based on detected faults.
    """
    if not all_faults:
        return 100

    severity_weights = {'High': 20, 'Medium': 10, 'Low': 3}
    total_penalty = sum(severity_weights.get(f.get('severity', 'Low'), 3) for f in all_faults)

    score = max(0, 100 - total_penalty)
    return score


def get_risk_level(health_score):
    """Determine risk level from health score."""
    if health_score >= 85:
        return {'level': 'Low', 'color': '#38A169', 'label': 'Healthy'}
    elif health_score >= 60:
        return {'level': 'Medium', 'color': '#ED8936', 'label': 'At Risk'}
    elif health_score >= 30:
        return {'level': 'High', 'color': '#E53E3E', 'label': 'Critical'}
    else:
        return {'level': 'Critical', 'color': '#9B2C2C', 'label': 'Failure Imminent'}
