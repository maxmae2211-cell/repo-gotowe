from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def test_google_search(driver):
    """Test Google search functionality"""
    try:
        # Navigate to Google
        driver.get("https://www.google.com")

        # Wait for search box and enter search term
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.send_keys("test query")

        # Click search button or press Enter
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "btnK"))
        )
        search_button.click()

        # Wait for results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search"))
        )

        print("Google search test completed successfully")
        return True

    except Exception as e:
        print(f"Google search test failed: {e}")
        return False

def test_example_site(driver):
    """Test example.com"""
    try:
        driver.get("https://www.example.com")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        print("Example site test completed successfully")
        return True

    except Exception as e:
        print(f"Example site test failed: {e}")
        return False

if __name__ == "__main__":
    driver = None
    try:
        driver = setup_driver()

        # Run tests
        test1_passed = test_google_search(driver)
        test2_passed = test_example_site(driver)

        if test1_passed and test2_passed:
            print("All Selenium tests passed!")
        else:
            print("Some Selenium tests failed!")

    except Exception as e:
        print(f"Selenium test setup failed: {e}")
    finally:
        if driver:
            driver.quit()
