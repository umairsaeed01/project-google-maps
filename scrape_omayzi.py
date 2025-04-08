import sys
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re # For potential regex use later

def format_for_url(text):
    """Formats text for Seek URL: lowercase, spaces to hyphens."""
    return text.lower().replace(' ', '-')

def get_driver():
    """Initializes and returns a Selenium WebDriver."""
    print("Python: Initializing WebDriver...", file=sys.stderr)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    print("Python: WebDriver Initialized.", file=sys.stderr)
    return driver

def get_job_links_from_search(driver, jobTitle, location, numJobs_limit):
    """Gets job links from the Seek search results page."""
    print(f"Python: Getting job links for title='{jobTitle}', location='{location}', limit='{numJobs_limit}'", file=sys.stderr)
    formatted_title = format_for_url(jobTitle)
    formatted_location = format_for_url(location)
    search_url = f'https://www.seek.com.au/{formatted_title}-jobs/in-{formatted_location}'
    print(f"Python: Navigating to search URL: {search_url}", file=sys.stderr)

    try:
        driver.get(search_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//article[@data-card-type='JobCard']"))
        )
        print("Python: Search results page loaded.", file=sys.stderr)
        time.sleep(2)
        html_content = driver.page_source
    except Exception as e:
        print(f"Python: Error loading search results page {search_url}: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    job_cards = soup.find_all('article', attrs={'data-card-type': 'JobCard'})
    print(f"Python: Found {len(job_cards)} potential job cards on search page.", file=sys.stderr)

    for job_card in job_cards:
        if len(links) >= numJobs_limit:
            print(f"Python: Reached job link limit of {numJobs_limit}.", file=sys.stderr)
            break

        title_element = job_card.find('a', attrs={'data-automation': 'jobTitle'})
        if title_element and title_element.has_attr('href'):
            job_link = f"https://www.seek.com.au{title_element['href']}"
            if job_link not in links and '/job/' in job_link:
                 links.append(job_link)
        else:
            print("Python: Found job card without a valid title link.", file=sys.stderr)

    print(f"Python: Extracted {len(links)} job links.", file=sys.stderr)
    return links

def scrape_job_details(driver, job_url):
    """Scrapes detailed information from a single job page."""
    print(f"Python: Scraping details from: {job_url}", file=sys.stderr)
    details = {
        "Job Title": "-", "Company Name": "-", "Location": "-", "Salary/Pay Range": "-",
        "Key Responsibilities": "-", "Required Skills/Qualifications": "-", "Date Posted": "-",
        "Job Type": "-", "Phone Number": "-", "Email": "-", "Full Job Description": "-",
        "Job URL": job_url
    }

    try:
        driver.get(job_url)
        WebDriverWait(driver, 15).until(
             EC.presence_of_element_located((By.XPATH, "//div[@data-automation='jobDescription'] | //div[contains(@class,'job-description')]"))
        )
        print(f"Python: Job details page loaded: {job_url}", file=sys.stderr)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # --- Selector Guesses - THESE NEED TO BE VERIFIED/ADJUSTED ---
        # Corrected syntax: Use if statements
        title_el = soup.find('h1', attrs={'data-automation': 'jobTitle'}) or soup.find('h1')
        details["Job Title"] = title_el.text.strip() if title_el else "-"

        company_el = soup.find('span', attrs={'data-automation': 'advertiser-name'}) or soup.find('a', attrs={'data-automation': 'jobCompany'})
        details["Company Name"] = company_el.text.strip() if company_el else "-"

        location_strong = soup.find('strong', string=re.compile(r'Location', re.I))
        location_next_sibling = location_strong.find_next_sibling(string=True) if location_strong else None
        location_el = soup.find('span', attrs={'data-automation': 'job-detail-location'}) or location_next_sibling
        details["Location"] = location_el.strip() if isinstance(location_el, str) else location_el.text.strip() if location_el else "-"


        salary_el = soup.find('span', attrs={'data-automation': 'job-detail-salary'}) or soup.find(string=re.compile(r'\$\d+.*(per|p\.a|annum)', re.I))
        details["Salary/Pay Range"] = salary_el.text.strip() if salary_el else "-"

        job_type_el = soup.find('span', attrs={'data-automation': 'job-detail-work-type'}) or soup.find(string=re.compile(r'(full time|part time|contract|casual)', re.I))
        details["Job Type"] = job_type_el.text.strip() if job_type_el else "-"

        date_posted_el = soup.find('span', attrs={'data-automation': 'job-detail-date'})
        details["Date Posted"] = date_posted_el.text.strip() if date_posted_el else "-"

        description_div = soup.find('div', attrs={'data-automation': 'jobDescription'}) or soup.find('div', class_=lambda x: x and 'job-description' in x)
        details["Full Job Description"] = description_div.get_text(separator='\n', strip=True) if description_div else "-"

        if description_div:
            responsibilities_heading = description_div.find(['h2', 'h3', 'strong'], string=re.compile(r'Responsibilities|Duties', re.I))
            if responsibilities_heading:
                 resp_sibling = responsibilities_heading.find_next_sibling(string=True)
                 details["Key Responsibilities"] = resp_sibling.strip() if resp_sibling else "See description"

            skills_heading = description_div.find(['h2', 'h3', 'strong'], string=re.compile(r'Skills|Qualifications|Requirements', re.I))
            if skills_heading:
                 skills_sibling = skills_heading.find_next_sibling(string=True)
                 details["Required Skills/Qualifications"] = skills_sibling.strip() if skills_sibling else "See description"

        details["Phone Number"] = "-"
        details["Email"] = "-"

        print(f"Python: Successfully scraped details for: {job_url}", file=sys.stderr)

    except Exception as e:
        print(f"Python: Error scraping details for {job_url}: {e}", file=sys.stderr)
        details["Job Title"] = f"Error scraping: {e}"

    return details


def scrape_seek_jobs(jobTitle, location, numJobs):
    """Main function to orchestrate scraping."""
    print("Python: Starting scrape_seek_jobs...", file=sys.stderr)
    driver = None
    all_job_details = []
    try:
        limit = int(numJobs)
    except ValueError:
        print(f"Python: Invalid numJobs '{numJobs}', defaulting to 5.", file=sys.stderr)
        limit = 5

    try:
        driver = get_driver()
        job_links = get_job_links_from_search(driver, jobTitle, location, limit)

        if not job_links:
            print("Python: No job links found on search results page.", file=sys.stderr)
            return json.dumps([])

        print(f"Python: Found {len(job_links)} links. Scraping details for each...", file=sys.stderr)
        for i, link in enumerate(job_links):
            print(f"--- Scraping Job {i+1}/{len(job_links)} ---", file=sys.stderr)
            details = scrape_job_details(driver, link)
            all_job_details.append(details)
            sleep_time = 2 + (i % 3)
            print(f"Python: Sleeping for {sleep_time} seconds...", file=sys.stderr)
            time.sleep(sleep_time)

    except Exception as e:
        print(f"Python: General error in scrape_seek_jobs: {e}", file=sys.stderr)
        return json.dumps({"error": f"An error occurred: {e}", "partial_results": all_job_details})
    finally:
        if driver:
            driver.quit()
            print("Python: WebDriver closed.", file=sys.stderr)

    print(f"Python: Finished scraping. Returning {len(all_job_details)} detailed job results.", file=sys.stderr)
    return json.dumps(all_job_details)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(json.dumps({"error": "Usage: python scrape_omayzi.py <jobTitle> <location> <numJobs>"}))
        sys.exit(1)

    job_title_arg = sys.argv[1]
    location_arg = sys.argv[2]
    num_jobs_arg = sys.argv[3]

    result_json = scrape_seek_jobs(job_title_arg, location_arg, num_jobs_arg)
    print(result_json)
