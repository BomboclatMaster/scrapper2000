import requests
from bs4 import BeautifulSoup
import csv
import logging
import concurrent.futures
import os

# Initialize logging to display detailed information in the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a session to reuse HTTP connections
session = requests.Session()

# Function to fetch and parse doctor/specialist data from a given URL
def fetch_doctors_data(url):
    logging.info(f"Fetching data from {url}...")
    
    try:
        response = session.get(url)
        if response.status_code != 200:
            logging.error(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return []
        logging.info(f"Successfully retrieved data from {url}.")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table with the ID 'doctor-list-result'
        table = soup.find('table', {'id': 'doctor-list-result'})
        if not table:
            logging.warning(f"Table not found at {url}.")
            return []

        doctor_data = []
        rows = table.find_all('tr')[1:]  # Skip the header row (index 0)

        # Extract doctor name and specialty from each row
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 2:  # Ensure there are enough columns (Name and Specialty)
                doctor_name = columns[0].get_text(strip=True)
                specialty = columns[1].get_text(strip=True)
                if doctor_name and specialty:
                    doctor_data.append([doctor_name, specialty])

        logging.info(f"Found {len(doctor_data)} doctor(s) and specialist(s) in {url}.")
        return doctor_data
    except Exception as e:
        logging.error(f"Error fetching data from {url}: {e}")
        return []

# Function to scrape doctors/specialists for a specific alphabet
def scrape_doctors_for_alphabet(alphabet):
    logging.info(f"Scraping doctors for alphabet: {alphabet}")
    
    # URL for doctor list (Medical Council Doctors)
    doctor_url = f"https://medicalcouncilmu.org/doctors-list/?alphabet={alphabet}"
    doctors = fetch_doctors_data(doctor_url)

    # URL for specialists list (Registered Specialists)
    specialist_url = f"https://medicalcouncilmu.org/list-of-registered-specialists/?alphabet={alphabet}"
    specialists = fetch_doctors_data(specialist_url)
    
    return doctors + specialists

# Function to save doctor data to CSV
def save_doctors_to_csv(doctor_data, filename="doctors_and_specialists_list.csv"):
    logging.info(f"Saving {len(doctor_data)} doctor(s) and specialist(s) to CSV file...")
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Doctor Name", "Specialty"])  # Header
        writer.writerows(doctor_data)
    logging.info(f"Doctor and specialist data saved to {filename}")

# Main script
if __name__ == "__main__":
    all_doctors = []

    # Dynamically determine the number of threads based on the number of CPU cores available
    num_threads = os.cpu_count()  # Get the number of CPU cores
    logging.info(f"Using {num_threads} threads for scraping.")

    # Use concurrent.futures to scrape for all alphabets (A-Z) concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Generate a list of alphabets (A-Z) and map them to the function
        alphabets = [chr(i) for i in range(65, 91)]  # A-Z
        futures = {executor.submit(scrape_doctors_for_alphabet, alphabet): alphabet for alphabet in alphabets}
        
        # Track progress as each task completes
        for future in concurrent.futures.as_completed(futures):
            alphabet = futures[future]
            try:
                data = future.result()
                all_doctors.extend(data)
                logging.info(f"Scraped data for alphabet: {alphabet}")
            except Exception as e:
                logging.error(f"Error while scraping alphabet {alphabet}: {e}")

    # Save the collected data to a CSV file
    save_doctors_to_csv(all_doctors)

    logging.info("Scraping completed. All doctor and specialist data has been saved.")
