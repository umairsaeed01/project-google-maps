try:
  import requests
  print("requests is already installed.")
except ImportError:
  print("requests is not installed.")
 

try:
  from bs4 import BeautifulSoup
  print("BeautifulSoup is already installed.")
except ImportError:
  print("BeautifulSoup is not installed.")