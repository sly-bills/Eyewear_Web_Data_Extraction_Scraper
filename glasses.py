# Libraries Used
import csv
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Step 1 - Configuration and Data Fetching
# Setup Selenium and WebDriver
print("Setting up the Web Driver...")
chrome_option = Options()
chrome_option.add_argument('--headless')
chrome_option.add_argument('--disable-gpu')
chrome_option.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.265 Safari/537.36"
)
print("Done setting up..")

# Install the chrome driver (This is a one-time setup)
print("Installing Chrome WebDriver...")
service = Service(ChromeDriverManager().install())
print("final setup")
driver = webdriver.Chrome(service=service, options=chrome_option)
print("Done")

# Make connection and get URL content
target_url = "https://www.glasses.com/gl-us/eyeglasses"
print(f"Visiting webpage: {target_url}")
driver.get(target_url)

# Further Instruction: Wait for JS to load the files. 
try:
    print("Waiting for products to load...")
    WDW(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'catalog-page'))
    )
    print("Done...Proceed to parse the data")
except (TimeoutError, Exception) as e:
    print(f"Error, waiting for {target_url}: {e}")
    driver.quit()
    print("closed")


# Step 2 - Data Parsing and Extraction
# Get page source and parse using BeautifulSoup
content = driver.page_source
page = BeautifulSoup(content, 'html.parser')

# Temporary storage for the extracted data
glasses_data = []
seen = set()  # to track duplicates

# Locate all product files and extract the data for each product. 
product_tiles = page.find_all('a', class_='product-tile')
print(f"Found {len(product_tiles)} products")

for tile in product_tiles:
    product_info = tile.find('div', class_='product-info')

    if product_info:
        brand_tag = product_info.find('div', class_='product-brand')
        brand = brand_tag.text.strip() if brand_tag else 'None' # Product Brand

        name_tag = product_info.find('div' , class_='product-code')
        name = name_tag.text.strip() if name_tag else 'None' # Product Name

        # For Book Status
        badge_cnt = tile.find('div', class_='product-top')
        if badge_cnt:
            # Best Seller/New Arrival/Kids
            first_status_tag = badge_cnt.find('div', class_='product-badge first-badge')
            first_book_status = first_status_tag.text.strip() if first_status_tag else 'None'

            # Sustainable/Universal Fit
            second_status_tag = badge_cnt.find('div', class_='product-badge second-badge')
            second_book_status = second_status_tag.text.strip() if second_status_tag else 'None'
        else:
            first_book_status = second_book_status = 'None'



        # For Price
        price_cnt = product_info.find('div', class_='product-prices')
        if price_cnt:
            # Former Price
            former_price_tag = price_cnt.find('div', class_='product-list-price')
            former_price = former_price_tag.text.strip() if former_price_tag else 'None'

            # Current_price
            current_price_tag = price_cnt.find('div', class_='product-offer-price')
            current_price = current_price_tag.text.strip() if current_price_tag else 'None'
        else:
            former_price = current_price = 'None'
    else:
        brand = name = price = former_price = first_book_status = second_book_status = current_price = None
        
        # Automatically applies missing value, if the product info is not available.

    discount_tag = tile.find('div', class_='product-badge discount-badge thirty')
    discount = discount_tag.text.strip() if discount_tag else 'None' 

    # Create unique key (Brand + Name)
    unique_key = (brand, name) # Checks for duplicates

    # Only save if not already seen
    if unique_key not in seen:
        seen.add(unique_key)  # mark as seen
    data = {
        'Brand': brand,
        'Name': name,
        'First Book Status': first_book_status,
        'Second Book Status': second_book_status,
        'Former Price': former_price,
        'Current Price': current_price,
        'Discount Percentage': discount
    }

    # Append data to the list
    glasses_data.append(data)


# Step 3 - Data Storage and Finalization
# Save the data to a CSV file
column_name = glasses_data[0].keys() # Get Column names from the first dictionary
with open('glassesdotcom_data.csv', mode='w', newline='', encoding='utf-8') as csv_file: # Open up the file with context manager
    dict_writer = csv.DictWriter(csv_file, fieldnames=column_name) # Create a DictWriter object
    dict_writer.writeheader() # Write the header row
    dict_writer.writerows(glasses_data) # Write all the data rows
print (f"Saved {len(glasses_data)} records to CSV file")

# Save the data to a JSON file
with open("glassesdotcom.json", mode='w') as json_file:
    json.dump(glasses_data, json_file, indent=4)
print(f"Saved {len(glasses_data)} records to JSON file")

# Close the browser and quit the driver
driver.quit()
print("End of Web Scraping")

