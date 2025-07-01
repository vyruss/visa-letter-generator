# Visa Letter Generator

A standalone command-line tool to generate professional visa support letters from YAML input files. This tool creates PDF documents that can be used to support visa applications for conference attendees.

## Installation

1. Clone or download this directory
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Simply run the script with a YAML file:

```bash
python generate_visa_letter.py JohnDoe.yaml
```

This will:
- Read the data from `JohnDoe.yaml`
- Generate `JohnDoe.pdf` in the same directory
- Automatically include `signature.jpg` if it exists in the current directory

## Input Format

A pre-filled example file `JohnDoe.yaml` is provided. Copy and rename this file for each new visa letter you need to create, and then edit the contents.

### Required Fields

- `full_name_passport`: Full name as it appears on the passport.
- `date_of_birth`: Date of birth in `YYYY-MM-DD` format.
- `passport_number`: Passport number
- `nationality`: Nationality of the applicant
- `address`: Full address (can be multi-line)
- `conference_name`: Name of the conference
- `conference_dates`: Conference dates (formatted as text)
- `conference_location`: Conference location
- `embassy_name`: Name of the embassy
- `embassy_address`: Address of the embassy (can be multi-line)
- `stay_at`: Address of where the attendee will be staying
- `contact`: Contact phone number for the attendee

### Optional Fields

- `conference_contact`: Contact information for the conference organizers
- `is_speaker`: Set to `true` if the attendee is a speaker
- `pgeu_accomodations`: Set to `true` if PostgreSQL Europe is covering accomodations
- `gender`: `male` or `female` for correct pronouns.
- `conference_info`: Extra information about the conference
- `extra_text`: Any extra text to be added to the letter

## Customization

To add your own name and title to the signature block:

1.  Open `letter_template.j2` in a text editor.
2.  Find the line that says `Yours faithfully,`.
3.  After this line, add your name and title. For example:

```
<para>Yours faithfully,</para>
<para>Your Name</para>
<para>Your Title, PostgreSQL Europe</para>
```

## Dependencies

- **PyYAML**: For parsing YAML input files
- **Jinja2**: For template rendering
- **ReportLab**: For PDF generation
- **Pillow**: For image processing (signature support)
