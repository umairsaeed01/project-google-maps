from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
 

path = ChromeDriverManager().install()
service = Service(executable_path=path)
driver = webdriver.Chrome(service=service)
driver.quit()
print("ChromeDriver has been installed.")