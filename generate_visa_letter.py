#!/usr/bin/env python3
"""
Visa Letter Generator

A standalone tool to generate visa letters from YAML input files.
"""

import yaml
import sys
from pathlib import Path
from datetime import datetime
from jinja2 import Template
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage


def load_yaml_data(yaml_file):
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        try:
            with open('pgeu.yaml', 'r', encoding='utf-8') as f:
                pgeu_config = yaml.safe_load(f)
                data.update(pgeu_config)
        except FileNotFoundError:
            print("Error: pgeu.yaml configuration file not found.")
            sys.exit(1)
        
        required_fields = [
            'full_name_passport', 'date_of_birth', 'passport_number', 'nationality',
            'address', 'embassy_name', 'embassy_address', 
            'stay_at', 'contact', 'entry_date', 'exit_date', 'gender'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        data.setdefault('is_speaker', False)
        data.setdefault('pgeu_accomodations', False)
        
        return data
    except FileNotFoundError:
        print(f"Error: YAML file '{yaml_file}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def create_visa_letter_pdf(data, output_file, signature_file=None):
    """Generate the visa letter PDF using ReportLab."""
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    def style(alignment=TA_LEFT, font_size=10, space_after=5):
        return ParagraphStyle('Custom', parent=styles['Normal'], 
                            fontSize=font_size, spaceAfter=space_after, 
                            alignment=alignment, textColor=colors.black, leading=11)
    
    # Build the document content
    story = []

    # Create header with logo and address using a table
    from reportlab.platypus import Table, TableStyle
    
    if Path("pgeu.jpg").exists():
        try:
            with PILImage.open("pgeu.jpg") as img:
                orig_width, orig_height = img.size
                aspect_ratio = orig_width / orig_height
                target_height = 1*inch
                target_width = target_height * aspect_ratio
            logo_element = Image("pgeu.jpg", width=target_width, height=target_height)
        except Exception as e:
            print(f"Warning: Could not load pgeu.jpg: {e}")
            logo_element = Paragraph("<b>PostgreSQL Europe Logo</b>", styles['Normal'])
    else:
        logo_element = Paragraph("<b>PostgreSQL Europe Logo</b>", styles['Normal'])
    
    pgeu_address = """
    <b>PostgreSQL Europe</b><br/>
    61, rue de Lyon<br/>
    75012 PARIS<br/>
    FRANCE<br/>
    Website: https://www.postgresql.eu/<br/>
    Email: board@postgresql.eu
    """
    address_element = Paragraph(pgeu_address, style(TA_LEFT))
    
    page_width = A4[0] - 144
    address_text_width = 2.3*inch
    logo_column_width = page_width - address_text_width
    address_column_width = address_text_width
    
    header_data = [[logo_element, address_element]]
    header_table = Table(header_data, colWidths=[logo_column_width, address_column_width])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 20))

    data['embassy_address']=data['embassy_address'].replace('\n', '<br/>')
    embassy_info = f"""
    {data['embassy_name']}<br/>
    {data['embassy_address']}
    """
    today = datetime.now().strftime("%B %d, %Y")
    
    embassy_para = Paragraph(embassy_info, style(TA_LEFT))
    date_para = Paragraph(today, style(TA_RIGHT))
    
    embassy_date_data = [[embassy_para, date_para]]
    embassy_date_table = Table(embassy_date_data, colWidths=[3*inch, 3*inch])
    embassy_date_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(embassy_date_table)
    story.append(Spacer(1, 20))

    
    try:
        # Handle dates that might be strings or date objects
        for date_field in ['entry_date', 'exit_date', 'date_of_birth']:
            if isinstance(data[date_field], str):
                data[date_field] = datetime.strptime(data[date_field], '%Y-%m-%d').strftime('%d/%m/%Y')
            else:
                # Already a date object, just format it
                data[date_field] = data[date_field].strftime('%d/%m/%Y')
    except (ValueError, AttributeError) as e:
        print(f"Error: Invalid date format. Please use YYYY-MM-DD for date fields. Details: {e}")
        sys.exit(1)

    try:
        with open('letter_template.j2', 'r', encoding='utf-8') as f:
            template_str = f.read()
        letter_template = Template(template_str)
    except FileNotFoundError:
        print("Error: letter_template.j2 not found.")
        sys.exit(1)

    if 'signer' in data and 'contact_info' in data['signer']:
        data['signer']['contact_info'] = data['signer']['contact_info'].replace('\n', '<br/>')
    
    letter_content = letter_template.render(**data)
    
    paragraphs = letter_content.strip().split('\n\n')
    for para in paragraphs:
        if para.strip():
            if '[SIGNATURE_PLACEHOLDER]' in para:
                if signature_file and Path(signature_file).exists():
                    try:
                        text_before = para.split('[SIGNATURE_PLACEHOLDER]')[0].strip()
                        text_after = para.split('[SIGNATURE_PLACEHOLDER]')[1].strip()
                        
                        if text_before:
                            story.append(Paragraph(text_before, style()))
                            story.append(Spacer(1, 6))
                        
                        with PILImage.open(signature_file) as img:
                            orig_width, orig_height = img.size
                            aspect_ratio = orig_width / orig_height
                            target_height = 0.5625*inch
                            target_width = target_height * aspect_ratio
                        signature = Image(signature_file, width=target_width, height=target_height)
                        signature.hAlign = 'LEFT'
                        story.append(signature)
                        story.append(Spacer(1, 6))
                        
                        if text_after:
                            story.append(Paragraph(text_after, style()))
                            story.append(Spacer(1, 6))
                    except Exception as e:
                        print(f"Warning: Could not add signature image: {e}")
                        clean_para = para.replace('[SIGNATURE_PLACEHOLDER]', '')
                        if clean_para.strip():
                            story.append(Paragraph(clean_para.strip(), style()))
                            story.append(Spacer(1, 6))
                else:
                    clean_para = para.replace('[SIGNATURE_PLACEHOLDER]', '')
                    if clean_para.strip():
                        story.append(Paragraph(clean_para.strip(), style()))
                        story.append(Spacer(1, 6))
            else:
                story.append(Paragraph(para.strip(), style()))
                story.append(Spacer(1, 6))
    
    if 'conference_contact' in data:
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Contact: {data['conference_contact']}", style()))
    
    try:
        doc.build(story)
        print(f"Visa letter generated successfully: {output_file}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_visa_letter.py <input.yaml>")
        print("Example: python generate_visa_letter.py JohnDoe.yaml")
        sys.exit(1)
    
    input_yaml = sys.argv[1]
    data = load_yaml_data(input_yaml)
    yaml_path = Path(input_yaml)
    output_file = yaml_path.with_suffix('.pdf')
    signature_file = "signature.jpg" if Path("signature.jpg").exists() else None
    create_visa_letter_pdf(data, output_file, signature_file)


if __name__ == '__main__':
    main()
