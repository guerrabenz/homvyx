"""
Homvyx Automation Pipeline — Configuration
Brand: Homvyx | Niche: Home & Kitchen | Market: US (Amazon.com, USD, English)
"""

# === BRAND ===
BRAND_NAME = "Homvyx"
BRAND_TAGLINE = "Smart home finds you didn't know you needed"
NICHE = "home & kitchen"
LANGUAGE = "en"
MARKET = "US"
CURRENCY = "USD"

# === AMAZON ===
AMAZON_BASE_URL = "https://www.amazon.com"
AMAZON_BESTSELLERS = {
    "kitchen": "https://www.amazon.com/Best-Sellers-Kitchen-Dining/zgbs/kitchen",
    "home": "https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden",
    "organization": "https://www.amazon.com/Best-Sellers-Storage-Organization/zgbs/storageorganization",
    "gadgets": "https://www.amazon.com/Best-Sellers-Kitchen-Dining-Gadgets/zgbs/kitchen/289754",
}
AFFILIATE_TAG = "homvyx-20"  # Replace with your actual Amazon Associates tag
PRODUCT_FILTERS = {
    "min_price": 15.0,
    "max_price": 150.0,
    "min_rating": 4.0,
    "min_reviews": 500,
}

# === SOCIAL CHANNELS ===
CHANNELS = {
    "youtube": {
        "name": "Homvyx",
        "handle": "@homvyx",
        "post_time": "12:00",  # EST
        "format": "shorts",
    },
    "tiktok": {
        "name": "Homvyx",
        "handle": "@homvyx",
        "post_time": "14:00",
        "format": "video",
    },
    "instagram": {
        "name": "Homvyx",
        "handle": "@homvyx",
        "post_time": "18:00",
        "format": "reels",
    },
}

# === VIDEO SETTINGS ===
VIDEO = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "duration_target": 30,  # seconds
    "max_duration": 60,
    "format": "mp4",
    "codec": "libx264",
}

# === TTS (Text-to-Speech) ===
TTS = {
    "engine": "edge-tts",  # Free, high quality
    "voice": "en-US-ChristopherNeural",  # Male US voice
    "voice_alt": "en-US-JennyNeural",    # Female US voice
    "rate": "+5%",
    "pitch": "+0Hz",
}

# === CONTENT TEMPLATES ===
DISCLOSURE = "As an Amazon Associate, I earn from qualifying purchases."
DISCLOSURE_SHORT = "#ad #amazonassociate"

CTA_TEMPLATES = [
    "Link in bio to grab yours! 🔗",
    "Tap the link in bio before it sells out! ⚡",
    "Get yours from the link in bio! 👆",
    "Link in bio — thank me later! 😉",
    "Found the link for you — check bio! 🎯",
]

# === HASHTAGS ===
HASHTAGS = {
    "broad": ["#fyp", "#foryou", "#viral"],
    "niche": ["#amazonfinds", "#kitchenhacks", "#homehacks", "#musthaves", "#amazonmusthaves"],
    "specific": ["#kitchengadgets", "#homeorganization", "#productreview", "#amazondeals", "#tiktokmademebuyit"],
}

# === HOOK TEMPLATES (English, US market) ===
HOOKS = {
    "curiosity": [
        "Nobody tells you this about {product_category}...",
        "I found this by accident and it changed everything.",
        "The detail 99% of people miss about {product_name}.",
        "This will make a lot of people angry, but...",
        "3 things your kitchen is missing right now.",
    ],
    "contrarian": [
        "Stop wasting money on {expensive_alternative}. Get this instead.",
        "Everyone recommends {popular_product}. Here's why they're wrong.",
        "Most people do {common_task} wrong. Including me.",
        "Unpopular opinion: {bold_claim}.",
    ],
    "direct": [
        "Stop using {old_method} for {task}. Do this instead.",
        "3 steps to {result} in under {time}.",
        "30-second tutorial: {specific_action}.",
        "Save this video for when you need it.",
        "If you cook at home, you NEED to know this.",
    ],
    "social_proof": [
        "This ${price} gadget has {reviews} five-star reviews.",
        "{reviews} people can't be wrong about this.",
        "The most viral kitchen gadget of 2026.",
        "Why everyone on TikTok is buying this.",
    ],
    "price_anchor": [
        "This looks like it costs ${high_price}. It's actually ${real_price}.",
        "Under ${price} and it does THIS?!",
        "Best kitchen gadget under ${price}. Period.",
        "I can't believe this only costs ${price}.",
    ],
}

# === SCRIPT FRAMEWORKS ===
FRAMEWORKS = {
    "hook_problem_solution_cta": {
        "structure": ["hook", "problem", "solution", "cta"],
        "timing": {"hook": 3, "problem": 7, "solution": 15, "cta": 5},
        "total_sec": 30,
        "best_for": "shorts",
    },
    "pastor": {
        "structure": ["problem", "amplify", "story", "transformation", "offer", "response"],
        "timing": {"problem": 5, "amplify": 5, "story": 10, "transformation": 10, "offer": 15, "response": 5},
        "total_sec": 50,
        "best_for": "longer_reviews",
    },
    "aida": {
        "structure": ["attention", "interest", "desire", "action"],
        "timing": {"attention": 2, "interest": 3, "desire": 7, "action": 3},
        "total_sec": 15,
        "best_for": "quick_hits",
    },
    "pas": {
        "structure": ["problem", "agitate", "solve"],
        "timing": {"problem": 5, "agitate": 5, "solve": 10},
        "total_sec": 20,
        "best_for": "problem_focused",
    },
}

# === PATHS ===
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
VIDEOS_DIR = os.path.join(OUTPUT_DIR, "videos")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
SCRIPTS_DIR = os.path.join(OUTPUT_DIR, "scripts")

for d in [OUTPUT_DIR, VIDEOS_DIR, IMAGES_DIR, AUDIO_DIR, SCRIPTS_DIR]:
    os.makedirs(d, exist_ok=True)
