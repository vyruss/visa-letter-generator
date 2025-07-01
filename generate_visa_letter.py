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
    """Load and validate YAML input data, merging with pgeu.yaml configuration."""
    try:
        # Load user data
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Load PostgreSQL Europe configuration
        try:
            with open('pgeu.yaml', 'r', encoding='utf-8') as f:
                pgeu_config = yaml.safe_load(f)
                # Merge conference and signer data
                data.update(pgeu_config)
        except FileNotFoundError:
            print("Error: pgeu.yaml configuration file not found.")
            sys.exit(1)
        
        # Validate required fields (updated to remove conference fields)
        required_fields = [
            'full_name_passport', 'date_of_birth', 'passport_number', 'nationality',
            'address', 'embassy_name', 'embassy_address', 
            'stay_at', 'contact', 'entry_date', 'exit_date', 'gender'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Set default values for optional fields
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
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.black
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=20,
        alignment=TA_RIGHT,
        textColor=colors.black
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=6,
        alignment=TA_LEFT,
        textColor=colors.black,
        leading=11
    )
    
    # Build the document content
    story = []

    # Create header with logo and address using a table
    from reportlab.platypus import Table, TableStyle
    
    # Try to add logo, fallback to text if not found
    logo_element = None
    if Path("pgeu.jpg").exists():
        try:
            # Get original image dimensions to maintain aspect ratio
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
    
    # PostgreSQL Europe address with LEFT alignment within a right-positioned container
    pgeu_address_style = ParagraphStyle(
        'PGEUAddress',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT  # Left-aligned text within the container
    )
    pgeu_address = """
    <b>PostgreSQL Europe</b><br/>
    61, rue de Lyon<br/>
    75012 PARIS<br/>
    FRANCE<br/>
    Website: https://www.postgresql.eu/<br/>
    Email: board@postgresql.eu
    """
    address_element = Paragraph(pgeu_address, pgeu_address_style)
    
    # Calculate exact positioning to make left-aligned address text touch right edge
    page_width = A4[0] - 144  # Total width minus margins (72 each)
    
    # Estimate the width needed for the address text (longest line is the website)
    # "Website: https://www.postgresql.eu/" is approximately 2.2 inches at 9pt
    address_text_width = 2.2*inch
    
    # Calculate column widths so address text touches right edge
    logo_column_width = page_width - address_text_width
    address_column_width = address_text_width
    
    # Create header table with precise widths
    header_data = [[logo_element, address_element]]
    header_table = Table(header_data, colWidths=[logo_column_width, address_column_width])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),   # Logo left-aligned
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),   # Address LEFT-aligned within its cell
        ('RIGHTPADDING', (1, 0), (1, 0), 0), # Remove right padding
        ('LEFTPADDING', (0, 0), (-1, -1), 0), # Remove ALL left padding to touch left margin
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 20))

    # Add embassy address and date on same line using table - embassy touches left margin
    embassy_and_date_style = ParagraphStyle(
        'EmbassyAndDate',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT
    )
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_RIGHT
    )
    
    embassy_info = f"""
    {data['embassy_name']}<br/>
    {data['embassy_address'].replace('\n', '<br/>')}
    """
    today = datetime.now().strftime("%B %d, %Y")
    
    # Create embassy and date table
    embassy_para = Paragraph(embassy_info, embassy_and_date_style)
    date_para = Paragraph(today, date_style)
    
    embassy_date_data = [[embassy_para, date_para]]
    embassy_date_table = Table(embassy_date_data, colWidths=[3*inch, 3*inch])
    embassy_date_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Remove ALL left padding to touch left margin
        ('RIGHTPADDING', (1, 0), (1, 0), 0),   # Remove right padding for date to touch right margin
    ]))
    
    story.append(embassy_date_table)
    story.append(Spacer(1, 20))

    
    # Format dates for display
    try:
        # Format dates for display in DD/MM/YYYY format
        data['entry_date'] = datetime.strptime(data['entry_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        data['exit_date'] = datetime.strptime(data['exit_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        data['date_of_birth'] = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').strftime('%d/%m/%Y')
    except ValueError as e:
        print(f"Error: Invalid date format. Please use YYYY-MM-DD for date fields. Details: {e}")
        sys.exit(1)

    # Load the Jinja2 template from file
    try:
        with open('letter_template.j2', 'r', encoding='utf-8') as f:
            template_str = f.read()
        letter_template = Template(template_str)
    except FileNotFoundError:
        print("Error: letter_template.j2 not found.")
        sys.exit(1)

    # Convert newlines in contact_info to HTML breaks before rendering
    if 'signer' in data and 'contact_info' in data['signer']:
        data['signer']['contact_info'] = data['signer']['contact_info'].replace('\n', '<br/>')
    
    # Render the template
    letter_content = letter_template.render(**data)
    
    # Split content into paragraphs and add to story
    paragraphs = letter_content.strip().split('\n\n')
    for para in paragraphs:
        if para.strip():
            # Check if this paragraph contains the signature placeholder
            if '[SIGNATURE_PLACEHOLDER]' in para:
                # Replace placeholder with actual signature
                if signature_file and Path(signature_file).exists():
                    try:
                        # Add the text before the placeholder
                        text_before = para.split('[SIGNATURE_PLACEHOLDER]')[0].strip()
                        text_after = para.split('[SIGNATURE_PLACEHOLDER]')[1].strip()
                        
                        if text_before:
                            story.append(Paragraph(text_before, body_style))
                            story.append(Spacer(1, 6))
                        
                        # Add signature image - 25% less tall, maintain aspect ratio
                        with PILImage.open(signature_file) as img:
                            orig_width, orig_height = img.size
                            aspect_ratio = orig_width / orig_height
                            target_height = 0.5625*inch  # 0.75 * 0.75 = 0.5625
                            target_width = target_height * aspect_ratio
                        signature = Image(signature_file, width=target_width, height=target_height)
                        signature.hAlign = 'LEFT'
                        story.append(signature)
                        story.append(Spacer(1, 6))
                        
                        if text_after:
                            story.append(Paragraph(text_after, body_style))
                            story.append(Spacer(1, 6))
                    except Exception as e:
                        print(f"Warning: Could not add signature image: {e}")
                        # Remove placeholder and continue
                        clean_para = para.replace('[SIGNATURE_PLACEHOLDER]', '')
                        if clean_para.strip():
                            story.append(Paragraph(clean_para.strip(), body_style))
                            story.append(Spacer(1, 6))
                else:
                    # Remove placeholder if no signature file
                    clean_para = para.replace('[SIGNATURE_PLACEHOLDER]', '')
                    if clean_para.strip():
                        story.append(Paragraph(clean_para.strip(), body_style))
                        story.append(Spacer(1, 6))
            else:
                story.append(Paragraph(para.strip(), body_style))
                story.append(Spacer(1, 6))
    
    # Add conference contact info if provided
    if 'conference_contact' in data:
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Contact: {data['conference_contact']}", body_style))
    
    # Build the PDF
    try:
        doc.build(story)
        print(f"Visa letter generated successfully: {output_file}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        sys.exit(1)


def main():
    """Main function to handle command line arguments and generate the visa letter."""
    if len(sys.argv) != 2:
        print("Usage: python generate_visa_letter.py <input.yaml>")
        print("Example: python generate_visa_letter.py JohnDoe.yaml")
        sys.exit(1)
    
    input_yaml = sys.argv[1]
    
    # Load data from YAML
    data = load_yaml_data(input_yaml)
    
    # Generate output filename (same as input but with .pdf extension)
    yaml_path = Path(input_yaml)
    output_file = yaml_path.with_suffix('.pdf')
    
    # Use signature.jpg if it exists in the current directory
    signature_file = "signature.jpg"
    if not Path(signature_file).exists():
        signature_file = None
    
    # Generate the PDF
    create_visa_letter_pdf(data, output_file, signature_file)


if __name__ == '__main__':
    main()
