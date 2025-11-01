import csv
import os
import requests
from bs4 import BeautifulSoup

def scrape_reviews(product_name):
    # Path to product's links file
    links_file = f"data/{product_name}/links.csv"
    reviews_file = f"reviews/{product_name}/reviews.csv"

    # Ensure reviews folder exists
    os.makedirs(os.path.dirname(reviews_file), exist_ok=True)

    # Read all links
    with open(links_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        links = list(reader)

    all_reviews = []

    for row in links:
        url = row[0]
        print(f"Scraping: {url}")
        try:
            page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(page.text, "html.parser")

            # Example: Amazon review div (adjust later for other sites)
            reviews = soup.find_all("span", {"data-hook": "review-body"})
            for r in reviews:
                text = r.get_text(strip=True)
                if text:
                    all_reviews.append([text])

        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")

    # Save reviews
    with open(reviews_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Review"])
        writer.writerows(all_reviews)

    print(f"✅ Saved {len(all_reviews)} reviews to {reviews_file}")