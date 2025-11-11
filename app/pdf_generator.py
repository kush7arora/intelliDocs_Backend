"""
PDF Report Generator for Analysis Results
Creates professional PDF documents for resume and transcript analysis
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
import os

def create_resume_pdf(analysis_data, output_path):
    """
    Generate professional PDF report for resume analysis
    
    Args:
        analysis_data (dict): Resume analysis data
        output_path (str): Path to save PDF
    
    Returns:
        str: Path to generated PDF
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.alignment = TA_JUSTIFY
    
    # Title
    title = Paragraph("Resume Analysis Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Metadata
    analysis = analysis_data.get('analysis', {})
    metadata_text = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    metadata = Paragraph(metadata_text, normal_style)
    elements.append(metadata)
    elements.append(Spacer(1, 20))
    
    # ATS Score Section
    ats_score = analysis.get('ats_score', 0)
    score_heading = Paragraph("ATS Score", heading_style)
    elements.append(score_heading)
    
    score_text = f"<b>Score: {ats_score}/100</b>"
    if ats_score >= 80:
        score_text += " - Excellent! Your resume is well-optimized for ATS systems."
    elif ats_score >= 60:
        score_text += " - Good, but could be improved. Check suggestions below."
    else:
        score_text += " - Needs improvement. Follow the suggestions to increase score."
    
    score_para = Paragraph(score_text, normal_style)
    elements.append(score_para)
    elements.append(Spacer(1, 20))
    
    # Contact Information Section
    contact_heading = Paragraph("Contact Information", heading_style)
    elements.append(contact_heading)
    
    contact_info = analysis.get('contact_info', {})
    contact_data = [
        ['Field', 'Value'],
        ['Email', contact_info.get('email', 'Not found')],
        ['Phone', contact_info.get('phone', 'Not found')],
        ['LinkedIn', contact_info.get('linkedin', 'N/A')],
        ['GitHub', contact_info.get('github', 'N/A')],
    ]
    
    contact_table = Table(contact_data, colWidths=[2*inch, 4*inch])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(contact_table)
    elements.append(Spacer(1, 20))
    
    # Skills Section
    skills_heading = Paragraph("Technical Skills", heading_style)
    elements.append(skills_heading)
    
    skills = analysis.get('skills', {})
    total_skills = skills.get('total_count', 0)
    skills_text = f"<b>Total Skills Found: {total_skills}</b>"
    elements.append(Paragraph(skills_text, normal_style))
    elements.append(Spacer(1, 10))
    
    technical_skills = skills.get('technical', {})
    for category, skill_list in technical_skills.items():
        if skill_list:
            category_text = f"<b>{category.upper()}:</b> {', '.join(skill_list)}"
            elements.append(Paragraph(category_text, normal_style))
            elements.append(Spacer(1, 8))
    
    elements.append(Spacer(1, 20))
    
    # Experience & Stats
    stats_heading = Paragraph("Experience & Statistics", heading_style)
    elements.append(stats_heading)
    
    stats_data = [
        ['Metric', 'Value'],
        ['Years of Experience', str(analysis.get('experience_years', 0))],
        ['Resume Sections', analysis.get('sections_score', 'N/A')],
        ['Word Count', str(analysis.get('word_count', 0))],
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # Improvement Suggestions
    suggestions = analysis.get('suggestions', [])
    if suggestions:
        suggestions_heading = Paragraph("Improvement Suggestions", heading_style)
        elements.append(suggestions_heading)
        
        for idx, suggestion in enumerate(suggestions, 1):
            priority = suggestion.get('priority', 'medium').upper()
            issue = suggestion.get('issue', '')
            suggestion_text = suggestion.get('suggestion', '')
            
            bullet_text = f"<b>{idx}. [{priority}]</b> {issue}<br/><i>{suggestion_text}</i>"
            elements.append(Paragraph(bullet_text, normal_style))
            elements.append(Spacer(1, 10))
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_text = "Generated by IntelliDocs - AI-Powered Resume Analyzer"
    footer = Paragraph(footer_text, ParagraphStyle('Footer', parent=normal_style, alignment=TA_CENTER, textColor=colors.grey))
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    return output_path


def create_transcript_pdf(analysis_data, output_path):
    """
    Generate professional PDF report for transcript analysis
    
    Args:
        analysis_data (dict): Transcript analysis data
        output_path (str): Path to save PDF
    
    Returns:
        str: Path to generated PDF
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.alignment = TA_JUSTIFY
    
    # Title
    title = Paragraph("Meeting Transcript Summary", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Metadata
    analysis = analysis_data.get('analysis', {})
    metadata_text = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    metadata = Paragraph(metadata_text, normal_style)
    elements.append(metadata)
    elements.append(Spacer(1, 20))
    
    # Summary Section
    summary_heading = Paragraph("Summary", heading_style)
    elements.append(summary_heading)
    
    summary_data = analysis.get('summary', {})
    summary_text = summary_data.get('summary', 'No summary available')
    summary_para = Paragraph(summary_text, normal_style)
    elements.append(summary_para)
    
    # Compression info
    if 'original_length' in summary_data:
        compression_text = f"<i>Compressed from {summary_data.get('original_length', 0)} to {summary_data.get('summary_length', 0)} words ({summary_data.get('compression_ratio', 0)}x reduction)</i>"
        compression_para = Paragraph(compression_text, normal_style)
        elements.append(Spacer(1, 10))
        elements.append(compression_para)
    
    elements.append(Spacer(1, 20))
    
    # Action Items Section
    action_items = analysis.get('action_items', [])
    if action_items:
        action_heading = Paragraph("Action Items", heading_style)
        elements.append(action_heading)
        
        for idx, item in enumerate(action_items, 1):
            item_text = f"{idx}. {item}"
            item_para = Paragraph(item_text, normal_style)
            elements.append(item_para)
            elements.append(Spacer(1, 8))
        
        elements.append(Spacer(1, 20))
    
    # Key Decisions Section
    key_decisions = analysis.get('key_decisions', [])
    if key_decisions:
        decisions_heading = Paragraph("Key Decisions", heading_style)
        elements.append(decisions_heading)
        
        for idx, decision in enumerate(key_decisions, 1):
            decision_text = f"{idx}. {decision}"
            decision_para = Paragraph(decision_text, normal_style)
            elements.append(decision_para)
            elements.append(Spacer(1, 8))
        
        elements.append(Spacer(1, 20))
    
    # Improvement Suggestions
    improvements = analysis.get('improvements', {})
    suggestions = improvements.get('suggestions', [])
    
    if suggestions:
        suggestions_heading = Paragraph("Documentation Suggestions", heading_style)
        elements.append(suggestions_heading)
        
        for idx, suggestion in enumerate(suggestions, 1):
            issue = suggestion.get('issue', '')
            suggestion_text = suggestion.get('suggestion', '')
            
            bullet_text = f"<b>{idx}. {issue}</b><br/><i>{suggestion_text}</i>"
            elements.append(Paragraph(bullet_text, normal_style))
            elements.append(Spacer(1, 10))
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_text = "Generated by IntelliDocs - AI-Powered Transcript Summarizer"
    footer = Paragraph(footer_text, ParagraphStyle('Footer', parent=normal_style, alignment=TA_CENTER, textColor=colors.grey))
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    return output_path
