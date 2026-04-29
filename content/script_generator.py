"""
Homvyx Script Generator
Generates viral short-form video scripts for Amazon affiliate products.
Frameworks: Hook-Problem-Solution-CTA, PASTOR, AIDA, PAS
Target: US market, English, 15-60 second videos
"""

import random
import json
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    HOOKS, FRAMEWORKS, CTA_TEMPLATES, DISCLOSURE_SHORT,
    HASHTAGS, BRAND_NAME
)


def pick_hook(hook_type: str, product: dict) -> str:
    """Select and fill a hook template with product data."""
    templates = HOOKS.get(hook_type, HOOKS["curiosity"])
    template = random.choice(templates)

    replacements = {
        "{product_name}": product.get("name", "this gadget"),
        "{product_category}": product.get("category", "kitchen gadgets"),
        "{price}": str(int(product.get("price", 29))),
        "{real_price}": str(int(product.get("price", 29))),
        "{high_price}": str(int(product.get("price", 29) * 3)),
        "{reviews}": f"{product.get('reviews_count', 5000):,}",
        "{expensive_alternative}": product.get("expensive_alt", "expensive brands"),
        "{popular_product}": product.get("popular_alt", "the popular option"),
        "{bold_claim}": product.get("bold_claim", "this cheap gadget beats the expensive one"),
        "{old_method}": product.get("old_method", "the old way"),
        "{task}": product.get("task", "cooking"),
        "{common_task}": product.get("task", "organizing their kitchen"),
        "{result}": product.get("result", "a cleaner kitchen"),
        "{time}": product.get("time", "2 minutes"),
        "{specific_action}": product.get("action", "organize your pantry"),
    }

    for key, val in replacements.items():
        template = template.replace(key, val)

    return template


def generate_hps_cta(product: dict) -> dict:
    """Generate Hook-Problem-Solution-CTA script (30s)."""
    hook_type = random.choice(["curiosity", "direct", "price_anchor", "social_proof"])
    hook = pick_hook(hook_type, product)
    name = product.get("name", "this gadget")
    price = product.get("price", 29)
    features = product.get("features", "multiple uses")
    reviews = product.get("reviews_count", 5000)

    problem_templates = [
        f"If you're tired of wasting time on {product.get('task', 'kitchen tasks')}, you're not alone.",
        f"Every time I tried to {product.get('task', 'organize my kitchen')}, it was a disaster.",
        f"Let's be honest — {product.get('task', 'prepping meals')} takes way too long.",
        f"I used to spend 20 minutes on what this does in 30 seconds.",
    ]

    solution_templates = [
        f"This {name} completely changed the game. {features}. And it's only ${int(price)}.",
        f"Meet the {name}. It does {features} — and {reviews:,} people already gave it 5 stars.",
        f"The {name} handles everything. {features}. Best ${int(price)} I ever spent.",
        f"One gadget. {features}. ${int(price)}. {reviews:,} five-star reviews. Done.",
    ]

    cta = random.choice(CTA_TEMPLATES)

    return {
        "framework": "hook_problem_solution_cta",
        "hook_type": hook_type,
        "duration_sec": 30,
        "sections": {
            "hook": {"text": hook, "duration": 3},
            "problem": {"text": random.choice(problem_templates), "duration": 7},
            "solution": {"text": random.choice(solution_templates), "duration": 15},
            "cta": {"text": cta, "duration": 5},
        },
        "full_script": f"{hook}\n\n{random.choice(problem_templates)}\n\n{random.choice(solution_templates)}\n\n{cta}",
    }


def generate_aida(product: dict) -> dict:
    """Generate AIDA script (15s quick hit)."""
    name = product.get("name", "this gadget")
    price = product.get("price", 29)
    reviews = product.get("reviews_count", 5000)

    attention = pick_hook("direct", product)
    interest = f"If you {product.get('task', 'cook at home')}, this is for you."
    desire = f"{reviews:,} five-star reviews. Only ${int(price)}. And look what it does."
    action = random.choice(CTA_TEMPLATES)

    return {
        "framework": "aida",
        "hook_type": "direct",
        "duration_sec": 15,
        "sections": {
            "attention": {"text": attention, "duration": 2},
            "interest": {"text": interest, "duration": 3},
            "desire": {"text": desire, "duration": 7},
            "action": {"text": action, "duration": 3},
        },
        "full_script": f"{attention}\n\n{interest}\n\n{desire}\n\n{action}",
    }


def generate_pas(product: dict) -> dict:
    """Generate Problem-Agitate-Solve script (20s)."""
    name = product.get("name", "this gadget")
    price = product.get("price", 29)
    task = product.get("task", "keeping your kitchen organized")

    problem = f"Is your kitchen a mess? {task.capitalize()} shouldn't be this hard."
    agitate = f"And every time you try to fix it, you end up spending hours and it STILL looks the same."
    solve = f"This {name} fixes it in under 2 minutes. ${int(price)}. {random.choice(CTA_TEMPLATES)}"

    return {
        "framework": "pas",
        "hook_type": "problem_focused",
        "duration_sec": 20,
        "sections": {
            "problem": {"text": problem, "duration": 5},
            "agitate": {"text": agitate, "duration": 5},
            "solve": {"text": solve, "duration": 10},
        },
        "full_script": f"{problem}\n\n{agitate}\n\n{solve}",
    }


