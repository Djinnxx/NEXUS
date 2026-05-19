"""
Generates professional PDF pentest/OSINT reports using reportlab.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# Colour palette
C_BG      = colors.HexColor("#1a1a2e")
C_PANEL   = colors.HexColor("#16213e")
C_ACCENT  = colors.HexColor("#e94560")
C_BLUE    = colors.HexColor("#0f3460")
C_LIGHT   = colors.HexColor("#eaeaea")
C_MUTED   = colors.HexColor("#a0a0b0")
C_GREEN   = colors.HexColor("#00b894")
C_YELLOW  = colors.HexColor("#fdcb6e")
C_RED     = colors.HexColor("#e17055")
C_WHITE   = colors.white
C_BLACK   = colors.black


def _risk_color(score: int):
    if score >= 75: return C_ACCENT
    if score >= 50: return C_RED
    if score >= 25: return C_YELLOW
    return C_GREEN


def _risk_label(score: int) -> str:
    if score >= 75: return "CRITICAL"
    if score >= 50: return "HIGH"
    if score >= 25: return "MEDIUM"
    return "LOW"


def generate_report(target: str, all_results: dict, output_path: str = None) -> str:
    """
    Generate a PDF report.
    Returns the output file path.
    """
    if not output_path:
        safe = target.replace(".", "_").replace("/", "_").replace(":", "_")
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(os.path.expanduser("~"), f"NEXUS_REPORT_{safe}_{ts}.pdf")

    doc    = SimpleDocTemplate(output_path, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ------------------------------------------------------------------ styles
    title_style = ParagraphStyle("NexusTitle",
        parent=styles["Heading1"], fontSize=24, textColor=C_ACCENT,
        spaceAfter=4, alignment=TA_LEFT)
    h2_style = ParagraphStyle("NexusH2",
        parent=styles["Heading2"], fontSize=14, textColor=C_LIGHT,
        spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("NexusBody",
        parent=styles["Normal"], fontSize=10, textColor=C_MUTED,
        spaceAfter=4, leading=14)
    mono_style = ParagraphStyle("NexusMono",
        parent=styles["Code"], fontSize=9, textColor=C_GREEN,
        backColor=C_PANEL, spaceAfter=2, leading=12)
    warn_style = ParagraphStyle("NexusWarn",
        parent=styles["Normal"], fontSize=10, textColor=C_RED, spaceAfter=4)

    # ------------------------------------------------------------------ cover
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("NEXUS OSINT", title_style))
    story.append(Paragraph("Intelligence Report", ParagraphStyle("sub",
        fontSize=16, textColor=C_BLUE, spaceAfter=2)))
    story.append(HRFlowable(width="100%", thickness=2, color=C_ACCENT, spaceAfter=8))

    # Target info table
    overall_risk = max((v.get("risk_score", 0) for v in all_results.values()), default=0)
    meta_data = [
        ["Target",    target],
        ["Date",      datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Modules",   str(len(all_results))],
        ["Risk Score", f"{overall_risk}/100 – {_risk_label(overall_risk)}"],
    ]
    meta_table = Table(meta_data, colWidths=[4*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), C_BLUE),
        ("TEXTCOLOR",   (0, 0), (0, -1), C_WHITE),
        ("TEXTCOLOR",   (1, 0), (1, -1), C_LIGHT),
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_PANEL, C_BG]),
        ("GRID",        (0, 0), (-1, -1), 0.5, C_BLUE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",(0, 0), (-1, -1), 8),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5*cm))

    # ------------------------------------------------------------------ modules
    story.append(Paragraph("Module Findings", h2_style))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BLUE, spaceAfter=8))

    module_labels = {
        "ip":        "IP Lookup",
        "whois":     "WHOIS",
        "dns":       "DNS Enumeration",
        "cert":      "Certificate Transparency",
        "wayback":   "Wayback Machine",
        "breach":    "Email Breach Check",
        "username":  "Username Search",
        "shodan":    "Shodan",
        "virustotal":"VirusTotal",
        "github":    "GitHub Dorking",
        "exif":      "EXIF / Metadata",
        "darkweb":   "Dark Web",
        "paste":     "Paste Monitor",
        "ioc":       "IOC Check",
    }

    for key, label in module_labels.items():
        res = all_results.get(key)
        if not res:
            continue

        story.append(Paragraph(f"► {label}", h2_style))
        status     = res.get("status", "N/A")
        risk_score = res.get("risk_score", 0)
        story.append(Paragraph(
            f"Status: {status}  |  Risk Score: {risk_score}/100 – {_risk_label(risk_score)}",
            warn_style if risk_score >= 50 else body_style
        ))

        findings = res.get("findings", [])
        if findings:
            for f in findings[:25]:
                story.append(Paragraph(f"• {f}", mono_style))
        else:
            story.append(Paragraph("No findings.", body_style))

        story.append(Spacer(1, 0.3*cm))

    # ------------------------------------------------------------------ recommendations
    story.append(PageBreak())
    story.append(Paragraph("Recommendations", h2_style))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACCENT, spaceAfter=8))

    recs = [
        "Rotate any credentials found in GitHub / paste sites immediately.",
        "Review SPF, DKIM, and DMARC records to prevent email spoofing.",
        "Investigate all open ports and exposed services found via Shodan.",
        "Remove or restrict EXIF data from publicly shared images.",
        "Monitor breach databases regularly for newly exposed credentials.",
        "Review and clean dark web mentions with affected service providers.",
        "Implement certificate pinning where applicable.",
        "Enable HSTS and review SSL certificate expiry dates.",
    ]
    for rec in recs:
        story.append(Paragraph(f"➤  {rec}", body_style))

    # ------------------------------------------------------------------ footer
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BLUE, spaceAfter=4))
    story.append(Paragraph(
        "Generated by NEXUS OSINT v1.0 – For authorized use only.",
        ParagraphStyle("footer", fontSize=8, textColor=C_MUTED, alignment=TA_CENTER)
    ))

    doc.build(story)
    return output_path
