import subprocess

try:
    subprocess.run(["/Users/umairsaeed/anaconda3/bin/python3", "/Users/umairsaeed/Documents/ai/project\ google\ maps/scrape_seek.py"], check=True)
except Exception as e:
    print(f"Error: {e}")