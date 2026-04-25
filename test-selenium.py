from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Przykładowy test Selenium: wyszukiwanie Google
def test_google_search():
    driver = webdriver.Chrome()
    driver.get("https://www.google.com")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys("Taurus performance testing")
    search_box.send_keys(Keys.RETURN)
    time.sleep(2)
    assert "Taurus" in driver.title
    driver.quit()

if __name__ == "__main__":
    test_google_search()
