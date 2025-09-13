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


# Visit the target webpage
target_url = "https://www.framesdirect.com/eyeglasses"
print(f"Visiting webpage: {target_url}")
driver.get(target_url)

# Further Instruction: Wait for JS to load the files. 
try:
    print("Waiting for products to load...")
    WDW(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'fd-cat'))
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
eyeglasses_data = []
seen = set()  # to track duplicates based on (brand, product_name)


# Locate all product files and extract relevant data
product_holders = page.find_all('div', class_='prod-holder')
print(f"Found {len(product_holders)} products. Extracting data...")

for holder in product_holders:
    prod_title = holder.find('div', class_='prod-title')

    if prod_title:
        brand_tag = prod_title.find('div', class_='catalog-name')
        brand = brand_tag.text.strip() if brand_tag else "N/A"

        name_tag = prod_title.find('div', class_='product_name')
        name = name_tag.text.strip() if name_tag else "N/A"

        # For Price
        price_cnt = holder.find('div', class_='prod-price-wrap')
        if price_cnt:
            # Original Price
            orig_price_tag = price_cnt.find('div', class_='prod-aslowas')
            original_price = orig_price_tag.text.strip() if orig_price_tag else "N/A"

            # Former Price
            former_price_tag = price_cnt.find('div', class_='prod-catalog-retail-price')
            former_price = former_price_tag.text.strip() if former_price_tag else "N/A"
        else:
            original_price = former_price = "N/A"

    discount_tag = holder.find('div', class_='frame-discount')
    discount = discount_tag.text.strip() if discount_tag else "N/A"

    # Create unique key (Brand + Name)
    unique_key = (brand, name) # Checks for duplicates

    if unique_key not in seen:
        seen.add(unique_key)  # mark as seen
    data = {
            "brand": brand,
            "name": name,
            "original_price": original_price,
            "former_price": former_price,
            "discount": discount
    }

    # Append data to the list
    eyeglasses_data.append(data)


# Step 3 - Data Storage and Finalization
# Save the data to a CSV file
column_name = eyeglasses_data[0].keys() # Get Column names from the first dictionary
with open('framesdirectdotcom_data.csv', mode='w', newline='', encoding='utf-8') as csv_file: # Open up the file with context manager
    dict_writer = csv.DictWriter(csv_file, fieldnames=column_name) # Create a DictWriter object
    dict_writer.writeheader() # Write the header row
    dict_writer.writerows(eyeglasses_data) # Write all the data rows
print (f"Saved {len(eyeglasses_data)} records to CSV file")

# Save the data to a JSON file
with open("framesdirectdotcom.json", mode='w') as json_file:
    json.dump(eyeglasses_data, json_file, indent=4)
print(f"Saved {len(eyeglasses_data)} records to JSON file")

# Close the browser and quit the driver
driver.quit()
print("End of Web Scraping")