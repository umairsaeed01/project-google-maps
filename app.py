from flask import Flask, render_template, request, send_file
import csv
import os # Needed for checking if file exists for download
from scraper import scrape_seek

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    """Renders the main page."""
    return render_template('index.html', results=None)

@app.route('/search', methods=['POST'])
def search():
    """Handles the job search form submission."""
    job_title = request.form.get('job_title')
    results = []
    error_message = None

    if not job_title:
        error_message = "Please enter a job title."
    else:
        try:
            print(f"Starting scrape for: {job_title}") # Add print statement for debugging
            results = scrape_seek(job_title)
            if results:
                 save_to_csv(results, 'seek_jobs.csv')
            else:
                 print("No results found or error during scraping.")
                 # Optionally set an error message if scrape_seek returns empty due to error/block
                 if not error_message: # Avoid overwriting existing errors
                     # Check scraper.py logs for specific reason (e.g., CAPTCHA)
                     # For now, a generic message if results are empty
                     error_message = "No jobs found or an error occurred during scraping. Check console logs."

        except Exception as e:
            error_message = f"An error occurred: {e}"
            print(f"Error during search: {e}") # Add print statement for debugging

    return render_template('index.html', results=results, error=error_message, search_term=job_title)

def save_to_csv(data, filename):
    """Saves the scraped data to a CSV file."""
    if not data:
        return # Don't create an empty file

    # Define the headers based on the keys of the first dictionary, if data exists
    headers = data[0].keys()

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        print(f"Data successfully saved to {filename}")
    except IOError as e:
        print(f"Error saving data to CSV: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CSV saving: {e}")

# Route to download the CSV file
@app.route('/download_csv')
def download_csv():
    """Provides the generated CSV file for download."""
    csv_path = "seek_jobs.csv"
    if os.path.exists(csv_path):
        try:
            return send_file(csv_path, as_attachment=True)
        except Exception as e:
            print(f"Error sending file: {e}")
            return "Error downloading file.", 500
    else:
        return "CSV file not found. Please perform a search first.", 404


if __name__ == '__main__':
    app.run(debug=True) # Enable debug mode for development