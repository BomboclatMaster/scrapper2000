import os
import random
import logging
import json
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from PIL import Image, ImageDraw, ImageFont
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Tuple
from faker import Faker  # Import Faker
from tqdm import tqdm  # Import tqdm for progress bar

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("claim_generation.log"),  # Log to a file
    ]
)

# Directory paths
logos_dir = 'logos'
output_dir = 'output'
design_file = 'design.json'  # File to store clinic design info

# Ensure the necessary directories exist
os.makedirs(logos_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Initialize Faker instance
fake = Faker()

# Load or create design info
def load_or_create_designs(clinics_info: List[Dict]) -> Dict:
    """
    Load design info from design.json or create new designs for each clinic.
    Args:
        clinics_info: List of clinics (dicts).
    Returns:
        Dict: Design info for each clinic.
    """
    if os.path.exists(design_file):
        with open(design_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        designs = {}
        for clinic in clinics_info:
            clinic_name = clinic['name']
            designs[clinic_name] = {
                'primary_color': random.choice(['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']),
                'secondary_color': random.choice(['#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5']),
                'font': random.choice(['Helvetica-Bold', 'Times-Roman', 'Courier']),
            }
        with open(design_file, 'w', encoding='utf-8') as file:
            json.dump(designs, file, indent=4)
        return designs

# Load data from CSV and JSON files
def load_data() -> Tuple[List[Dict], List[Tuple[str, str]], Dict]:
    """
    Load data from CSV and JSON files.
    Returns:
        clinics_info: List of clinics (dicts).
        doctors_info: List of tuples (doctor name, specialty).
        specialties_diseases: Dictionary mapping specialties to diseases.
    """
    try:
        # Load clinics info
        clinics_info = []
        with open('hospitals_and_clinics.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Ensure telephone and address fields exist
                row['telephone'] = row.get('telephone', 'N/A')
                row['address'] = row.get('address', 'N/A')
                row['location'] = row.get('location', 'N/A')
                row['email'] = row.get('email', 'N/A')
                clinics_info.append(row)
            if not clinics_info:
                raise ValueError("No data found in hospitals_and_clinics.csv")

        # Load doctors info
        doctors_info = []
        with open('doctors_and_specialists_list.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            doctors_info = [(row['Doctor Name'], row['Specialty']) for row in reader]
            if not doctors_info:
                raise ValueError("No data found in doctors_and_specialists_list.csv")

        # Load specialties and diseases info
        with open('specialities_diseases.json', 'r', encoding='utf-8') as file:
            specialties_diseases = json.load(file)
            if not specialties_diseases:
                raise ValueError("No data found in specialities_diseases.json")

        return clinics_info, doctors_info, specialties_diseases

    except Exception as e:
        logging.error(f"Error loading data: {e}")
        raise

# Load billing items from JSON file
def load_billing_items() -> Dict[str, Dict[str, List[Dict]]]:
    """
    Load billing items from disease_consultation.json.
    Returns:
        Dictionary mapping diagnoses to billing items.
    """
    try:
        with open('disease_consultation.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('diagnoses', {})
    except Exception as e:
        logging.error(f"Error loading billing items: {e}")
        return {}

# Generate a simple text-based logo for a provider
def generate_logo(provider_name: str, logo_file: str) -> bool:
    """
    Generate a simple text-based logo for a provider.
    Args:
        provider_name: Name of the provider.
        logo_file: Path to save the generated logo.
    Returns:
        bool: True if the logo was generated successfully, False otherwise.
    """
    try:
        # Create a blank image
        width, height = 300, 100
        img = Image.new('RGB', (width, height), color=(255, 255, 255))  # White background
        d = ImageDraw.Draw(img)

        # Use a default font
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()

        # Draw text (provider name) on the image
        text = provider_name[:20]  # Limit the text length to avoid overflow
        bbox = d.textbbox((0, 0), text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((width - text_width) / 2, (height - text_height) / 2), text, fill=(0, 0, 0), font=font)

        # Save the image as a logo
        img.save(logo_file)
        logging.info(f"Logo generated for {provider_name} and saved to {logo_file}")
        return True
    except Exception as e:
        logging.error(f"Error generating logo for {provider_name}: {e}")
        return False

def verify_logo(logo_file: str) -> bool:
    """
    Verifies if the logo image exists and is a valid image file.
    Args:
        logo_file: Path to the logo file.
    Returns:
        bool: True if the logo exists and is a valid image file, False otherwise.
    """
    try:
        # Check if the file exists and is an image
        if os.path.exists(logo_file):
            with Image.open(logo_file) as img:
                img.verify()  # This will check if the image is valid
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error verifying logo {logo_file}: {e}")
        return False

# Generate a professional medical bill PDF
def generate_claim_pdf(clinic: Dict, doctor: Tuple[str, str], diagnosis: str, fraud_type: str, output_pdf: str, design: Dict, billing_items: List[List[str]]) -> None:
    """
    Generate a professional medical bill PDF.
    Args:
        clinic: Dictionary containing clinic information.
        doctor: Tuple containing doctor name and specialty.
        diagnosis: Diagnosis for the claim.
        fraud_type: Type of claim ("legitimate" or "fraudulent").
        output_pdf: Path to save the generated PDF.
        design: Dictionary containing design info for the clinic.
        billing_items: List of billing items for the diagnosis.
    """
    try:
        # Generate fake patient data using Faker
        patient_name = fake.name()
        patient_id = fake.random_int(min=100000, max=999999)

        # Create a PDF canvas
        c = canvas.Canvas(output_pdf, pagesize=letter)

        # Set up design colors and font
        primary_color = design['primary_color']
        secondary_color = design['secondary_color']
        font_name = design['font']

        # Add clinic logo
        logo_file = os.path.join(logos_dir, f"logo_{clinic['name']}.png")
        if not os.path.exists(logo_file) or not verify_logo(logo_file):
            generate_logo(clinic['name'], logo_file)

        if verify_logo(logo_file):
            c.drawImage(logo_file, 50, 700, width=100, height=50)

        # Add clinic information
        c.setFont(font_name, 16)
        c.setFillColor(primary_color)
        c.drawString(170, 730, clinic['name'])
        c.setFont(font_name, 12)
        c.setFillColor(colors.black)
        c.drawString(170, 710, clinic['address'])
        c.drawString(170, 690, f"Phone: {clinic['telephone']}")
        c.drawString(170, 670, f"Email: {clinic['email']}")

        # Add bill header
        c.setFont(font_name, 14)
        c.setFillColor(primary_color)
        c.drawString(50, 640, "Medical Bill Receipt")
        c.line(50, 635, 550, 635)

        # Add patient information (using fake data)
        c.setFont(font_name, 12)
        c.drawString(50, 610, f"Patient Name: {patient_name}")
        c.drawString(50, 590, f"Patient ID: {patient_id}")
        c.drawString(50, 570, "Date of Service: " + datetime.now().strftime("%Y-%m-%d"))

        # Add doctor and diagnosis information
        c.drawString(50, 540, f"Doctor: {doctor[0]} ({doctor[1]})")
        c.drawString(50, 520, f"Diagnosis: {diagnosis}")

        # Add dynamic billing details table based on diagnosis
        data = [["Item", "Description", "Quantity", "Unit Price (Rs)", "Total (Rs)"]] + billing_items
        table_width = 480  # Total width for the table
        col_widths = [table_width * 0.15, table_width * 0.35, table_width * 0.10, table_width * 0.20, table_width * 0.20]  # Adjusted column widths to fit within the page
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # Reduced font size
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), secondary_color),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        table.wrapOn(c, 400, 200)
        table.drawOn(c, 50, 400)

        # Add total amount (calculated from billing items)
        total_amount = sum([float(item[4]) for item in billing_items])
        c.setFont(font_name, 12)
        c.setFillColor(primary_color)
        c.drawString(400, 370, f"Total Amount: Rs {total_amount:.2f}")

        # Add footer
        c.setFont(font_name, 10)
        c.setFillColor(colors.black)
        c.drawString(50, 50, f"Thank you for choosing {clinic['name']}!")
        c.drawString(50, 35, f"For any queries, please contact us at {clinic['telephone']} or {clinic['email']}")

        # Save the PDF
        c.save()
        logging.info(f"Claim PDF generated successfully: {output_pdf}")
    except Exception as e:
        logging.error(f"Error generating claim PDF for {fraud_type}: {e}")

# Dynamic billing items based on diagnosis
def get_billing_items_for_diagnosis(diagnosis: str, billing_items_data: Dict[str, Dict[str, List[Dict]]]) -> List[List[str]]:
    """
    Returns billing items based on the diagnosis.
    Args:
        diagnosis: Diagnosis name.
        billing_items_data: Dictionary mapping diagnoses to billing items.
    Returns:
        List of billing items (Item, Description, Quantity, Unit Price, Total).
    """
    items = billing_items_data.get(diagnosis, {}).get("billing_items", [])
    if not items:
        # Placeholder if no matching diagnosis found
        return [
            ["Consultation", "General Consultation", "1", "1000", "1000"],
            ["Lab Test", "General Lab Test", "1", "500", "500"]
        ]
    return [[item["Item"], item["Description"], str(item["Quantity"]), str(item["Unit Price"]), str(item["Total"])] for item in items]

# Main execution
if __name__ == "__main__":
    try:
        # Define the number of legitimate and fraudulent claims to generate
        legitimate_count = 50
        fraudulent_count = 50

        # Load data
        clinics_info, doctors_info, specialties_diseases = load_data()
        designs = load_or_create_designs(clinics_info)
        billing_items_data = load_billing_items()

        # Generate legitimate and fraudulent claims
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            total_claims = legitimate_count + fraudulent_count
            with tqdm(total=total_claims, desc="Generating Claims") as pbar:
                for i in range(legitimate_count):
                    clinic = random.choice(clinics_info)
                    doctor = random.choice(doctors_info)
                    specialty = doctor[1]
                    if specialty in specialties_diseases:
                        diagnosis = random.choice(specialties_diseases[specialty])  # Choose a diagnosis from the specialty
                        billing_items = get_billing_items_for_diagnosis(diagnosis, billing_items_data)
                        output_pdf = os.path.join(output_dir, f"legit_claim_{i}.pdf")
                        futures.append(executor.submit(generate_claim_pdf, clinic, doctor, diagnosis, "legitimate", output_pdf, designs[clinic['name']], billing_items))

                for i in range(fraudulent_count):
                    clinic = random.choice(clinics_info)
                    doctor = random.choice(doctors_info)
                    specialty = doctor[1]
                    if specialty in specialties_diseases:
                        diagnosis = random.choice(specialties_diseases[specialty])  # Choose a diagnosis from the specialty
                        billing_items = get_billing_items_for_diagnosis(diagnosis, billing_items_data)
                        output_pdf = os.path.join(output_dir, f"fraud_claim_{i}.pdf")
                        futures.append(executor.submit(generate_claim_pdf, clinic, doctor, diagnosis, "fraudulent", output_pdf, designs[clinic['name']], billing_items))

                # Wait for all tasks to complete and update progress bar
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    pbar.update(1)

        logging.info(f"Successfully generated {legitimate_count} legitimate and {fraudulent_count} fraudulent claims.")
    except Exception as e:
        logging.error(f"Fatal error in main execution: {e}")
