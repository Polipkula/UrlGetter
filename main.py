import requests
from bs4 import BeautifulSoup
from collections import deque
import json
import time
from urllib.parse import urljoin

# Function to download the page content
def fetch_page(url):
    try:
        # Send a GET request to the URL with a timeout of 10 seconds
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error if the request failed
        return response.text  # Return the page content
    except requests.RequestException as e:
        # Print an error message if there was an issue fetching the page
        print(f"Error fetching {url}: {e}")
        return None

# Function to parse the page content
def parse_page(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    article_data = {}
    
    # Extract the title of the article, assuming it's in an <h1> tag
    title_tag = soup.find('h1')
    if title_tag:
        article_data['title'] = title_tag.get_text(strip=True)
    
    # Extract the date of the article, assuming it's in a <time> tag
    date_tag = soup.find('time')
    if date_tag:
        article_data['date'] = date_tag.get('datetime')
    
    # Extract the full article content from the div with id="content"
    content_div = soup.find('div', id='content')
    if content_div:
        article_data['content'] = content_div.get_text(strip=True)
    
    # Count the number of images in the article
    img_tags = content_div.find_all('img') if content_div else []
    article_data['img_count'] = len(img_tags)

    # Find all links on the page (anchor tags with href attributes)
    links = [urljoin(base_url, a.get('href')) for a in soup.find_all('a', href=True)]
    return article_data, links

# Function to save the data to a JSON file
def save_data(data, filename='articles.json'):
    with open(filename, 'a', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        f.write('\n')  # Write each JSON object on a new line

# Main function to run the crawler
def crawl(start_url, max_pages=100):
    queue = deque([start_url])  # Queue to manage URLs to be visited
    visited = set()  # Set to keep track of visited URLs
    
    while queue and len(visited) < max_pages:
        current_url = queue.popleft()  # Get the next URL from the queue
        if current_url in visited:
            continue  # Skip if the URL has already been visited

        print(f"Crawling: {current_url}")
        html = fetch_page(current_url)  # Fetch the page content
        if html is None:
            continue  # Skip to the next URL if the page couldn't be fetched

        article_data, links = parse_page(html, current_url)  # Parse the page content
        if article_data:
            save_data(article_data)  # Save the extracted article data

        visited.add(current_url)  # Mark the current URL as visited
        for link in links:
            # Add new links to the queue if they haven't been visited
            if link not in visited and link.startswith(('http://', 'https://')):
                queue.append(link)
        
        time.sleep(1)  # Pause for 1 second between requests to avoid overwhelming the server

if __name__ == "__main__":
    # List of starting URLs for the crawler
    start_urls = [
        "https://www.idnes.cz"
    ]
    for url in start_urls:
        crawl(url, max_pages=500)  # Start crawling each URL with a maximum of 500 pages
