import requests
from bs4 import BeautifulSoup
import re # For potentially extracting email/phone later

# Seek URL structure (adjust if needed based on current Seek structure)
SEEK_URL = "https://www.seek.com.au/{}-jobs/in-All-Australia"

# Headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

def scrape_seek(job_title):
    """
    Scrapes Seek.com for jobs matching the given job title.

    Args:
        job_title (str): The job title to search for.

    Returns:
        list: A list of dictionaries, where each dictionary represents a job
              with keys: 'title', 'company', 'salary', 'description'.
              Returns an empty list if no jobs are found or an error occurs.
    """
    if not job_title:
        return []

    # Format the job title for the URL (e.g., "data scientist" -> "data-scientist")
    formatted_title = job_title.strip().lower().replace(' ', '-')
    search_url = SEEK_URL.format(formatted_title)
    print(f"Scraping URL: {search_url}") # Debugging print

    try:
        response = requests.get(search_url, headers=HEADERS, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Check for CAPTCHA or blocking - this is a basic check, might need refinement
        if "challenge" in response.url.lower() or "captcha" in response.text.lower():
            print("Warning: CAPTCHA or block detected. Cannot proceed with scraping.")
            # In a real app, you might raise a specific exception here
            return [] # Indicate failure due to block

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- CSS Selectors for Seek (These might change!) ---
        # Find all job listing containers. This selector needs verification.
        # Inspect Seek's HTML structure to find the right container element.
        # Example selector (likely needs updating): 'article[data-card-type="JobCard"]'
        job_cards = soup.find_all('article', {'data-automation': 'normalJob'}) # Example selector - VERIFY THIS

        if not job_cards:
            print("No job cards found using the current selector.")
            return []

        results = []
        for card in job_cards:
            # Extract Job Title - Example selector (VERIFY THIS)
            title_element = card.find('a', {'data-automation': 'jobTitle'})
            title = title_element.text.strip() if title_element else 'N/A'

            # Extract Company Name - Example selector (VERIFY THIS)
            company_element = card.find('a', {'data-automation': 'jobCompany'})
            company = company_element.text.strip() if company_element else 'N/A'

            # Extract Salary - Example selector (VERIFY THIS)
            # Salary might be in different places or formats
            salary_element = card.find('span', {'data-automation': 'jobSalary'})
            salary = salary_element.text.strip() if salary_element else 'Not specified'

            # Extract Job Description Snippet - Example selector (VERIFY THIS)
            # Seek often shows snippets; full description requires visiting the job link
            description_element = card.find('span', {'data-automation': 'jobShortDescription'})
            description = description_element.text.strip() if description_element else 'N/A'

            # --- Email/Phone Extraction (More Complex) ---
            # These are rarely on the search results page.
            # Would typically require visiting the individual job link (found in title_element['href'])
            # and parsing that page. We'll skip this for now.
            email = 'N/A'
            phone = 'N/A'

            if title != 'N/A': # Only add if we found a title
                results.append({
                    'title': title,
                    'company': company,
                    'salary': salary,
                    'description': description,
                    # 'email': email, # Add later if implemented
                    # 'phone': phone, # Add later if implemented
                })

        print(f"Found {len(results)} jobs.") # Debugging print
        return results

    except requests.exceptions.RequestException as e:
        print(f"Error during request to Seek: {e}")
        return [] # Indicate failure due to network error
    except Exception as e:
        print(f"An unexpected error occurred during scraping: {e}")
        return [] # Indicate failure due to other errors

# Example usage (for testing the scraper directly)
if __name__ == '__main__':
    test_title = "python developer"
    scraped_jobs = scrape_seek(test_title)
    if scraped_jobs:
        print(f"\n--- Scraped Jobs for '{test_title}' ---")
        for job in scraped_jobs[:5]: # Print first 5 results
            print(f"Title: {job['title']}")
            print(f"Company: {job['company']}")
            print(f"Salary: {job['salary']}")
            print(f"Description: {job['description'][:100]}...") # Print snippet
            print("-" * 20)
    else:
        print(f"No jobs found or error occurred for '{test_title}'.")