import logging
import traceback
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1200,800")

try:
    logger.info("Installing Edge driver via webdriver-manager")
    driver_path = EdgeChromiumDriverManager().install()
    logger.info(f"Driver installed at: {driver_path}")
    service = Service(driver_path)

    logger.info("Starting Edge browser")
    with webdriver.Edge(service=service, options=opts) as driver:
        logger.info("Navigating to https://example.com")
        driver.get("https://example.com")
        print("Title:", driver.title)
        print("Current URL:", driver.current_url)
        logger.info("Selenium run completed successfully")
except Exception:
    print("Exception during Selenium run:")
    traceback.print_exc()
