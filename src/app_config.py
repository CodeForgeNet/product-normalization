import os

PACKAGING_STOP_WORDS = {
    'pack', 'bottle', 'jar', 'box', 'tin', 'pouch', 'combo', 'set',
    'packet', 'packets', 'piece', 'pieces', 'pcs', 'pc',
    'container', 'can', 'tube', 'sachet', 'bag', 'bags',
    'carton', 'wrapper', 'multipack', 'pack of', 'value pack',
    'family pack', 'jumbo pack', 'super saver', 'economy pack'
}

COMMON_STOP_WORDS = {
    'of', 'with', 'for', 'and', 'the', 'a', 'an', 'in', 'on',
    'at', 'to', 'from', 'by', 'as', 'is', 'or', 'new', 'fresh',
    'made', 'quality', 'spices', 'active'
}

QUALITY_STOP_WORDS = {
    'premium', 'original', 'taste', 'classic', 'special', 'super',
    'deluxe', 'select', 'choice', 'best', 'top', 'quality',
    'pure', 'natural', 'organic', 'healthy', 'tasty', 'delicious',
    'refreshing', 'crispy', 'crunchy', 'soft', 'smooth',
    'rich', 'creamy', 'light', 'dark', 'magic', 'golden',
    'farm fresh', 'handpicked', 'authentic', 'traditional'
}

ALL_STOP_WORDS = PACKAGING_STOP_WORDS | COMMON_STOP_WORDS | QUALITY_STOP_WORDS


