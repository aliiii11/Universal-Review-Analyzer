# src/fetch.py
from ddgs import DDGS
import csv, os, re, random, json
from collections import Counter
import requests
from io import BytesIO
from PIL import Image, ImageTk   # ✅ Needed for product images

TRUSTED_SITES = [
    "flipkart.com", "gsmarena.com", "techradar.com", "tomsguide.com",
    "theverge.com", "amazon.in", "91mobiles.com", "gadgets360.com",
    "smartprix.com", "pricebaba.com", "indiatoday.in"
]

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
COLLECTED_PATH = os.path.join(DATA_DIR, "collected_reviews.csv")

def _ensure_collected_file():
    if not os.path.exists(COLLECTED_PATH):
        with open(COLLECTED_PATH, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(["Product", "Site", "URL", "Review"])

def search_product_reviews(product_name: str, max_results: int = 50):
    query = f"{product_name} reviews"
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            url = r.get("href") or r.get("url")
            snippet = (r.get("body") or "").replace("\n", " ").strip()
            if url and any(site in url for site in TRUSTED_SITES):
                results.append({"url": url, "snippet": snippet})
    return results

def save_reviews(product_name: str, results: list[dict]):
    _ensure_collected_file()
    existing = set()
    with open(COLLECTED_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            existing.add(row["URL"])

    saved, skipped = 0, 0
    with open(COLLECTED_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for r in results:
            if r["url"] in existing:
                skipped += 1
                continue
            site = next((s for s in TRUSTED_SITES if s in r["url"]), "Unknown")
            w.writerow([product_name, site, r["url"], r["snippet"]])
            saved += 1
    return saved, skipped

def fetch_and_save_reviews(product_name: str, max_results: int = 50):
    results = search_product_reviews(product_name, max_results=max_results)
    saved, skipped = save_reviews(product_name, results)
    return {"saved": saved, "skipped": skipped, "total_found": len(results)}

# ---------- Trending ----------
_BRANDS = [
    "Apple", "Samsung", "Xiaomi", "OnePlus", "Google", "Nothing",
    "Realme", "Oppo", "Vivo", "Motorola", "Sony", "Asus"
]

def _extract_models_from_title(title: str):
    title = re.sub(r"\s+\|.*$", "", title)
    title = re.sub(r"-\s*GSMArena.*$", "", title)
    parts = re.split(r"[–—\-:|]", title)
    title = parts[0].strip()
    tokens = re.findall(r"[A-Z][A-Za-z]+(?:\s+[A-Za-z0-9]+){0,3}", title)
    out = []
    for t in tokens:
        if any(b in t for b in _BRANDS) and len(t.split()) <= 5:
            out.append(t.strip())
    return out

def get_trending_products(limit: int = 8):
    try:
        titles = []
        queries = [
            "best smartphones 2025",
            "trending phones 2025",
            "top phones 2025 gsmarena",
            "best phones review roundup"
        ]
        with DDGS() as ddgs:
            for q in queries:
                for r in ddgs.text(q, max_results=20):
                    t = r.get("title") or ""
                    if t:
                        titles.append(t)

        candidates = []
        for t in titles:
            candidates += _extract_models_from_title(t)

        seen, models = set(), []
        for m in candidates:
            k = m.lower()
            if k not in seen:
                seen.add(k)
                models.append(m)

        if models:
            return models[:limit]

    except Exception:
        pass

    try:
        _ensure_collected_file()
        counts = Counter()
        with open(COLLECTED_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("Product"):
                    counts[row["Product"]] += 1
        if counts:
            return [p for p, _ in counts.most_common(limit)]
    except Exception:
        pass

    fallback = [
        "iPhone 15", "Samsung Galaxy S24", "Google Pixel 9",
        "OnePlus 12", "Xiaomi 14", "Nothing Phone (2a)", "Realme GT 6", "Motorola Edge 50"
    ]
    return fallback[:limit]

# ---------- Product Info ----------
def get_product_info(product_name: str, max_images: int = 3):
    """
    Fetch product info: images + a Best Buy shopping link.
    Tries DuckDuckGo first, then fallback to GSMArena / Amazon / Flipkart.
    Returns dict with name, buy_url, images.
    """
    images, buy_url = [], None

    with DDGS() as ddgs:
        # --- Best Buy link ---
        for r in ddgs.text(f"{product_name} buy site:amazon.in OR site:flipkart.com", max_results=5):
            u = r.get("href") or r.get("url")
            if u and ("amazon" in u or "flipkart" in u):
                buy_url = u
                break

        # --- Try DuckDuckGo Images ---
        for r in ddgs.images(product_name, max_results=max_images):
            if r.get("image"):
                try:
                    img_data = requests.get(r["image"], timeout=5).content
                    img = Image.open(BytesIO(img_data))
                    img.thumbnail((200, 200))
                    images.append(ImageTk.PhotoImage(img))
                except Exception:
                    pass

    # --- Fallback: GSMArena ---
    if not images:
        try:
            for r in ddgs.images(f"{product_name} site:gsmarena.com", max_results=max_images):
                if r.get("image"):
                    try:
                        img_data = requests.get(r["image"], timeout=5).content
                        img = Image.open(BytesIO(img_data))
                        img.thumbnail((200, 200))
                        images.append(ImageTk.PhotoImage(img))
                    except Exception:
                        pass
        except Exception:
            pass

    return {
        "name": product_name,
        "buy_url": buy_url,
        "images": images
    }
