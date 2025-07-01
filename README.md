# Visa Letter Generator

A simple tool to generate letters to support visa applications for PostgreSQL Europe conference attendees.

## Quick Start

### 1. Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add Required Files
- Place `signature.jpg` (signer's signature) in the directory

### 3. Edit Conference Configuration
Edit `pgeu.yaml` with your conference and signer information:
- Conference details (name, dates, venue, etc.)
- Signer details (name, title, contact information)
All dates must be in YYYY-MM-DD format (e.g., "2025-10-15").

### 4. Create Individual Request File
Create a YAML file (e.g., `JohnDoe.yaml`) with the applicant's personal details and embassy details:
All dates must be in YYYY-MM-DD format (e.g., "2025-10-15").

```yaml
full_name_passport: "John Takeshi Doe"
date_of_birth: "1985-03-15"
nationality: "Japanese"
passport_number: "TK1234567"
address: "1-2-3 Shibuya Tokyo 150-0002 Japan"
gender: "Male"

embassy_name: "Embassy of Latvia"
embassy_address: |
  3-4-1 Akasaka, Minato-ku
  Tokyo 107-0052, Japan

stay_at: "Radisson Blu Latvia Conference & Spa Hotel"
contact: "+81-90-1234-5678"
entry_date: "2025-10-01"
exit_date: "2025-10-25"
```

### 5. Generate Letter
```bash
./generate_visa_letter.py JohnDoe.yaml
```

This creates `JohnDoe.pdf` with the visa support letter.

## File Structure

```
visa-letter-generator/
├── generate_visa_letter.py    # Main script
├── pgeu.yaml                  # Conference configuration
├── letter_template.j2         # Letter template
├── pgeu.jpg                   # PostgreSQL Europe logo
├── signature.jpg              # Signature image
├── requirements.txt           # Python dependencies
└── JohnDoe.yaml               # Individual request file
```
