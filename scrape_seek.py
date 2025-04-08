# scrape_seek.py
import os
print(f"Current working directory: {os.getcwd()}")
import csv
import re
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def extract_contact_info(text):
    """Extracts phone numbers and email addresses from text."""
    # Simple regex for phone numbers (adjust as needed for different formats)
    phone_regex = r'(\(?\+?\d{1,3}\)?[\s.-]?\d{1,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4})'
    # Simple regex for emails
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    phones = re.findall(phone_regex, text)
    emails = re.findall(email_regex, text)

    phone_str = ', '.join(phones) if phones else '-'
    email_str = ', '.join(emails) if emails else '-'
    return phone_str, email_str

def scrape_seek(keyword, location, max_jobs=None):
    """Scrapes Seek job listings and returns data as a list of lists."""
    base_url = "https://www.seek.com.au"
    # Format location for URL (e.g., "Melbourne VIC" -> "melbourne-vic")
    location_slug = location.lower().replace(' ', '-')
    search_url = f"{base_url}/{keyword.lower().replace(' ', '-')}-jobs/in-{location_slug}"
    print(f"Starting scrape for '{keyword}' in '{location}' (max_jobs={max_jobs})...")
    print(f"Search URL: {search_url}")

    job_data = []
    # Define headers for the CSV file
    headers = [
        "Job Title", "Company Name", "Location", "Salary/Pay Range",
        "Key Responsibilities", "Required Skills/Qualifications", "Date Posted",
        "Job Type", "Phone Number", "Email", "Full Job Description", "Job URL"
    ]
    job_data.append(headers)

    with sync_playwright() as p:
        # Try launching with channel='chrome' if default chromium fails
        try:
            browser = p.chromium.launch(headless=True) # Set headless=False to watch
        except Exception as launch_error:
            print(f"Chromium launch failed: {launch_error}. Trying with Chrome channel.")
            try:
                 browser = p.chromium.launch(channel="chrome", headless=True)
            except Exception as channel_launch_error:
                 print(f"Chrome channel launch also failed: {channel_launch_error}")
                 print("Please ensure Playwright browsers are installed (`playwright install`)")
                 return # Exit if browser cannot be launched

        page = browser.new_page()
        # Add a user-agent to look more like a real browser
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})


        try:
            print(f"Navigating to {search_url}...")
            page.goto(search_url, wait_until='domcontentloaded', timeout=90000) # Increased timeout
            print("Page loaded. Waiting for job listings...")
            # Wait for job cards to be present using a more robust selector
            page.wait_for_selector('article[data-card-type="JobCard"]', timeout=60000) # Increased timeout
            print("Job listings found.")

            # --- Get job links ---
            job_links = set() # Use a set to avoid duplicates
            # Find all article elements representing job cards
            job_card_articles = page.query_selector_all('article[data-card-type="JobCard"]')
            print(f"Found {len(job_card_articles)} job card articles.")

            for article in job_card_articles:
                 # Try finding the link within the h3 tag first
                 link_element = article.query_selector('h3 a[data-automation="job-title"]')
                 # Fallback to a more general link if the specific one isn't found
                 if not link_element:
                      link_element = article.query_selector('a[data-automation="jobTitle"]') # Check this selector too
                 if not link_element:
                      link_element = article.query_selector('a[href*="/job/"]') # General fallback

                 if link_element:
                     href = link_element.get_attribute('href')
                     if href and href.startswith('/job/'):
                         full_url = base_url + href.split('?')[0] # Clean URL parameters
                         job_links.add(full_url)


            job_links = list(job_links) # Convert back to list for iteration
            print(f"Extracted {len(job_links)} unique job URLs.")

            if not job_links:
                 print("No job links found. The selectors might need updating or the search yielded no results.")
                 print("Page HTML snippet:")
                 print(page.content()[:2000]) # Print start of HTML for debugging selectors


            # --- Scrape each job page ---
            jobs_to_scrape = job_links
            if max_jobs is not None and max_jobs > 0:
                jobs_to_scrape = job_links[:max_jobs]
                print(f"Limiting scrape to {len(jobs_to_scrape)} jobs based on max_jobs={max_jobs}.")

            for i, job_url in enumerate(jobs_to_scrape):
                print(f"\nScraping job {i+1}/{len(jobs_to_scrape)}: {job_url}")
                try:
                    page.goto(job_url, wait_until='domcontentloaded', timeout=60000)
                    # Allow some time for dynamic content if needed
                    time.sleep(3) # Increased sleep slightly
                    html_content = page.content()
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # --- Extract data using BeautifulSoup ---
                    # Selectors need careful inspection and adjustment based on Seek's current HTML structure
                    # These are examples and likely need refinement

                    # Title
                    title = soup.find('h1', {'data-automation': 'job-detail-title'})
                    title_text = title.text.strip() if title else '-'
                    if title_text == '-': # Fallback selector
                         title = soup.find('h1', class_=lambda x: x and 'JobTitle' in x)
                         title_text = title.text.strip() if title else '-'


                    # Company
                    company = soup.find('span', {'data-automation': 'advertiser-name'})
                    company_text = company.text.strip() if company else '-'
                    if company_text == '-' : # Fallback using link
                         company_link = soup.find('a', {'data-automation': 'job-header-company-name'})
                         company_text = company_link.text.strip() if company_link else '-'
                    if company_text == '-': # Generic fallback
                         company = soup.find('span', class_=lambda x: x and 'AdvertiserName' in x)
                         company_text = company.text.strip() if company else '-'


                    # Location
                    location_element = soup.find('span', {'data-automation': 'job-detail-location'})
                    location_text = location_element.text.strip() if location_element else '-'
                    if location_text == '-': # Fallback using strong tag heuristic
                        strong_tags = soup.find_all('strong')
                        for tag in strong_tags:
                             parent_div = tag.find_parent('div')
                             if parent_div and 'Location' in parent_div.text:
                                 location_text = tag.text.strip()
                                 break
                    if location_text == '-': # Generic fallback
                         loc_span = soup.find('span', class_=lambda x: x and 'Location' in x)
                         if loc_span:
                              # Often location is inside a link within this span
                              loc_link = loc_span.find('a')
                              location_text = loc_link.text.strip() if loc_link else loc_span.text.strip()


                    # Salary
                    salary = soup.find('span', {'data-automation': 'job-detail-salary'})
                    salary_text = salary.text.strip() if salary else '-'
                    if salary_text == '-': # Generic fallback
                         salary = soup.find('span', class_=lambda x: x and 'Salary' in x)
                         salary_text = salary.text.strip() if salary else '-'


                    # Job Type / Classification
                    job_type_text = '-'
                    # Find the container div first
                    classification_div = soup.find('div', string=lambda t: t and 'Classification' in t)
                    if classification_div:
                         # Find the actual classification text, often in a following sibling or child span/strong tag
                         details_span = classification_div.find_next_sibling('span')
                         if details_span:
                              job_type_text = details_span.text.strip()
                         else: # Try finding within strong tags if no direct span sibling
                              strong_tag = classification_div.find_next('strong')
                              if strong_tag:
                                   job_type_text = strong_tag.text.strip()


                    # Date Posted
                    date_posted_element = soup.find('span', {'data-automation': 'job-detail-date'})
                    date_posted_text = date_posted_element.text.strip() if date_posted_element else '-'
                    if date_posted_text == '-': # Generic fallback
                         date_span = soup.find('span', class_=lambda x: x and 'ListedDate' in x)
                         date_posted_text = date_span.text.strip() if date_span else '-'


                    # Full description
                    description_div = soup.find('div', {'data-automation': 'jobAdDetails'})
                    full_description_text = description_div.get_text(separator='\n', strip=True) if description_div else '-'
                    if full_description_text == '-': # Fallback
                         description_div = soup.find('div', class_=lambda x: x and 'job-description' in x)
                         full_description_text = description_div.get_text(separator='\n', strip=True) if description_div else '-'


                    # Extract Responsibilities & Skills (Placeholder - requires better logic)
                    responsibilities_text = "See Full Description"
                    skills_text = "See Full Description"

                    # Extract contacts
                    phone_text, email_text = extract_contact_info(full_description_text)

                    job_details = [
                        title_text, company_text, location_text, salary_text,
                        responsibilities_text, skills_text, date_posted_text,
                        job_type_text, phone_text, email_text, full_description_text, job_url
                    ]
                    job_data.append(job_details)
                    print(f"Successfully extracted: {title_text} | {company_text} | {location_text}")
                    time.sleep(1.5) # Slightly longer delay

                except Exception as e:
                    print(f"Error scraping {job_url}: {e}")
                    job_data.append(['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', f'Error scraping: {e}', job_url])


        except Exception as e:
            print(f"An error occurred during scraping setup or navigation: {e}")
            print("Page HTML snippet at time of error:")
            try:
                print(page.content()[:2000]) # Print start of HTML for debugging selectors
            except Exception as content_error:
                print(f"Could not get page content: {content_error}")


        finally:
            browser.close()
            print("\nBrowser closed.")

    # --- Return data ---
    print(f"Scraping finished. Returning {len(job_data) - 1} jobs.")
    return job_data

# Optional: Keep for testing if needed, but commented out for module use
# if __name__ == "__main__":
    # Ensure location matches Seek's format if possible (e.g., "Melbourne VIC")
    # Check Seek URL structure for location formatting
    # results = scrape_seek("AI Engineer", "Melbourne VIC", max_jobs=5)
    # if results:
    #     # Print header
    #     print("\n--- Scraped Data ---")
    #     print(results[0])
    #     # Print first data row
    #     if len(results) > 1:
    #         print(results[1])
    #
    # Example for different search:
    # scrape_seek("Data Scientist", "Sydney NSW", filename="seek_ds_jobs_sydney.csv")