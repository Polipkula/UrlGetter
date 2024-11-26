import requests
from bs4 import BeautifulSoup
import csv
from concurrent.futures import ThreadPoolExecutor

START_URLS = [
    "https://www.novinky.cz", 
    "https://www.idnes.cz",  
    "https://www.ctk.cz"
]

def collect_urls(start_url, max_urls=1000):
    collected_urls = set()
    visited_urls = set()
    to_visit = [start_url]

    while to_visit and len(collected_urls) < max_urls:
        current_url = to_visit.pop(0)
        if current_url in visited_urls:
            continue

        try:
            response = requests.get(current_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            for link in soup.find_all('a', href=True):
                url = link['href']
                if url.startswith('/'):
                    url = start_url + url
                if url not in collected_urls and start_url in url:
                    collected_urls.add(url)
                    to_visit.append(url)

            visited_urls.add(current_url)
        except Exception as e:
            print(f"Error collecting URLs from {current_url}: {e}")

    return list(collected_urls)

def scrape_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'No title'
        category = soup.find('a', class_='category').get_text(strip=True) if soup.find('a', class_='category') else 'Unknown'
        comments = len(soup.find_all('div', class_='comment'))
        images = len(soup.find_all('img'))
        content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
        publication_date = soup.find('time')['datetime'] if soup.find('time') else 'Unknown'

        return {
            'url': url,
            'title': title,
            'category': category,
            'comments': comments,
            'images': images,
            'content': content,
            'publication_date': publication_date
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_multiple_urls(urls):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(scrape_article, urls))
    return [res for res in results if res]

def save_to_csv(data, filename='scraped_data.csv'):
    if not data:
        print("No data to save!")
        return

    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['url', 'title', 'category', 'comments', 'images', 'content', 'publication_date'])
        writer.writeheader()
        writer.writerows(data)
    print(f"Data successfully saved to {filename}.")

if __name__ == "__main__":
    all_urls = []
    for start_url in START_URLS:
        print(f"Collecting URLs from {start_url}...")
        urls = collect_urls(start_url, max_urls=1000)
        print(f"Collected {len(urls)} URLs from {start_url}.")
        all_urls.extend(urls)

    print(f"Total collected URLs: {len(all_urls)}")
    print("Scraping data from articles...")
    scraped_data = scrape_multiple_urls(all_urls)

    print("Saving data to CSV...")
    save_to_csv(scraped_data)