from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import requests
import os
import re


def scrape_tweet(tweet_url):
    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    print(f"[+] Loading tweet: {tweet_url}")
    driver.get(tweet_url)
    time.sleep(5)  # Let JS load

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # --- Extract Post Text and Hashtags (Improved Version) ---
    tweet_text = ""
    hashtags = []

    # Try common meta properties for description
    meta_tags = soup.find_all('meta')
    for tag in meta_tags:
        if tag.get('property') in ['og:title', 'twitter:description']:
            tweet_text = tag.get('content', '').strip()
            break

    # Extract hashtags using regex
    hashtags = re.findall(r'#\w+', tweet_text)

    print(f"[+] Tweet Text:\n{tweet_text}\n")
    print(f"[+] Hashtags: {hashtags}\n")

    # --- Extract Images ---
    # images = []
    # for img_tag in soup.find_all('img'):
    #     src = img_tag.get('src')
    #     if src and 'media' in src and src not in images:
    #         images.append(src)
    #
    # print(f"[+] Found {len(images)} image(s).")
    #
    # # --- Save Images ---
    # folder = f"tweet_images"
    # os.makedirs(folder, exist_ok=True)
    #
    # for idx, img_url in enumerate(images):
    #     try:
    #         # Force full-resolution version
    #         high_res_url = re.sub(r'&name=\w+$', '&name=orig', img_url)
    #         img_data = requests.get(high_res_url).content
    #         img_name = f"image_{idx + 1}.png"
    #         img_path = os.path.join(folder, img_name)
    #         with open(img_path, 'wb') as f:
    #             f.write(img_data)
    #         print(f"[+] Saved {img_name}")
    #     except Exception as e:
    #         print(f"[!] Failed to download image {img_url}: {e}")


# Example Tweet URL
tweet_url = "https://x.com/WE_NMIXX/status/1935911245611516236"  # Replace with your link
scrape_tweet(tweet_url)
