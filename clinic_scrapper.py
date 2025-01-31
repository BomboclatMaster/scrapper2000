import logging
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import csv
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize session
session = requests.Session()

# Retry strategy (using allowed_methods instead of method_whitelist)
retry_strategy = Retry(
    total=3,  # Retry 3 times if the request fails
    backoff_factor=1,  # Time between retries increases exponentially
    status_forcelist=[500, 502, 503, 504],  # Retry on server errors
    allowed_methods=["HEAD", "GET", "OPTIONS"]  # Corrected argument name
)

# Attach the adapter to the session to configure the pool size and retries
adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

BASE_URL = "https://www.medpages.info/sf/"

# Function to fetch max page number from the pagination
def get_max_page_number(url):
    logging.info(f"Fetching max page number from {url}...")
    try:
        response = session.get(url)
        if response.status_code != 200:
            logging.error(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return 1  # Return 1 as default page if unable to fetch
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the last pagination element and extract the page number
        pagination = soup.find('div', class_='pagination-container')
        last_page_link = pagination.find_all('a')[-2]  # Second last link is the max page
        max_page_number = int(last_page_link.get_text())
        logging.info(f"Max page number: {max_page_number}")
        return max_page_number
        # return 1
    except Exception as e:
        logging.error(f"Error fetching max page number: {e}")
        return 1

# Function to fetch hospital/clinic links from a single page
def fetch_hospital_links_from_page(url):
    logging.info(f"Fetching hospital/clinic links from {url}...")
    try:
        response = session.get(url)
        if response.status_code != 200:
            logging.error(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()  # Use a set to avoid duplicate links
        
        # Find all <a> tags that have a <section> child with class 'result-record' or 'highlight-result'
        for a_tag in soup.find_all('a', href=True):
            section = a_tag.find('section', class_=['result-record', 'highlight-result'])
            if section:
                # Make sure we are constructing the full URL
                full_url = f"{BASE_URL}/{a_tag['href']}" if a_tag['href'].startswith("index.php") else a_tag['href']
                links.add(full_url)
        
        logging.info(f"Found {len(links)} hospital/clinic links on page.")
        return list(links)
    except Exception as e:
        logging.error(f"Error fetching hospital links from {url}: {e}")
        return []

# Function to scrape hospital/clinic data from the details page
def fetch_hospital_details(hospital_url):
    logging.info(f"Scraping hospital/clinic details from {hospital_url}...")
    try:
        response = session.get(hospital_url)
        logging.info(f"{hospital_url}... response.status {response.status_code}")

        if response.status_code != 200:
            logging.error(f"Failed to retrieve data from {hospital_url}. Status code: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract name and field from the 'main-record-title' section
        name = soup.find('h1', class_='main-name').get_text(strip=True) if soup.find('h1', class_='main-name') else None
        field = soup.find('h2', class_='main-field').get_text(strip=True) if soup.find('h2', class_='main-field') else None

        logging.debug(f"Scraped Name: {name}, Field: {field}")  # Debug logging for scraped data
        
        # Extract contact info from the 'contact-info' section
        contact_info = soup.find('section', class_='contact-info')
        telephone = address = location = None
        if contact_info:
            info_table = contact_info.find('table', class_='info-table')
            if info_table:
                rows = info_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if 'Telephone' in label:
                            telephone = value
                        elif 'Address' in label:
                            address = value
                        elif 'Location' in label:
                            location = value

        logging.debug(f"Scraped Telephone: {telephone}, Address: {address}, Location: {location}")  # Debug logging for contact info

        return {
            "name": name,
            "field": field,
            "telephone": telephone,
            "address": address,
            "location": location
        }
    except Exception as e:
        logging.error(f"Error scraping hospital details from {hospital_url}: {e}")
        return None

# Function to scrape hospital data from all pages concurrently
def scrape_hospitals():
    base_url = "https://www.medpages.info/sf/index.php?page=newsearchresults&q=mauritius&sp=no&lat=&long=&pageno={}"

    # Get the max page number
    max_page = get_max_page_number(base_url.format(1))

    # Create a thread pool based on available CPU cores
    num_threads = os.cpu_count() or 4  # Default to 4 threads if cpu_count() is None
    logging.info(f"Using {num_threads} threads for concurrent scraping.")

    # Gather all the page URLs
    page_urls = [base_url.format(i) for i in range(1, max_page + 1)]

    # Use ThreadPoolExecutor for concurrent fetching of pages
    all_hospital_links = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_url = {executor.submit(fetch_hospital_links_from_page, url): url for url in page_urls}
        
        # Wait for results and collect hospital links
        for future in as_completed(future_to_url):
            result = future.result()
            if result:
                all_hospital_links.extend(result)

    logging.info(f"Total hospital/clinic links fetched: {len(all_hospital_links)}")

    # Now scrape the details of each hospital/clinic concurrently
    hospital_details = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_url = {executor.submit(fetch_hospital_details, link): link for link in all_hospital_links}
        
        for future in as_completed(future_to_url):
            details = future.result()
            if details:
                hospital_details.append(details)

    logging.info(f"Total hospital details scraped: {len(hospital_details)}")

    # Save the results to a CSV file
    save_to_csv(hospital_details)

# Function to save hospital details to CSV
def save_to_csv(hospital_details):
    if not hospital_details:
        logging.warning("No hospital details to save.")
        return

    keys = hospital_details[0].keys()
    try:
        with open('hospitals_and_clinics.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=keys)
            writer.writeheader()
            for detail in hospital_details:
                writer.writerow(detail)

        logging.info("Hospital details saved to hospitals_and_clinics.csv")
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")

# Run the scraper
if __name__ == "__main__":
    scrape_hospitals()