BRAND_ALIASES = {
    'amulspray': 'amul',
    'amul lite': 'amul',
    'amulya': 'amul',
    'amul kool': 'amul',
    'amul kool cafe': 'amul',
    'amul mithai mate': 'amul',
    'amul happy treats': 'amul',
    'amul gold': 'amul',
    
    'nestle milkmaid mini': 'nestle',
    'nestle a+': 'nestle',
    'nestle milo': 'nestle',
    'nestle kitkat': 'nestle',
    'nestle munch': 'nestle',
    'nestle nangrow': 'nestle',
    'nestle lactogrow': 'nestle',
    'nestle gold': 'nestle',
    'nestle nesplus': 'nestle',
    'nestle koko krunch': 'nestle',
    'nestle milkybar': 'nestle',
    'nescafe': 'nestle',
    
    'britannia laughing cow': 'britannia',
    'britannia dairy': 'britannia',
    'britannia breads': 'britannia',
    'britannia nutrichoice': 'britannia',
    'britannia little hearts': 'britannia',
    'britannia good day': 'britannia',
    'britannia pure magic': 'britannia',
    'britannia treat jim jam': 'britannia',
    'britannia marie gold': 'britannia',
    'britannia vita marie': 'britannia',
    'britannia bourbon': 'britannia',
    'britannia nice time': 'britannia',
    'britannia 5050': 'britannia',
    'britannia milk bikis': 'britannia',
    'britannia treat': 'britannia',
    'britannia tiger krunch': 'britannia',
    
    'himalaya herbals': 'himalaya',
    'himalayan natives': 'himalaya',
    'himalayan': 'himalaya',
    'himalaya wellness': 'himalaya',
    
    'heritage foods (india) limited': 'heritage',
    
    'patanjali': 'patanjali',
    
    'haldiram': 'haldirams',
    'haldiram bhujiawala': 'haldirams',
    "haldiram's": 'haldirams',
    
    'mother dairy': 'motherdairy',
    
    'hul': 'hindustan unilever',
    'hindustan unilever': 'hul',
    
    
    'dabur india': 'dabur',
    'dabur otc': 'dabur',
    'dabur hommade': 'dabur',
    'dabur real': 'dabur',
    'dabur home care': 'dabur',
    'dabur oral care': 'dabur',
    'dabur hair care': 'dabur',
    'dabur vatika': 'dabur',
    'dabur amla': 'dabur',
    
    'parle products': 'parle',
    'parle platina': 'parle',
    'parle milano': 'parle',
    'parle hide & seek': 'parle',
    'parle krackjack': 'parle',
    'parle-g': 'parle',
    'parle marie': 'parle',
    'parle monaco': 'parle',
    
    'itc limited': 'itc',
    'itc master chef': 'itc',
    'modern kitchens': 'itc',
    'modern kitchen': 'itc',
    'modern': 'itc',
    'oleev kitchen': 'itc',
    'the cinnamon kitchen': 'itc',
    'kitchen treasures': 'itc',
    'kitchen champion': 'itc',
    'kitchential': 'itc',
    'itc nimyle': 'itc',
    'fruitchill': 'itc',
    
    'tata sampann': 'tata',
    'tata coffee': 'tata',
    'tata coffee grand': 'tata',
    'tata coffee gold': 'tata',
    'tata simply better': 'tata',
    'tata soulfull': 'tata',
    'tata salt': 'tata',
    'tata gofit': 'tata',
    
    'cadbury dairy milk': 'cadbury',
    'cadbury nutties': 'cadbury',
    'cadbury bournville': 'cadbury',
    'cadbury bournvita': 'cadbury',
    'cadbury bournvita biscuits': 'cadbury',
    'cadbury chocobakes': 'cadbury',
    'cadbury oreo': 'cadbury',
    'cadbury dairy milk silk': 'cadbury',
    'cadbury temptations': 'cadbury',
    
    'sunfeast yippee!': 'sunfeast',
    'sunfeast yippee': 'sunfeast',
    'sunfeast dark fantasy': 'sunfeast',
    'sunfeast baked creations': 'sunfeast',
    'sunfeast farmlite': 'sunfeast',
    'sunfeast bourbon': 'sunfeast',
    'sunfeast wowzers': 'sunfeast',
    "sunfeast mom's magic": 'sunfeast',
    'sunfeast nice': 'sunfeast',
    
    "kwality wall's": 'kwality',
    'kwality bakers': 'kwality',
    'kwality walls magnum': 'kwality',
    'kwality walls cornetto': 'kwality',
    'kwality walls': 'kwality',
    "kwality wall's cornetto": 'kwality',
    
    "lay's": 'lays',
    "lay's stax": 'lays',
    
    'bingo!': 'bingo',
    'bingo tedhe medhe': 'bingo',
    'bingo mad angles': 'bingo',
    
    'pepsico': 'pepsi',
    'pepsi imported': 'pepsi',
    'pepsi black': 'pepsi',
    'pepsi vietnam': 'pepsi',
    
    'coca cola': 'cocacola',
    'coca-cola': 'cocacola',
    
    'maggi nutrilicious': 'maggi',
    'maggi spicy': 'maggi',
    
    'paper boat': 'paperboat',
    'paper boat zero': 'paperboat',
    
    'catch': 'catch',
    
    'dettol-international': 'dettol',
    
    'nivea men': 'nivea',
    
    'colgate': 'colgate',
    
    'milky mist': 'milkymist',
    
    'whole farm': 'wholefarm',
    'whole farm grocery': 'wholefarm',
    
    'yoga bar': 'yogabar',
    
    "kellogg's": 'kelloggs',
    
    'bb royal': 'bbroyal',
    'bb popular': 'bbpopular',
    'bb gooddiet': 'bbgooddiet',
    'bb super saver': 'bbsupersaver',
    'bb home': 'bbhome',
    'bb home herbal': 'bbhome',
    
    'fresho!': 'fresho',
    'id fresho!': 'fresho',
    'fresho! organic': 'fresho',
    'fresho! signature': 'fresho',
    'fresho! premium': 'fresho',
    
    'organic india': 'organicindia',
    'organic tattva': 'organictattva',
    'organic mandya': 'organicmandya',
    '24 mantra organic': '24mantra',
    '24 mantra': '24mantra',
    'natureland organics': 'naturelandorganics',
    'organic nation': 'organicnation',
    
    'bru': 'bru',
    'bru instant': 'bru',
    
    'real': 'real',
    'real thai': 'real',
    'real activ': 'real',
    'real namkeen': 'real',
    'real nut': 'real',
    'real fruit power': 'real',
    'real cheers': 'real',
    
    'vadilal': 'vadilal',
    'vadilal mumbai': 'vadilal',
    'vadilal quick treat': 'vadilal',
    
    'too yumm': 'tooyumm',
    'too yumm!': 'tooyumm',
    
    'chitale': 'chitale',
    'chitale dairy': 'chitale',
    'chitale bandhu mithaiwale': 'chitale',
    'chitale bandhu': 'chitale',
    
    'epigamia': 'epigamia',
    'epigamia origins': 'epigamia',
    
    'akshayakalpa organic': 'akshayakalpa',
    'akshayakalpa': 'akshayakalpa',
    
    'nandini': 'nandini',
    'nandi': 'nandini',
    
    'aashirvaad': 'aashirvaad',
    'aashirvaad mithaas': 'aashirvaad',
    
    'mtr': 'mtr',
    'mtr 3 minute': 'mtr',
    
    'farmley': 'farmley',
    
    'dukes': 'dukes',
    'dukes waffy': 'dukes',
    
    'godrej jersey': 'godrej',
    'godrej yummiez': 'godrej',
    'godrej protekt': 'godrej',
    'godrej ezee': 'godrej',
    'godrej fab': 'godrej',
    'godrej genteel': 'godrej',
    'godrej aer': 'godrej',
    'godrej magic': 'godrej',
    'godrej no.1': 'godrej',
    
    'unibic': 'unibic',
    'unibic swaadesi': 'unibic',
    
    'fortune': 'fortune',
    'fortune xpert': 'fortune',
    
    'saffola': 'saffola',
    'saffola foods': 'saffola',
    
    'borges': 'borges',
    
    'veeba': 'veeba',
    'wok tok by veeba': 'veeba',
    
    "ching's secret": 'chings',
    "ching's": 'chings',
    
    'gillette': 'gillette',
    'gillette venus': 'gillette',
    'gillette fusion': 'gillette',
    
    "l'oreal": 'loreal',
    "l'oreal paris": 'loreal',
    "l'oreal professional": 'loreal',
    
    'dove': 'dove',
    'baby dove': 'dove',
    'dove men+': 'dove',
    
    'garnier': 'garnier',
    'garnier men': 'garnier',
    'garnier skin naturals': 'garnier',
    
    'lakme': 'lakme',
    'lakme 9to5': 'lakme',
    
    'sugar cosmetics': 'sugar',
    'sugar pop': 'sugar',
    
    'maybelline': 'maybelline',
    'maybelline new york': 'maybelline',
    
    'lotus': 'lotus',
    'lotus herbals': 'lotus',
    'lotus biscoff': 'lotus',
    'lotus make-up': 'lotus',
    'lotus professional': 'lotus',
    
    'the body shop': 'thebodyshop',
    
    'mamaearth': 'mamaearth',
    
    'plum': 'plum',
    "plum bodylovin'": 'plum',
    
    'wow!': 'wow',
    'wow! coco charge': 'wow',
    'wow! noodles': 'wow',
    'wow! momo': 'wow',
    'wow! kulfi': 'wow',
    
    'harpic': 'harpic',
    'harpic-international': 'harpic',
    
    'vim': 'vim',
    
    'tide': 'tide',
    'tide plus': 'tide',
    
    'surf excel': 'surfexcel',
    
    'rin': 'rin',
    'lizol': 'lizol',
    
    'coca-cola': 'cocacola',
    'coca cola': 'cocacola',
}

