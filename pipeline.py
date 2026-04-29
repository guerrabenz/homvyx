"""
Homvyx Pipeline — Main Orchestrator
Connects all modules: Discovery → Script → Video → Post

Usage:
    python pipeline.py                    # Full pipeline with seed products
    python pipeline.py --discover         # Only product discovery
    python pipeline.py --script           # Only script generation
    python pipeline.py --video            # Only video creation
    python pipeline.py --product "Name"   # Process specific product
"""

import argparse
import json
import os
import sys
import requests
from datetime import datetime

# Add homvyx root to path
HOMVYX_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HOMVYX_DIR)

from config.settings import BRAND_NAME, VIDEOS_DIR, SCRIPTS_DIR
from discovery.product_finder import SEED_PRODUCTS
from content.script_generator import generate_all_scripts


def log(msg: str):
    """Timestamped log output."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] {msg}")


def save_scripts_to_file(product: dict, scripts: list, output_dir: str = None):
    """Save generated scripts to JSON file for reference."""
    output_dir = output_dir or SCRIPTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    safe_name = "".join(c for c in product["name"] if c.isalnum() or c in " -_")[:40].strip()
    filename = f"scripts_{safe_name.replace(' ', '_').lower()}.json"
    filepath = os.path.join(output_dir, filename)

    data = {
        "product": {
            "name": product["name"],
            "price": product.get("price"),
            "rating": product.get("rating"),
            "reviews_count": product.get("reviews_count"),
            "affiliate_link": product.get("affiliate_link"),
        },
        "generated_at": datetime.now().isoformat(),
        "scripts": scripts,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    log(f"📄 Scripts saved: {filepath}")
    return filepath


def post_to_n8n(video_path: str, product_name: str, script: dict):
    """Send the generated video and metadata to n8n via Webhook."""
    webhook_url = os.environ.get("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/homvyx-upload")
    log(f"📤 Uploading {script['platform']} video to n8n webhook...")
    
    try:
        with open(video_path, "rb") as f:
            files = {"video": (os.path.basename(video_path), f, "video/mp4")}
            data = {
                "product_name": product_name,
                "platform": script["platform"],
                "caption": script.get("caption", ""),
                "description": script.get("description", ""),
                "title": f"{product_name} - Must Have!",
                "tags": "amazonfinds,kitchenhacks,musthaves,homehacks",
                "affiliate_link": script.get("affiliate_link", "")
            }
            response = requests.post(webhook_url, files=files, data=data, timeout=300)
            
            if response.status_code == 200:
                log(f"✅ Successfully sent to n8n: {response.text}")
                return True
            else:
                log(f"❌ Failed to send to n8n: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        log(f"❌ Error sending to n8n: {e}")
        return False


def run_full_pipeline(products: list = None, create_video: bool = True):
    """
    Run the complete Homvyx pipeline:
    1. Load products (seed or discovered)
    2. Generate scripts for each product
    3. Create videos
    4. (Future: Post to social media)
    """
    products = products or SEED_PRODUCTS

    print(f"\n{'='*60}")
    print(f"  🚀 HOMVYX PIPELINE — {BRAND_NAME}")
    print(f"  Products: {len(products)} | Video: {'Yes' if create_video else 'No'}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    results = []

    for i, product in enumerate(products, 1):
        print(f"\n{'━'*60}")
        print(f"  📦 [{i}/{len(products)}] {product['name']}")
        print(f"     💰 ${product.get('price', 'N/A')} | ⭐ {product.get('rating', 'N/A')}")
        print(f"{'━'*60}")

        # Step 1: Generate scripts
        log("Generating scripts...")
        scripts = generate_all_scripts(product)
        log(f"Generated {len(scripts)} scripts ({', '.join(s['platform'] for s in scripts)})")

        # Save scripts to file
        save_scripts_to_file(product, scripts)

        # Print scripts preview
        for s in scripts:
            print(f"\n  📱 {s['platform'].upper()} ({s['framework']}, {s['duration_sec']}s)")
            print(f"  🪝 Hook: {s['sections'][list(s['sections'].keys())[0]]['text'][:80]}...")

        # Step 2: Create videos
        if create_video:
            try:
                from video.video_builder import create_content_package

                for script in scripts:
                    log(f"Creating {script['platform']} video...")
                    package = create_content_package(product, script)

                    if package.get("video_path"):
                        results.append({
                            "product": product["name"],
                            "platform": script["platform"],
                            "video_path": package["video_path"],
                            "caption": package.get("caption", "")[:100],
                            "status": "ready",
                        })
                        log(f"✅ {script['platform']} video ready!")
                        
                        # Post to n8n automatically
                        post_to_n8n(package["video_path"], product["name"], script)
                    else:
                        log(f"⚠️  {script['platform']} video failed — scripts saved for manual creation")
                        results.append({
                            "product": product["name"],
                            "platform": script["platform"],
                            "video_path": None,
                            "status": "script_only",
                        })

            except ImportError as e:
                log(f"⚠️  Video module not available ({e}). Scripts saved for manual creation.")
        else:
            log("Skipping video creation (--no-video)")

    # Summary
    print(f"\n{'='*60}")
    print(f"  📊 PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"  Products processed: {len(products)}")
    print(f"  Scripts generated: {len(products) * 3}")

    if results:
        ready = sum(1 for r in results if r["status"] == "ready")
        failed = sum(1 for r in results if r["status"] != "ready")
        print(f"  Videos created: {ready}")
        if failed:
            print(f"  Videos failed: {failed}")

    print(f"\n  📁 Output directory: {VIDEOS_DIR}")
    print(f"  📁 Scripts directory: {SCRIPTS_DIR}")
    print(f"  ⏱️  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    return results


def run_discovery_only():
    """Run only the product discovery phase."""
    print(f"\n{'='*60}")
    print(f"  🔍 HOMVYX DISCOVERY MODE")
    print(f"{'='*60}\n")

    log("Loading seed products...")
    for i, p in enumerate(SEED_PRODUCTS, 1):
        print(f"  {i}. {p['name']} — ${p['price']} ⭐{p['rating']} ({p['reviews_count']:,} reviews)")
    print(f"\n  Total: {len(SEED_PRODUCTS)} products")
    print(f"\n  💡 To discover more: Use Firecrawl MCP to scrape Amazon Best Sellers")
    print(f"     or YouTube MCP discoverNicheTrends for 'kitchen gadgets'")


def run_script_only(product_name: str = None):
    """Run only script generation for a specific product or all seeds."""
    if product_name:
        product = next((p for p in SEED_PRODUCTS if product_name.lower() in p["name"].lower()), None)
        if not product:
            print(f"  ❌ Product '{product_name}' not found in seed products")
            return
        products = [product]
    else:
        products = SEED_PRODUCTS

    for product in products:
        print(f"\n{'─'*50}")
        print(f"  📦 {product['name']}")
        scripts = generate_all_scripts(product)

        for s in scripts:
            print(f"\n  📱 {s['platform'].upper()} — {s['framework']} ({s['duration_sec']}s)")
            print(f"  {'─'*40}")
            print(f"  {s['full_script']}")
            print(f"\n  📋 Caption: {s['caption'][:150]}...")

        save_scripts_to_file(product, scripts)


# ============================================================
# CLI ENTRY POINT
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Homvyx Content Pipeline")
    parser.add_argument("--discover", action="store_true", help="Only run product discovery")
    parser.add_argument("--script", action="store_true", help="Only generate scripts")
    parser.add_argument("--video", action="store_true", help="Only create videos")
    parser.add_argument("--no-video", action="store_true", help="Skip video creation")
    parser.add_argument("--product", type=str, help="Process specific product by name")
    parser.add_argument("--count", type=int, default=None, help="Limit number of products")

    args = parser.parse_args()

    if args.discover:
        run_discovery_only()
    elif args.script:
        run_script_only(args.product)
    else:
        products = SEED_PRODUCTS
        if args.product:
            products = [p for p in SEED_PRODUCTS if args.product.lower() in p["name"].lower()]
        if args.count:
            products = products[:args.count]
        run_full_pipeline(products, create_video=not args.no_video)
