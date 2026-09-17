from selenium import webdriver
from selenium.webdriver.edge.options import Options


def test_example_page():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,800")

    with webdriver.Edge(options=options) as driver:
        driver.get("https://example.com")
        assert driver.title == "Example Domain"
        assert driver.current_url == "https://example.com/"
