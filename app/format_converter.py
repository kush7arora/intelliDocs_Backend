"""
Format Converter - Convert between PDF, DOCX, and TXT formats
"""

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import PyPDF2
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER

def pdf_to_text(pdf_path):
    """
    Convert PDF to plain text
    
    Args:
        pdf_path (str): Path to PDF file
    
    Returns:
        str: Extracted text
    """
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Failed to convert PDF to text: {str(e)}")


def pdf_to_docx(pdf_path, output_path):
    """
    Convert PDF to DOCX
    
    Args:
        pdf_path (str): Path to PDF file
        output_path (str): Path to save DOCX
    
    Returns:
        str: Path to output file
    """
    try:
        # Extract text from PDF
        text = pdf_to_text(pdf_path)
        
        # Create DOCX
        doc = Document()
        doc.add_heading('Converted Document', 0)
        doc.add_paragraph(f"Converted from PDF on {datetime.now().strftime('%B %d, %Y')}")
        doc.add_paragraph(text)
        
        doc.save(output_path)
        return output_path
    except Exception as e:
        raise Exception(f"Failed to convert PDF to DOCX: {str(e)}")


def text_to_docx(text_content, output_path, title="Document"):
    """
    Convert plain text to DOCX
    
    Args:
        text_content (str): Text content
        output_path (str): Path to save DOCX
        title (str): Document title
    
    Returns:
        str: Path to output file
    """
    try:
        doc = Document()
        doc.add_heading(title, 0)
        doc.add_paragraph(f"Created on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        doc.add_paragraph(text_content)
        
        doc.save(output_path)
        return output_path
    except Exception as e:
        raise Exception(f"Failed to convert text to DOCX: {str(e)}")


def docx_to_text(docx_path):
    """
    Convert DOCX to plain text
    
    Args:
        docx_path (str): Path to DOCX file
    
    Returns:
        str: Extracted text
    """
    try:
        doc = Document(docx_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to convert DOCX to text: {str(e)}")


def text_to_pdf(text_content, output_path, title="Document"):
    """
    Convert plain text to PDF (simple version)
    
    Args:
        text_content (str): Text content
        output_path (str): Path to save PDF
        title (str): Document title
    
    Returns:
        str: Path to output file
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from xml.sax.saxutils import escape  # ✅ Add this import
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
        )
        elements.append(Paragraph(escape(title), title_style))  # ✅ Escape title
        elements.append(Spacer(1, 0.5))
        
        # Add content - escape each line to prevent XML parsing errors
        normal_style = styles['Normal']
        line_count = 0
        for paragraph in text_content.split('\n'):
            if paragraph.strip():
                # ✅ Escape the paragraph text to handle special characters and XML
                escaped_text = escape(paragraph.strip())
                elements.append(Paragraph(escaped_text, normal_style))
                elements.append(Spacer(1, 0.1))
                line_count += 1
                
                # Add page break every 50 lines (for long documents)
                if line_count % 50 == 0:
                    elements.append(PageBreak())
        
        doc.build(elements)
        return output_path
    except Exception as e:
        raise Exception(f"Failed to convert text to PDF: {str(e)}")


def convert_format(input_path, output_path, from_format, to_format, title="Document"):
    """
    Convert between formats
    
    Args:
        input_path (str): Path to input file
        output_path (str): Path to save output
        from_format (str): Source format ('pdf', 'docx', 'txt')
        to_format (str): Target format ('pdf', 'docx', 'txt')
        title (str): Document title for output
    
    Returns:
        str: Path to output file
    """
    from_format = from_format.lower()
    to_format = to_format.lower()
    
    # Same format - just copy
    if from_format == to_format:
        raise Exception("Source and target formats are the same")
    
    # PDF conversions
    if from_format == 'pdf':
        if to_format == 'txt':
            text = pdf_to_text(input_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return output_path
        elif to_format == 'docx':
            return pdf_to_docx(input_path, output_path)
    
    # DOCX conversions
    elif from_format == 'docx':
        if to_format == 'txt':
            text = docx_to_text(input_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return output_path
        elif to_format == 'pdf':
            text = docx_to_text(input_path)
            return text_to_pdf(text, output_path, title)
    
    # TXT conversions
    elif from_format == 'txt':
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if to_format == 'docx':
            return text_to_docx(text, output_path, title)
        elif to_format == 'pdf':
            return text_to_pdf(text, output_path, title)
    
    raise Exception(f"Unsupported format conversion: {from_format} to {to_format}")