QUANTITY_UNITS = {
    'kg': 'gram',
    'kgs': 'gram',
    'g': 'gram',
    'gm': 'gram',
    'gms': 'gram',
    'gram': 'gram',
    'grams': 'gram',
    
    'l': 'ml',
    'ltr': 'ml',
    'litre': 'ml',
    'litres': 'ml',
    'liter': 'ml',
    'liters': 'ml',
    'ml': 'ml',
    'milliliter': 'ml',
    'millilitre': 'ml',
    
    'pc': 'piece',
    'pcs': 'piece',
    'piece': 'piece',
    'pieces': 'piece',
    'pack': 'piece',
    'packs': 'piece',
    'u': 'piece',
}

UNIT_MULTIPLIERS = {
    'kg': 1000,
    'kgs': 1000,
    'l': 1000,
    'ltr': 1000,
    'litre': 1000,
    'litres': 1000,
    'liter': 1000,
    'liters': 1000,
}

FINGERPRINT_MATCH_THRESHOLD = 100
FUZZY_MATCH_THRESHOLD = 90
SEMANTIC_MATCH_THRESHOLD = 0.88

QUANTITY_TOLERANCE = 0.05

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
DOCS_DIR = os.path.join(BASE_DIR, 'docs')

PRODUCTS_INPUT_FILE = os.path.join(DATA_DIR, 'products_table.csv')
NORMALIZED_PRODUCTS_OUTPUT = os.path.join(OUTPUT_DIR, 'normalized_products.csv')
PRODUCTS_OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'products_updated.csv')
TEST_CASES_FILE = os.path.join(OUTPUT_DIR, 'test_cases.json')
ANALYSIS_REPORT_FILE = os.path.join(OUTPUT_DIR, 'data_analysis_report.json')

