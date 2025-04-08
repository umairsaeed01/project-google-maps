# view_csv_server.py
import http.server
import socketserver
import csv
import io
import html # Import the html module for escaping

PORT = 8000
CSV_FILE = 'seek_ai_jobs_melbourne.csv'

class CSVRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            try:
                with open(CSV_FILE, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    # Use io.StringIO to build the HTML string efficiently
                    html_output = io.StringIO()
                    html_output.write("<!DOCTYPE html>\n")
                    html_output.write("<html>\n<head>\n<meta charset=\"UTF-8\">\n<title>Seek Job Data</title>\n")
                    # Add some basic styling
                    html_output.write("<style>\n")
                    html_output.write("body { font-family: sans-serif; margin: 20px; }\n")
                    html_output.write("table { border-collapse: collapse; width: 100%; table-layout: fixed; }\n") # Fixed layout helps with column width
                    html_output.write("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n")
                    html_output.write("th { background-color: #f2f2f2; position: sticky; top: 0; z-index: 1; }\n") # Sticky header
                    html_output.write("tr:nth-child(even) { background-color: #f9f9f9; }\n")
                    # Adjust column widths as needed - Example: make description wider
                    html_output.write("th:nth-child(1), td:nth-child(1) { width: 15%; }") # Job Title
                    html_output.write("th:nth-child(2), td:nth-child(2) { width: 15%; }") # Company Name
                    html_output.write("th:nth-child(3), td:nth-child(3) { width: 10%; }") # Location
                    html_output.write("th:nth-child(11), td:nth-child(11) { width: 30%; }") # Full Job Description (adjust index if headers change)
                    html_output.write("td { vertical-align: top; word-wrap: break-word; }") # Wrap long text
                    html_output.write("pre { white-space: pre-wrap; word-wrap: break-word; margin: 0; font-family: inherit; }") # Preserve formatting in description
                    html_output.write("\n</style>\n</head>\n<body>\n")
                    html_output.write(f"<h1>Job Data from {CSV_FILE}</h1>\n")
                    html_output.write("<div style='overflow-x: auto;'>\n") # Add horizontal scroll if needed
                    html_output.write("<table>\n")

                    # Read header row
                    try:
                        header = next(reader)
                        html_output.write("<thead><tr>")
                        for col_name in header:
                            # Escape header content to prevent HTML injection
                            html_output.write(f"<th>{html.escape(col_name)}</th>")
                        html_output.write("</tr></thead>\n")
                        description_col_index = header.index("Full Job Description") if "Full Job Description" in header else -1

                    except StopIteration:
                        self.send_error(500, f"Error: CSV file '{CSV_FILE}' appears to be empty or has no header.")
                        return


                    # Read data rows
                    html_output.write("<tbody>\n")
                    for row_num, row in enumerate(reader):
                         # Ensure row has the same number of columns as header
                         if len(row) != len(header):
                              print(f"Warning: Skipping row {row_num + 2} due to mismatched column count ({len(row)} columns, expected {len(header)}). Row data: {row}")
                              continue # Skip malformed rows

                         html_output.write("<tr>")
                         for i, cell in enumerate(row):
                             # Escape cell content to prevent HTML injection
                             escaped_cell = html.escape(cell)
                             # Check if it's the 'Full Job Description' column
                             if i == description_col_index:
                                 html_output.write(f"<td><pre>{escaped_cell}</pre></td>") # Use <pre> for description
                             else:
                                 html_output.write(f"<td>{escaped_cell}</td>")
                         html_output.write("</tr>\n")
                    html_output.write("</tbody>\n")

                    html_output.write("</table>\n</div>\n</body>\n</html>")

                    # Send response
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(html_output.getvalue().encode('utf-8'))

            except FileNotFoundError:
                self.send_error(404, f"Error: File not found - {CSV_FILE}")
            except Exception as e:
                 self.send_error(500, f"Error reading or parsing CSV: {e}")

        else:
            # Fallback to default behavior for other paths (e.g., serving other files)
            super().do_GET()

Handler = CSVRequestHandler

# Ensure the server binds to localhost only for security unless wider access is needed
server_address = ('localhost', PORT)
with socketserver.TCPServer(server_address, Handler) as httpd:
    print(f"Serving CSV data from '{CSV_FILE}' at http://{server_address[0]}:{server_address[1]}")
    print("Press Ctrl+C to stop the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.shutdown()