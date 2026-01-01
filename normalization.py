"""
Product Normalization Module
Handles brand, product name, and quantity normalization
"""
import re
from typing import Optional

# Stop words to remove from product names
STOP_WORDS = {
    # Packaging terms
    'pack', 'bottle', 'jar', 'box', 'tin', 'pouch', 'combo', 'set',
    'piece', 'pcs', 'packet', 'sachet', 'carton', 'can', 'tube',
    
    # Common words
    'of', 'with', 'for', 'and', 'the', 'a', 'an', 'in', 'on',
    
    # Descriptive terms (that don't change the product identity)
    'premium', 'original', 'taste', 'fresh', 'new', 'best',
    'quality', 'pure', 'natural', 'organic', 'special', 'super',
    'deluxe', 'classic', 'traditional', 'authentic', 'real',
    
    # Quantity-related words (handled separately)
    'gm', 'gms', 'gram', 'grams', 'kg', 'kgs', 'kilogram', 'kilograms',
    'ml', 'mls', 'milliliter', 'milliliters', 'ltr', 'litre', 'liter',
    'l', 'oz', 'ounce', 'lb', 'pound',
    
    # Size descriptors
    'small', 'medium', 'large', 'mini', 'maxi', 'jumbo', 'giant',
    'regular', 'standard', 'family', 'economy'
}

# Brand aliases - normalize variations to standard form
BRAND_ALIASES = {
    'himalaya herbals': 'himalaya',
    'hul': 'hindustan unilever',
    'mother dairy': 'motherdairy',
    'amul india': 'amul',
    'britannia ind': 'britannia',
    'nestle india': 'nestle',
    'itc ltd': 'itc',
    'dabur india': 'dabur',
    'parle products': 'parle',
    'coca cola': 'cocacola',
    'pepsico': 'pepsi',
    'unilever': 'hindustan unilever',
    'p&g': 'procter and gamble',
    'tata consumer': 'tata',
    'godrej consumer': 'godrej',
}


def normalize_brand(brand_name: str) -> str:
    """
    Normalize brand name
    - Convert to lowercase
    - Remove extra spaces
    - Handle brand aliases
    - Remove special characters
    
    Args:
        brand_name: Original brand name
        
    Returns:
        Normalized brand name
    """
    if not brand_name:
        return ''
    
    # Convert to lowercase and strip
    brand = brand_name.lower().strip()
    
    # Remove special characters but keep spaces
    brand = re.sub(r'[^\w\s]', '', brand)
    
    # Remove extra spaces
    brand = re.sub(r'\s+', ' ', brand).strip()
    
    # Handle brand aliases
    if brand in BRAND_ALIASES:
        brand = BRAND_ALIASES[brand]
    
    return brand


def normalize_product_name(product_name: str) -> str:
    """
    Normalize product name
    - Convert to lowercase
    - Remove stop words
    - Remove quantities
    - Remove special characters
    - Remove extra spaces
    
    Args:
        product_name: Original product name
        
    Returns:
        Normalized product name
    """
    if not product_name:
        return ''
    
    # Convert to lowercase
    name = product_name.lower().strip()
    
    # Remove special characters but keep spaces
    name = re.sub(r'[^\w\s]', ' ', name)
    
    # Remove quantity patterns (will be handled separately)
    # Pattern: number followed by unit (e.g., "500g", "1.5kg", "100 ml")
    name = re.sub(r'\d+\.?\d*\s*(?:g|gm|gms|gram|grams|kg|kgs|kilogram|kilograms|ml|mls|milliliter|milliliters|ltr|litre|liter|l|oz|ounce|lb|pound)s?\b', '', name, flags=re.IGNORECASE)
    
    # Remove standalone numbers (like "2" in "2 pack")
    name = re.sub(r'\b\d+\b', '', name)
    
    # Split into words
    words = name.split()
    
    # Remove stop words
    words = [w for w in words if w not in STOP_WORDS]
    
    # Remove duplicates while preserving order
    seen = set()
    words = [w for w in words if not (w in seen or seen.add(w))]
    
    # Join back and remove extra spaces
    name = ' '.join(words)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def normalize_quantity(quantity: str) -> str:
    """
    Normalize quantity to standard format
    - Convert to base units (grams for weight, ml for volume)
    - Standardize format
    
    Args:
        quantity: Original quantity string (e.g., "500g", "0.5kg", "1 liter")
        
    Returns:
        Normalized quantity (e.g., "500_gram", "1000_ml")
    """
    if not quantity:
        return ''
    
    # Convert to lowercase
    qty = quantity.lower().strip()
    
    # Remove special characters except dots and spaces
    qty = re.sub(r'[^\w\s.]', '', qty)
    
    # Weight conversions to grams
    patterns = [
        # Kilograms to grams
        (r'(\d+\.?\d*)\s*(?:kg|kgs|kilogram|kilograms)\b', lambda m: f"{float(m.group(1)) * 1000}_gram"),
        # Grams
        (r'(\d+\.?\d*)\s*(?:g|gm|gms|gram|grams)\b', lambda m: f"{float(m.group(1))}_gram"),
        # Pounds to grams (1 lb = 453.592 grams)
        (r'(\d+\.?\d*)\s*(?:lb|lbs|pound|pounds)\b', lambda m: f"{float(m.group(1)) * 453.592}_gram"),
        # Ounces to grams (1 oz = 28.3495 grams)
        (r'(\d+\.?\d*)\s*(?:oz|ounce|ounces)\b', lambda m: f"{float(m.group(1)) * 28.3495}_gram"),
        
        # Volume conversions to ml
        # Liters to ml
        (r'(\d+\.?\d*)\s*(?:l|ltr|litre|liter|liters|litres)\b', lambda m: f"{float(m.group(1)) * 1000}_ml"),
        # Milliliters
        (r'(\d+\.?\d*)\s*(?:ml|mls|milliliter|milliliters)\b', lambda m: f"{float(m.group(1))}_ml"),
    ]
    
    for pattern, converter in patterns:
        match = re.search(pattern, qty, re.IGNORECASE)
        if match:
            try:
                normalized = converter(match)
                # Round to 2 decimal places and remove unnecessary decimals
                value, unit = normalized.split('_')
                value = float(value)
                if value == int(value):
                    return f"{int(value)}_{unit}"
                else:
                    return f"{value:.2f}_{unit}".rstrip('0').rstrip('.')
            except:
                continue
    
    # If no pattern matched, return original (cleaned)
    return re.sub(r'\s+', '_', qty)


