"""
Homvyx Product Discovery Engine
Finds trending products on Amazon.com (US market) for affiliate content.
Uses Firecrawl for scraping + YouTube MCP for trend validation.
"""

import json
import os
import sys
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    AMAZON_BESTSELLERS, PRODUCT_FILTERS, AFFILIATE_TAG, AMAZON_BASE_URL
)


# ============================================================
# PRODUCT DATA EXTRACTION
# ============================================================

def build_amazon_search_urls(keywords: list[str]) -> list[str]:
    """Build Amazon search URLs for product discovery."""
    urls = []
    for kw in keywords:
        query = kw.replace(" ", "+")
        urls.append(f"{AMAZON_BASE_URL}/s?k={query}&ref=nb_sb_noss")
    return urls


DEFAULT_SEARCH_KEYWORDS = [
    "kitchen gadgets 2026",
    "home organization must haves",
    "kitchen tools best sellers",
    "cleaning gadgets home",
    "cooking gadgets tiktok viral",
    "bathroom organization ideas",
    "pantry organization containers",
    "kitchen storage solutions",
    "home improvement gadgets",
    "smart kitchen accessories",
]


def parse_product_from_scrape(raw_data: dict) -> dict | None:
    """Parse a product from Firecrawl scraped data into our format."""
    try:
        name = raw_data.get("name", raw_data.get("title", ""))
        if not name:
            return None

        price_str = raw_data.get("price", "0")
        if isinstance(price_str, str):
            price = float(re.sub(r'[^\d.]', '', price_str) or "0")
        else:
            price = float(price_str)

        rating_str = raw_data.get("rating", "0")
        if isinstance(rating_str, str):
            rating = float(re.sub(r'[^\d.]', '', rating_str) or "0")
        else:
            rating = float(rating_str)

        reviews_str = raw_data.get("reviews", raw_data.get("reviews_count", "0"))
        if isinstance(reviews_str, str):
            reviews = int(re.sub(r'[^\d]', '', reviews_str) or "0")
        else:
            reviews = int(reviews_str)

        asin = raw_data.get("asin", "")
        url = raw_data.get("url", raw_data.get("link", ""))

        # Build affiliate link
        if asin:
            affiliate_link = f"https://amazon.com/dp/{asin}?tag={AFFILIATE_TAG}"
        elif url:
            separator = "&" if "?" in url else "?"
            affiliate_link = f"{url}{separator}tag={AFFILIATE_TAG}"
        else:
            affiliate_link = ""

        # Apply filters
        if price < PRODUCT_FILTERS["min_price"] or price > PRODUCT_FILTERS["max_price"]:
            return None
        if rating < PRODUCT_FILTERS["min_rating"]:
            return None
        if reviews < PRODUCT_FILTERS["min_reviews"]:
            return None

        return {
            "name": name.strip(),
            "price": price,
            "rating": rating,
            "reviews_count": reviews,
            "amazon_url": url,
            "affiliate_link": affiliate_link,
            "category": raw_data.get("category", "kitchen"),
            "image_urls": json.dumps(raw_data.get("images", [])),
            "features": raw_data.get("features", raw_data.get("description", "")),
            "status": "pending",
            "trend_score": 0,
        }
    except Exception as e:
        print(f"  ⚠️  Parse error: {e}")
        return None


# ============================================================
# FIRECRAWL EXTRACTION SCHEMA
# ============================================================

AMAZON_EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Product title"},
                    "price": {"type": "string", "description": "Current price in USD"},
                    "rating": {"type": "string", "description": "Star rating out of 5"},
                    "reviews": {"type": "string", "description": "Number of reviews"},
                    "asin": {"type": "string", "description": "Amazon ASIN code"},
                    "url": {"type": "string", "description": "Product page URL"},
                    "images": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Product image URLs"
                    },
                    "features": {"type": "string", "description": "Key product features"},
                    "category": {"type": "string", "description": "Product category"},
                },
            },
        }
    },
}


# ============================================================
# YOUTUBE TREND VALIDATION
# ============================================================

YOUTUBE_SEARCH_QUERIES = [
    "amazon kitchen gadgets must have",
    "tiktok made me buy it kitchen",
    "amazon home finds 2026",
    "best kitchen gadgets under $50",
    "amazon organization products",
    "kitchen gadgets that are worth it",
    "viral amazon products home",
]


def calculate_trend_score(yt_trends: dict) -> float:
    """Calculate a trend score 0-100 based on YouTube signals."""
    score = 0.0

    # Momentum signals
    momentum = yt_trends.get("momentum", "steady")
    if momentum == "accelerating":
        score += 40
    elif momentum == "steady":
        score += 20
    elif momentum == "decelerating":
        score += 5

    # Competition level
    saturation = yt_trends.get("saturation", "moderate")
    if saturation == "low":
        score += 30  # Low competition = opportunity
    elif saturation == "moderate":
        score += 15
    elif saturation == "high":
        score += 5

    # Content gaps found
    gaps = yt_trends.get("content_gaps", [])
    score += min(len(gaps) * 5, 30)

    return min(score, 100)


# ============================================================
# MANUAL PRODUCT ENTRY (for quick starts)
# ============================================================