PHASE1_SUMMARY = os.path.join(DOCS_DIR, 'phase1_summary.md')
LOG_FILE = os.path.join(LOGS_DIR, 'processing.log')

BATCH_SIZE = 1000
ENABLE_EMBEDDINGS = True
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
EMBEDDING_CACHE_FILE = os.path.join(OUTPUT_DIR, 'embeddings_cache.pkl')

MAX_CANDIDATES_FUZZY = 50
MAX_CANDIDATES_SEMANTIC = 20


import re

QUANTITY_PATTERNS = [
    r'(\d+\.?\d*)\s*(kg|kgs|g|gm|gms|gram|grams|l|ltr|litre|litres|liter|liters|ml)\b',
    r'(\d+\.?\d*)\s*(kg|kgs|g|gm|gms|gram|grams|l|ltr|litre|litres|liter|liters|ml)\s*x\s*(\d+)',
    r'(\d+)\s*(pc|pcs|piece|pieces|pack|packs|u)\b',
]

COMPILED_QUANTITY_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in QUANTITY_PATTERNS]

DATASET_STATS = {
    'total_products': 16369,
    'unique_brands': 2369,
    'platforms': ['bigbasket', 'blinkit', 'zepto', 'dmart'],
    'top_categories': [
        'Snacks & Branded Foods',
        'Foodgrains, Oil & Masala',
        'Beauty & Hygiene',
        'Bakery, Cakes & Dairy',
        'Beverages'
    ]
}


os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)


def validate_config():
    issues = []
    
    if not os.path.exists(DATA_DIR):
        issues.append(f"Data directory not found: {DATA_DIR}")
    
    if not os.path.exists(PRODUCTS_INPUT_FILE):
        issues.append(f"Input file not found: {PRODUCTS_INPUT_FILE}")
    
    if FUZZY_MATCH_THRESHOLD < 0 or FUZZY_MATCH_THRESHOLD > 100:
        issues.append(f"Invalid fuzzy match threshold: {FUZZY_MATCH_THRESHOLD}")
    
    if SEMANTIC_MATCH_THRESHOLD < 0 or SEMANTIC_MATCH_THRESHOLD > 1:
        issues.append(f"Invalid semantic match threshold: {SEMANTIC_MATCH_THRESHOLD}")
    
    return issues


if __name__ == "__main__":
    print("="*70)
    print("CONFIGURATION SUMMARY")
    print("="*70)
    print(f"\n📂 Directories:")
    print(f"   Base: {BASE_DIR}")
    print(f"   Data: {DATA_DIR}")
    print(f"   Output: {OUTPUT_DIR}")
    print(f"   Logs: {LOGS_DIR}")
    
    print(f"\n📄 Files:")
    print(f"   Input: {PRODUCTS_INPUT_FILE}")
    print(f"   Output (Normalized): {NORMALIZED_PRODUCTS_OUTPUT}")
    print(f"   Output (Products): {PRODUCTS_OUTPUT_FILE}")
    
    print(f"\n🎯 Matching Settings:")
    print(f"   Fingerprint Threshold: {FINGERPRINT_MATCH_THRESHOLD}%")
    print(f"   Fuzzy Match Threshold: {FUZZY_MATCH_THRESHOLD}%")
    print(f"   Semantic Match Threshold: {SEMANTIC_MATCH_THRESHOLD}")
    print(f"   Embeddings Enabled: {ENABLE_EMBEDDINGS}")
    
    print(f"\n📊 Stop Words:")
    print(f"   Packaging: {len(PACKAGING_STOP_WORDS)} words")
    print(f"   Common: {len(COMMON_STOP_WORDS)} words")
    print(f"   Quality: {len(QUALITY_STOP_WORDS)} words")
    print(f"   Total: {len(ALL_STOP_WORDS)} words")
    
    print(f"\n🏷️  Brand Aliases:")
    print(f"   Total: {len(BRAND_ALIASES)} aliases defined")
    
    print(f"\n📐 Quantity Units:")
    print(f"   Weight units: {len([u for u in QUANTITY_UNITS.values() if u == 'gram'])}")
    print(f"   Volume units: {len([u for u in QUANTITY_UNITS.values() if u == 'ml'])}")
    
    print(f"\n✅ Configuration validation:")
    issues = validate_config()
    if issues:
        print("   ⚠️  Issues found:")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("   ✅ All checks passed!")
    
    print("\n" + "="*70)
    print("Configuration loaded successfully!")
    print("="*70)