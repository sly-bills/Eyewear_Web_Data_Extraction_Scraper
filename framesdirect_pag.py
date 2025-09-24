import json
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def setup_webdriver():
    """Sets up and returns a configured Selenium WebDriver."""
    print("Setting up WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.265 Safari/537.36"
    )
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def extract_product_data(html_source):
    """Parses the HTML source and extracts product data."""
    soup = BeautifulSoup(html_source, "html.parser")
    product_holders = soup.find_all('div', class_='prod-holder')
    
    products_to_add = []

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
                # Current Price
                current_price_tag = price_cnt.find('div', class_='prod-aslowas')
                current_price = current_price_tag.text.strip() if current_price_tag else "N/A"

                # Former Price
                former_price_tag = price_cnt.find('div', class_='prod-catalog-retail-price')
                former_price = former_price_tag.text.strip() if former_price_tag else "N/A"
            else:
                original_price = former_price = "N/A"

        discount_tag = holder.find('div', class_='frame-discount')
        discount = discount_tag.text.strip() if discount_tag else "N/A"

        data = {
                "brand": brand,
                "name": name,
                "current_price": current_price,
                "former_price": former_price,
                "discount": discount
        }

        # Append data to the list
        products_to_add.append(data)
    
    return products_to_add


def save_data_to_files(data, json_filename='./extracted_data/framesdirect_data.json', csv_filename='./extracted_data/framesdirect_data.csv'):
    """Saves the extracted data to both JSON and CSV files."""
    if not data:
        print("No data to save.")
        return

    # Deduplicate the data
    final_data = [dict(t) for t in {tuple(d.items()) for d in data}]

    # Save to JSON
    with open(json_filename, 'w') as json_file:
        json.dump(final_data, json_file, indent=4)
    print(f"Data successfully saved to {json_filename}.")

    # Save to CSV
    if final_data:
        keys = final_data[0].keys()
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
            dict_writer = csv.DictWriter(csv_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(final_data)
        print(f"Data successfully saved to {csv_filename}.")

# Main execution flow
if __name__ == "__main__":
    driver = setup_webdriver()
    base_url = "https://www.framesdirect.com"
    url = f"{base_url}/eyeglasses?"
    all_products_data = []

    try:
        while url:
            print(f"Visiting URL: {url}")
            driver.get(url)
            
            try:
                print("Waiting for product holders to load...")
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "fd-cat"))
                )
            except Exception as e:
                print(f"Error waiting for page to load: {e}")
                driver.quit()
                exit()

            # Get page source and extract data
            html_source = driver.page_source
            products_on_page = extract_product_data(html_source)
            all_products_data.extend(products_on_page)
            print(f"Extracted {len(products_on_page)} products. Total so far: {len(all_products_data)}")

            # Find the next page link
            soup = BeautifulSoup(html_source, "html.parser")
            next_link_element = soup.find('a', class_='ml-1', attrs={'href': True})

            if next_link_element and 'href' in next_link_element.attrs:
                next_url_path = next_link_element['href']
                url = f"{base_url}{next_url_path}"
                print(f"Found next page URL: {url}")
                # Save the incremental progress
                save_data_to_files(all_products_data)
            else:
                print("No more pages found.")
                url = None # End the loop
                
        # Final save after the loop completes
        save_data_to_files(all_products_data)

    finally:
        driver.quit()
        print("\nScraping complete. WebDriver closed.")
