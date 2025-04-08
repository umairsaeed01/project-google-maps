import json
  import os

   def search_clinics(suburb):
        print(f"Searching for clinics in {suburb}")

    if __name__ == "__main__":
        suburb_name = input("Enter a suburb name: ")
        search_clinics(suburb_name)