SEED_PRODUCTS = [
    {
        "name": "Fullstar Vegetable Chopper",
        "price": 24.99,
        "rating": 4.5,
        "reviews_count": 185000,
        "amazon_url": "https://amazon.com/dp/B0764HS4SL",
        "affiliate_link": f"https://amazon.com/dp/B0764HS4SL?tag={AFFILIATE_TAG}",
        "image_urls": [
            "https://m.media-amazon.com/images/I/71oBAWC4awL.jpg",
            "https://m.media-amazon.com/images/I/71mV6WAoYAL.jpg",
            "https://m.media-amazon.com/images/I/71FkZZdOIXL.jpg"
        ],
        "features": "12 blades, 7-in-1 chopper, dishwasher safe, built-in strainer",
        "task": "chopping vegetables",
        "old_method": "a knife and cutting board",
        "result": "perfectly diced veggies in seconds",
        "expensive_alt": "expensive food processors",
    },
    {
        "name": "Silicone Stove Gap Covers",
        "price": 12.99,
        "rating": 4.4,
        "reviews_count": 52000,
        "amazon_url": "https://amazon.com/dp/B0CMXM868T",
        "affiliate_link": f"https://amazon.com/dp/B0CMXM868T?tag={AFFILIATE_TAG}",
        "image_urls": [
            "https://m.media-amazon.com/images/I/71I3v-1A1WL._AC_SL1500_.jpg",
            "https://m.media-amazon.com/images/I/71fL9aD0m5L._AC_SL1500_.jpg",
            "https://m.media-amazon.com/images/I/81y5ZkI9P1L._AC_SL1500_.jpg"
        ],
        "features": "Heat resistant, fits all stoves, stops crumbs and spills",
        "task": "cleaning between the stove and counter",
        "old_method": "sticking your hand in the gap",
        "result": "no more crumbs in the stove gap",
        "expensive_alt": "custom countertops",
    },
    {
        "name": "Under Sink Organizer Shelf",
        "price": 19.99,
        "rating": 4.6,
        "reviews_count": 34000,
        "amazon_url": "https://amazon.com/dp/B0D59ZLGRR",
        "affiliate_link": f"https://amazon.com/dp/B0D59ZLGRR?tag={AFFILIATE_TAG}",
        "image_urls": [
            "https://m.media-amazon.com/images/I/71xMh-zS3eL._AC_SL1500_.jpg",
            "https://m.media-amazon.com/images/I/71P+0r81xHL._AC_SL1500_.jpg",
            "https://m.media-amazon.com/images/I/71tP0a9o1vL._AC_SL1500_.jpg"
        ],
        "features": "2-tier expandable, fits any cabinet, adjustable height",
        "task": "organizing under the sink",
        "old_method": "piling everything under the sink",
        "result": "a perfectly organized cabinet",
        "expensive_alt": "custom cabinet organizers",
    },
    {
        "name": "Electric Spin Scrubber",
        "price": 39.99,
        "rating": 4.5,
        "reviews_count": 28000,
        "amazon_url": "https://amazon.com/dp/B0B7RSV894",
        "affiliate_link": f"https://amazon.com/dp/B0B7RSV894?tag={AFFILIATE_TAG}",
        "image_urls": [
            "https://m.media-amazon.com/images/I/81xG-Y3+hXL._AC_SL1500_.jpg",
            "https://m.media-amazon.com/images/I/71T1mN6Zz6L._AC_SL1500_.jpg",
            "https://m.media-amazon.com/images/I/71B9W+D2oOL._AC_SL1500_.jpg"
        ],
        "features": "Cordless, 8 brush heads, IPX7 waterproof, 90min battery",
        "task": "scrubbing the bathroom",
        "old_method": "scrubbing on your hands and knees",
        "result": "a spotless bathroom without the effort",
        "expensive_alt": "hiring a cleaning service",
    },
    {
        "name": "Magnetic Spice Rack Organizer",
        "price": 29.99,
        "rating": 4.7,
        "reviews_count": 15000,
        "amazon_url": "https://amazon.com/dp/B0C4FHXMB1",
        "affiliate_link": f"https://amazon.com/dp/B0C4FHXMB1?tag={AFFILIATE_TAG}",
        "category": "kitchen organization",
        "image_urls": [
            "https://m.media-amazon.com/images/I/71wLpQ2e4aL._AC_SL1500_.jpg",
            "https://m.media-amazon.com/images/I/81xG-Y3+hXL._AC_SL1500_.jpg",
            "https://m.media-amazon.com/images/I/71xMh-zS3eL._AC_SL1500_.jpg"
        ],
        "features": "Removes tough stains, lightweight, easy to store",
        "task": "finding the right spice while cooking",
        "old_method": "digging through a cluttered spice cabinet",
        "result": "every spice visible and within reach",
        "expensive_alt": "built-in spice drawer systems",
    },
]


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    print(f"{'='*60}")
    print(f"  HOMVYX PRODUCT DISCOVERY — Seed Products")
    print(f"{'='*60}\n")

    for i, product in enumerate(SEED_PRODUCTS, 1):
        print(f"  {i}. {product['name']}")
        print(f"     💰 ${product['price']} | ⭐ {product['rating']} | 📝 {product['reviews_count']:,} reviews")
        print(f"     📦 Category: {product['category']}")
        print(f"     🔗 {product['affiliate_link']}")
        print()

    print(f"  Total: {len(SEED_PRODUCTS)} products ready for content generation")
    print(f"\n  Use these with script_generator.py to create content!")
