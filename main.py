import requests
from bs4 import BeautifulSoup
import csv
from concurrent.futures import ThreadPoolExecutor

START_URLS = [
    "https://www.idnes.cz"
]

MAX_URLS = 1000  
OUTPUT_FILE = "scraped_data.csv"

def collect_article_urls(base_url):
    """Sbírá odkazy na články z dané domény."""
    collected_urls = []
    to_visit = [base_url]
    visited_urls = set()

    while to_visit and len(collected_urls) < MAX_URLS:
        current_url = to_visit.pop(0)
        if current_url in visited_urls:
            continue
        visited_urls.add(current_url)

        try:
            response = requests.get(current_url)
            response.raise_for_status()


            if response.status_code == 403:
                print(f"Access denied to {current_url}, skipping...")
                continue  
            if response.status_code == 401:
                print(f"Login required for {current_url}, skipping...")
                continue  

            soup = BeautifulSoup(response.text, 'html.parser')

            for link in soup.find_all('a', href=True):
                url = link['href']
                if base_url in url: 
                    collected_urls.append(url)
                    to_visit.append(url)
        except Exception as e:
            print(f"Error collecting URLs from {current_url}: {e}")

    return collected_urls  


def scrape_article(url):
    """Stahuje obsah článku."""
    try:
        response = requests.get(url)
        response.raise_for_status()


        if response.status_code == 403:
            print(f"Access denied to {url}, skipping...")
            return None 
        if response.status_code == 401:
            print(f"Login required for {url}, skipping...")
            return None 

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
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(scrape_article, urls))
    return [res for res in results if res]

def save_to_csv(data, filename):
    if not data:
        print("No data to save!")
        return

    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"Data successfully saved to {filename}.")

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

    print("Saving data to CSV...")
    save_to_csv(scraped_data, OUTPUT_FILE)