def generate_caption(product: dict, platform: str, script: dict) -> dict:
    """Generate platform-optimized caption with hashtags."""
    name = product.get("name", "Amazing Kitchen Gadget")
    price = product.get("price", 29)

    # Platform-specific caption style
    if platform == "youtube":
        caption = f"{name} — ${int(price)} on Amazon 🔥\n\n"
        caption += f"👇 GET YOURS: [Link in description]\n\n"
        caption += f"{DISCLOSURE_SHORT}\n\n"
        tags = random.sample(HASHTAGS["niche"], 3) + random.sample(HASHTAGS["specific"], 2)
        caption += " ".join(tags)

        description = f"🔥 {name}\n\n"
        description += f"💰 Price: ${int(price)}\n"
        description += f"⭐ Rating: {product.get('rating', 4.5)}/5 ({product.get('reviews_count', 5000):,} reviews)\n\n"
        description += f"🛒 Get it here: {product.get('affiliate_link', '[affiliate link]')}\n\n"
        description += f"{product.get('features', '')}\n\n"
        description += f"As an Amazon Associate, I earn from qualifying purchases.\n\n"
        description += " ".join(HASHTAGS["niche"] + HASHTAGS["specific"][:3])

    elif platform == "tiktok":
        caption = f"{script['sections'].get('hook', {}).get('text', name)} "
        caption += f"Only ${int(price)} 🤯 "
        caption += f"{DISCLOSURE_SHORT} "
        tags = random.sample(HASHTAGS["broad"], 1) + random.sample(HASHTAGS["niche"], 2) + random.sample(HASHTAGS["specific"], 2)
        caption += " ".join(tags)
        description = ""

    else:  # instagram
        caption = f"🏠 {name}\n\n"
        caption += f"{script.get('full_script', '')}\n\n"
        caption += f"💰 ${int(price)} on Amazon\n"
        caption += f"🔗 Link in bio!\n\n"
        caption += f"{DISCLOSURE_SHORT}\n\n"
        tags = random.sample(HASHTAGS["broad"], 1) + random.sample(HASHTAGS["niche"], 3) + random.sample(HASHTAGS["specific"], 2)
        caption += " ".join(tags)
        description = ""

    return {
        "caption": caption,
        "description": description,
        "hashtags": tags if 'tags' in dir() else [],
    }


def generate_all_scripts(product: dict) -> list:
    """Generate multiple script variations for a single product."""
    scripts = []

    # 1. Main script: Hook-Problem-Solution-CTA (YouTube Shorts)
    hps = generate_hps_cta(product)
    yt_caption = generate_caption(product, "youtube", hps)
    scripts.append({
        **hps,
        "platform": "youtube",
        "caption": yt_caption["caption"],
        "description": yt_caption["description"],
        "hashtags": " ".join(yt_caption.get("hashtags", [])),
    })

    # 2. Quick AIDA (TikTok)
    aida = generate_aida(product)
    tt_caption = generate_caption(product, "tiktok", aida)
    scripts.append({
        **aida,
        "platform": "tiktok",
        "caption": tt_caption["caption"],
        "description": "",
        "hashtags": " ".join(tt_caption.get("hashtags", [])),
    })

    # 3. PAS (Instagram Reels)
    pas = generate_pas(product)
    ig_caption = generate_caption(product, "instagram", pas)
    scripts.append({
        **pas,
        "platform": "instagram",
        "caption": ig_caption["caption"],
        "description": "",
        "hashtags": " ".join(ig_caption.get("hashtags", [])),
    })

    return scripts


# === CLI Test ===
if __name__ == "__main__":
    test_product = {
        "name": "Vegetable Chopper Pro",
        "price": 24.99,
        "rating": 4.7,
        "reviews_count": 18500,
        "category": "kitchen gadgets",
        "features": "12 blades, dishwasher safe, cuts veggies in seconds",
        "task": "chopping vegetables",
        "result": "perfectly cut veggies in seconds",
        "old_method": "a knife and cutting board",
        "affiliate_link": "https://amazon.com/dp/B0EXAMPLE?tag=homvyx-20",
    }

    print(f"{'='*60}")
    print(f"  HOMVYX SCRIPT GENERATOR — Test Run")
    print(f"  Product: {test_product['name']}")
    print(f"{'='*60}\n")

    scripts = generate_all_scripts(test_product)

    for s in scripts:
        print(f"\n{'─'*50}")
        print(f"📱 Platform: {s['platform'].upper()}")
        print(f"🎬 Framework: {s['framework']}")
        print(f"🪝 Hook Type: {s['hook_type']}")
        print(f"⏱️  Duration: {s['duration_sec']}s")
        print(f"{'─'*50}")
        print(f"\n📝 SCRIPT:\n{s['full_script']}")
        print(f"\n📋 CAPTION:\n{s['caption']}")
        if s.get("description"):
            print(f"\n📄 DESCRIPTION:\n{s['description']}")
        print()
