from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager # Added this import
import time

print("Starting Selenium test...")

options = Options()
options.add_argument("--headless")  # optional
options.add_argument("--no-sandbox")
# Add disable-dev-shm-usage, often helpful
options.add_argument("--disable-dev-shm-usage")
# Add a user agent
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


# Initialize Service using webdriver_manager
# The original code was missing the driver path or manager call for Service()
try:
    print("Initializing ChromeDriver service using webdriver-manager...")
    service = Service(ChromeDriverManager().install())
    print("Service initialized.")
except Exception as e:
    print(f"Error initializing ChromeDriver service: {e}")
    service = None # Ensure service is None if init fails

driver = None # Initialize driver to None
if service:
    try:
        print("Initializing WebDriver...")
        driver = webdriver.Chrome(service=service, options=options)
        print("WebDriver initialized.")

        print("Navigating to google.com...")
        driver.get("https://www.google.com")
        print("Navigation complete. Waiting...")
        time.sleep(2)
        print("Page title is:", driver.title)
        print("Test successful!")

    except Exception as e:
        print(f"An error occurred during WebDriver operation: {e}")

    finally:
        if driver:
            print("Quitting WebDriver...")
            driver.quit()
            print("WebDriver quit.")
        else:
            print("WebDriver was not initialized.")
else:
    print("Skipping WebDriver test as service initialization failed.")

print("Selenium test finished.")