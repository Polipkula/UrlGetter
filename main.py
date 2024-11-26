import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from urllib.robotparser import RobotFileParser
from pymongo import MongoClient
import time
import random

START_URLS = ["https://www.idnes.cz"]
MAX_URLS = 1000
MONGO_DB_NAME = "news_data"
MONGO_COLLECTION_NAME = "articles"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client[MONGO_DB_NAME]
collection = db[MONGO_COLLECTION_NAME]

def is_allowed(base_url, url):
    """Check if crawling is allowed by robots.txt."""
    rp = RobotFileParser()
    rp.set_url(f"{base_url}/robots.txt")
    try:
        rp.read()
        return rp.can_fetch("*", url)
    except Exception as e:
        print(f"Error reading robots.txt: {e}")
        return False

def is_valid_article_url(url):
    """Filter out non-article links."""
    if not url.startswith("https://www.idnes.cz"):
        return False
    if 'fotogalerie' in url or 'diskuze' in url or 'video' in url:
        return False
    return True

def collect_article_urls(base_url):
    """Collect article URLs from the base domain."""
    collected_urls = []
    to_visit = [base_url]
    visited_urls = set()

    while to_visit and len(collected_urls) < MAX_URLS:
        current_url = to_visit.pop(0)
        if current_url in visited_urls:
            continue
        visited_urls.add(current_url)

        if not is_allowed(base_url, current_url):
            print(f"Crawling disallowed for {current_url}. Skipping...")
            continue

        try:
            response = requests.get(current_url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            for link in soup.find_all('a', href=True):
                url = link['href']
                if not url.startswith("http"):
                    url = base_url + url

                if is_valid_article_url(url) and url not in visited_urls:
                    collected_urls.append(url)
                    to_visit.append(url)
        except Exception as e:
            print(f"Error collecting URLs from {current_url}: {e}")

    return collected_urls

def scrape_article(url):
    """Scrape article content from a URL."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'No title'
        category = soup.find('a', class_='category').get_text(strip=True) if soup.find('a', class_='category') else 'Unknown'
        comments = len(soup.find_all('div', class_='comment'))
        images = len(soup.find_all('img'))
        content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
        publication_date = soup.find('time')['datetime'] if soup.find('time') else 'Unknown'

        return {
            "url": url,
            "title": title,
            "category": category,
            "comments": comments,
            "images": images,
            "content": content,
            "publication_date": publication_date
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_multiple_urls_parallel(urls):
    """Scrape multiple articles using parallel threads."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(scrape_article, urls))
    return [res for res in results if res]

def save_to_mongo(data):
    """Save scraped data to MongoDB."""
    if not data:
        print("No data to save!")
        return
    collection.insert_many(data)
    print(f"Data successfully saved to MongoDB in {MONGO_COLLECTION_NAME} collection.")

def rate_limit():
    """Add a random delay between requests."""
    time.sleep(random.uniform(1, 3))

if __name__ == "__main__":
    all_collected_urls = []

    for start_url in START_URLS:
        print(f"Collecting URLs from {start_url}...")
        urls = collect_article_urls(start_url)
        all_collected_urls.extend(urls)
        print(f"Collected {len(urls)} URLs from {start_url}")

    print(f"Total collected URLs: {len(all_collected_urls)}")

    print("Scraping data from articles...")
    scraped_data = scrape_multiple_urls_parallel(all_collected_urls)

    print("Saving data to MongoDB...")
    save_to_mongo(scraped_data)