def create_fingerprint(brand: str, product_name: str, quantity: str = '') -> str:
    """
    Create a unique fingerprint for a product
    Combines normalized brand, product name, and quantity
    
    Args:
        brand: Normalized brand name
        product_name: Normalized product name
        quantity: Normalized quantity
        
    Returns:
        Fingerprint string (sorted words for consistency)
    """
    # Combine all parts
    parts = []
    
    if brand:
        parts.extend(brand.split())
    
    if product_name:
        parts.extend(product_name.split())
    
    if quantity:
        parts.append(quantity)
    
    # Sort alphabetically for consistency
    parts.sort()
    
    # Join with underscore
    fingerprint = '_'.join(parts)
    
    return fingerprint.lower()


# Test functions
def test_normalization():
    """Test the normalization functions"""
    
    print("Testing Brand Normalization:")
    print("-" * 50)
    test_brands = [
        "Tata Tea",
        "TATA TEA",
        "Himalaya Herbals",
        "Mother Dairy",
        "Amul India",
        "Coca-Cola"
    ]
    
    for brand in test_brands:
        normalized = normalize_brand(brand)
        print(f"{brand:30} -> {normalized}")
    
    print("\n\nTesting Product Name Normalization:")
    print("-" * 50)
    test_products = [
        "Tata Tea Gold Premium Pack 500g",
        "Amul Butter 100g Pack",
        "Himalaya Face Wash 100ml",
        "Coca Cola Soft Drink, 750 ml",
        "Premium Quality Basmati Rice 1kg"
    ]
    
    for product in test_products:
        normalized = normalize_product_name(product)
        print(f"{product:45} -> {normalized}")
    
    print("\n\nTesting Quantity Normalization:")
    print("-" * 50)
    test_quantities = [
        "500g",
        "0.5kg",
        "500 gm",
        "1 liter",
        "1000ml",
        "100 ml",
        "1.5 kg"
    ]
    
    for qty in test_quantities:
        normalized = normalize_quantity(qty)
        print(f"{qty:20} -> {normalized}")
    
    print("\n\nTesting Fingerprint Creation:")
    print("-" * 50)
    test_cases = [
        ("Tata", "Tea Gold Premium Pack", "500g"),
        ("TATA", "Tea Gold", "0.5kg"),
        ("Amul", "Butter Pack", "100g"),
        ("Amul", "Butter", "100 gm"),
    ]
    
    for brand, product, qty in test_cases:
        brand_norm = normalize_brand(brand)
        product_norm = normalize_product_name(product)
        qty_norm = normalize_quantity(qty)
        fingerprint = create_fingerprint(brand_norm, product_norm, qty_norm)
        print(f"\nOriginal: {brand} | {product} | {qty}")
        print(f"Normalized: {brand_norm} | {product_norm} | {qty_norm}")
        print(f"Fingerprint: {fingerprint}")


if __name__ == "__main__":
    test_normalization()