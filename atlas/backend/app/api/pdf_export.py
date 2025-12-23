"""
PDF Export Module

Generates professional PDF memos from analysis results.

Design Decisions:
- Uses ReportLab for reliable PDF generation
- Clean, professional formatting
- All sections from AnalyzeResponse are included
- Proper table formatting for market data and competitors
"""

from typing import Dict, Any
from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib import colors


def generate_pdf_memo(response: AnalyzeResponse, request_data: Dict[str, Any]) -> BytesIO:
    """
    Generate a professional PDF memo from analysis response.
    
    Args:
        response: AnalyzeResponse object with analysis results
        request_data: Original request data (for idea, date, etc.)
        
    Returns:
        BytesIO object containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=18,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        leading=14,
        fontName='Helvetica'
    )
    
    verdict_style = ParagraphStyle(
        'Verdict',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#27ae60') if response.verdict == "GO" 
                else colors.HexColor('#e74c3c') if response.verdict == "NO-GO"
                else colors.HexColor('#f39c12'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Title Section
    elements.append(Paragraph("ATLAS MEMO", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Date and Idea
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    elements.append(Paragraph(f"<b>Date:</b> {date_str}", body_style))
    elements.append(Spacer(1, 0.1*inch))
    
    idea = request_data.get("idea", "Startup Idea")
    elements.append(Paragraph(f"<b>Idea:</b> {idea}", body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Verdict and Confidence
    elements.append(Paragraph("VERDICT", heading_style))
    verdict_text = f"<b>{response.verdict}</b>"
    elements.append(Paragraph(verdict_text, verdict_style))
    elements.append(Spacer(1, 0.1*inch))
    
    confidence_text = f"Confidence Score: <b>{response.confidence_score}/100</b>"
    elements.append(Paragraph(confidence_text, body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    elements.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    for bullet in response.executive_summary:
        elements.append(Paragraph(f"• {bullet}", body_style))
        elements.append(Spacer(1, 0.05*inch))
    elements.append(Spacer(1, 0.2*inch))
    
    # Market Analysis - TAM/SAM/SOM Table
    elements.append(Paragraph("MARKET ANALYSIS", heading_style))
    
    # Base case table
    market_data = [
        ['Metric', 'Min (USD)', 'Base (USD)', 'Max (USD)'],
        [
            'TAM',
            f"${response.market.tam.min:,.0f}",
            f"${response.market.tam.base:,.0f}",
            f"${response.market.tam.max:,.0f}"
        ],
        [
            'SAM',
            f"${response.market.sam.min:,.0f}",
            f"${response.market.sam.base:,.0f}",
            f"${response.market.sam.max:,.0f}"
        ],
        [
            'SOM',
            f"${response.market.som.min:,.0f}",
            f"${response.market.som.base:,.0f}",
            f"${response.market.som.max:,.0f}"
        ]
    ]
    
    market_table = Table(market_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    market_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    elements.append(market_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Scenarios Table
    elements.append(Paragraph("SCENARIOS", subheading_style))
    
    scenarios_data = [
        ['Scenario', 'TAM (USD)', 'SAM (USD)', 'SOM (USD)']
    ]
    
    for scenario_key in ['bear', 'base', 'bull']:
        if scenario_key in response.scenarios:
            scenario = response.scenarios[scenario_key]
            scenarios_data.append([
                scenario.name,
                f"${scenario.market.tam.base:,.0f}",
                f"${scenario.market.sam.base:,.0f}",
                f"${scenario.market.som.base:,.0f}"
            ])
    
    scenarios_table = Table(scenarios_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    scenarios_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    elements.append(scenarios_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Competitors Table
    if response.competitors:
        elements.append(Paragraph("COMPETITORS", heading_style))
        
        competitors_data = [
            ['Name', 'Positioning', 'Pricing', 'Geography', 'Differentiator']
        ]
        
        for comp in response.competitors[:10]:  # Limit to 10 for readability
            competitors_data.append([
                comp.name[:30] if len(comp.name) > 30 else comp.name,
                comp.positioning[:40] if len(comp.positioning) > 40 else comp.positioning,
                comp.pricing[:30] if len(comp.pricing) > 30 else comp.pricing,
                comp.geography[:20] if len(comp.geography) > 20 else comp.geography,
                comp.differentiator[:40] if len(comp.differentiator) > 40 else comp.differentiator
            ])
        
        competitors_table = Table(
            competitors_data,
            colWidths=[1.2*inch, 1.5*inch, 1*inch, 1*inch, 1.5*inch]
        )
        competitors_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(competitors_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Risks
    elements.append(Paragraph("RISKS", heading_style))
    
    if response.risks.market:
        elements.append(Paragraph("<b>Market Risks:</b>", subheading_style))
        for risk in response.risks.market:
            elements.append(Paragraph(f"• {risk}", body_style))
            elements.append(Spacer(1, 0.05*inch))
    
    if response.risks.competition:
        elements.append(Paragraph("<b>Competition Risks:</b>", subheading_style))
        for risk in response.risks.competition:
            elements.append(Paragraph(f"• {risk}", body_style))
            elements.append(Spacer(1, 0.05*inch))
    
    if response.risks.regulatory:
        elements.append(Paragraph("<b>Regulatory Risks:</b>", subheading_style))
        for risk in response.risks.regulatory:
            elements.append(Paragraph(f"• {risk}", body_style))
            elements.append(Spacer(1, 0.05*inch))
    
    if response.risks.distribution:
        elements.append(Paragraph("<b>Distribution Risks:</b>", subheading_style))
        for risk in response.risks.distribution:
            elements.append(Paragraph(f"• {risk}", body_style))
            elements.append(Spacer(1, 0.05*inch))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Next 7 Days Tests
    if response.next_7_days_tests:
        elements.append(Paragraph("NEXT 7 DAYS TESTS", heading_style))
        for i, test in enumerate(response.next_7_days_tests, 1):
            elements.append(Paragraph(f"<b>Test {i}:</b> {test.test}", body_style))
            elements.append(Paragraph(f"<i>Method:</i> {test.method}", body_style))
            elements.append(Paragraph(f"<i>Success Threshold:</i> {test.success_threshold}", body_style))
            elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Sources
    elements.append(Paragraph("SOURCES", heading_style))
    for i, source in enumerate(response.sources, 1):
        # Truncate long URLs for better formatting
        url_display = source.url
        if len(url_display) > 80:
            url_display = url_display[:77] + "..."
        source_text = f"<b>{i}. {source.title}</b><br/>{url_display}"
        elements.append(Paragraph(source_text, body_style))
        elements.append(Spacer(1, 0.1*inch))
    
    # Add assumptions section if present
    if response.assumptions:
        elements.append(PageBreak())
        elements.append(Paragraph("ASSUMPTIONS", heading_style))
        for assumption in response.assumptions:
            elements.append(Paragraph(f"• {assumption}", body_style))
            elements.append(Spacer(1, 0.05*inch))
    
    # Add disconfirming evidence if present
    if response.disconfirming_evidence:
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("DISCONFIRMING EVIDENCE", heading_style))
        for evidence in response.disconfirming_evidence:
            elements.append(Paragraph(f"• {evidence}", body_style))
            elements.append(Spacer(1, 0.05*inch))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

