import re
import os
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_normal_driver(headless=False, max_retries=3):
    try:
        options = webdriver.ChromeOptions()
        path = rf'{BASE_DIR}\chrome-dir'
        options.add_argument(f'--user-data-dir={path}')
        options.add_argument("--log-level=3")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")

        if not headless:
            options.add_argument("--start-maximized")
        else:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")

        # Initialize normal Chrome driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        time.sleep(2)  # Allow the browser to fully initialize

        # Additional fingerprinting tweaks (remove WebDriver flag)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        return driver

    except Exception as e:
        print(f"Error: {e}")
        if max_retries > 0:
            print(f"Retrying... Attempts left: {max_retries}")
            time.sleep(2)
            return get_normal_driver(headless=headless, max_retries=max_retries - 1)
        else:
            print("Max retries exceeded. Could not create the driver.")
            return None


def check_element_visibility_and_return_text(driver, by_locator):
    try:
        element = WebDriverWait(driver, 2).until(EC.visibility_of_element_located(by_locator))
        return element.text.strip()
    except:
        print(f"Element not found or not visible: {by_locator}")
        return ''

def check_element_visibility_and_return_href(driver, by_locator):
    try:
        element = WebDriverWait(driver, 2).until(EC.visibility_of_element_located(by_locator))
        return element.get_attribute("href").strip()
    except:
        print(f"URL not found or not visible: {by_locator}")
        return ''


def create_xpath_1(title):
    return f"//h5[text()= '{title}']/parent::div//ul/li"


def get_output_file_name(query):
    match = re.search(r'trefwoord=([^&]+)', query)
    if match:
        output_file_name = 'vdab_' + match.group(1).replace('%20', '_') + '_data.csv'
    else:
        output_file_name = 'vdab_job_data.csv'
    return output_file_name


def shorten_vdab_url(url):
    pattern = r'(https://www\.vdab\.be/vindeenjob/vacatures/\d+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None
