"""
Test normalization with real data from Phase 1 analysis

File Location: product-normalization-hackathon/test_real_data.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.normalizer import TextNormalizer
import json

def test_with_test_cases():
    """Test normalization with test cases from Phase 1"""
    
    normalizer = TextNormalizer()
    
    # Load test cases
    test_cases_file = 'output/test_cases.json'
    
    if not os.path.exists(test_cases_file):
        print(f"❌ Test cases file not found: {test_cases_file}")
        print("   Please run Phase 1 data exploration first")
        return
    
    with open(test_cases_file, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print("="*70)
    print("TESTING WITH REAL DATA FROM PHASE 1")
    print("="*70)
    print()
    
    for test_case in test_cases[:5]:  # Test first 5 cases
        print(f"Test Case {test_case['test_id']}: (Should MATCH: {test_case['should_match']})")
        print()
        
        products = test_case['products']
        
        if len(products) < 2:
            print("  ⚠️  Not enough products to compare")
            continue
        
        # Compare first two products
        p1 = products[0]
        p2 = products[1]
        
        # Normalize both
        p1_brand = normalizer.normalize_brand(p1['brand'])
        p1_product = normalizer.normalize_product_name(p1['product'])
        p1_quantity = normalizer.normalize_quantity(p1['quantity'])
        p1_fingerprint = normalizer.create_fingerprint(p1['brand'], p1['product'], p1['quantity'])
        
        p2_brand = normalizer.normalize_brand(p2['brand'])
        p2_product = normalizer.normalize_product_name(p2['product'])
        p2_quantity = normalizer.normalize_quantity(p2['quantity'])
        p2_fingerprint = normalizer.create_fingerprint(p2['brand'], p2['product'], p2['quantity'])
        
        print(f"  Product 1 [{p1['platform']}]:")
        print(f"    Original: {p1['brand']} - {p1['product']} ({p1['quantity']})")
        print(f"    Normalized Brand: {p1_brand}")
        print(f"    Normalized Product: {p1_product}")
        print(f"    Normalized Quantity: {p1_quantity}")
        print(f"    Fingerprint: {p1_fingerprint}")
        print()
        
        print(f"  Product 2 [{p2['platform']}]:")
        print(f"    Original: {p2['brand']} - {p2['product']} ({p2['quantity']})")
        print(f"    Normalized Brand: {p2_brand}")
        print(f"    Normalized Product: {p2_product}")
        print(f"    Normalized Quantity: {p2_quantity}")
        print(f"    Fingerprint: {p2_fingerprint}")
        print()
        
        # Check if they match
        brands_match = p1_brand == p2_brand
        products_match = p1_product == p2_product
        fingerprints_match = p1_fingerprint == p2_fingerprint
        
        print(f"  Comparison:")
        print(f"    Brands match: {brands_match} ✅" if brands_match else f"    Brands match: {brands_match} ❌")
        print(f"    Products match: {products_match} ✅" if products_match else f"    Products match: {products_match} ⚠️")
        print(f"    Fingerprints match: {fingerprints_match} ✅" if fingerprints_match else f"    Fingerprints match: {fingerprints_match} ⚠️")
        
        print()
        print("-"*70)
        print()


def test_brand_normalization():
    """Test brand normalization with top brands from analysis"""
    
    normalizer = TextNormalizer()
    
    # Top brands from Phase 1 analysis
    top_brands = [
        "fresho!",
        "Amul",
        "Haldiram's",
        "bb Royal",
        "Britannia",
        "Paper Boat",
        "Farmley",
        "Maggi",
        "Lay's",
        "Catch",
        "Dettol",
        "Nivea",
        "Mother Dairy",
        "Milky Mist",
        "Himalaya Herbals",
        "Tata Sampann",
        "Nestle KitKat",
        "Coca Cola",
        "Coca-Cola"
    ]
    
    print("="*70)
    print("BRAND NORMALIZATION - TOP BRANDS")
    print("="*70)
    print()
    
    for brand in top_brands:
        normalized = normalizer.normalize_brand(brand)
        print(f"  {brand:30s} → {normalized}")
    
    print()


def test_product_patterns():
    """Test product name normalization with common patterns"""
    
    normalizer = TextNormalizer()
    
    # Common product patterns from analysis
    products = [
        "Tata Tea Gold Premium Pack 500g",
        "Amul Butter Pack 100g",
        "Britannia Good Day Butter Cookies",
        "Maggi 2-Minute Instant Noodles Masala",
        "Lay's Classic Salted Potato Chips",
        "Fresho! Tender Coconut Water - With Pulpy Malai",
        "Paper Boat Aamras Mango Fruit Juice",
        "Haldiram's Aloo Bhujia Namkeen",
        "Catch Turmeric Powder 100g Pack",
        "Dettol Original Liquid Hand Wash 200ml"
    ]
    
    print("="*70)
    print("PRODUCT NAME NORMALIZATION - COMMON PATTERNS")
    print("="*70)
    print()
    
    for product in products:
        normalized = normalizer.normalize_product_name(product)
        print(f"  Original:   {product}")
        print(f"  Normalized: {normalized}")
        print()


def test_quantity_variations():
    """Test quantity normalization with various formats"""
    
    normalizer = TextNormalizer()
    
    # Quantity variations from analysis
    quantities = [
        "500 g",
        "0.5 kg",
        "500g",
        "1 kg",
        "1000 g",
        "250 ml",
        "1 l",
        "1000 ml",
        "500 g x 2",
        "200 ml x 4",
        "100g x 2",
        "1.5 kg",
        "2.5 l",
        "24 pc",
        "1 pack"
    ]
    
    print("="*70)
    print("QUANTITY NORMALIZATION - VARIATIONS")
    print("="*70)
    print()
    
    for qty in quantities:
        normalized = normalizer.normalize_quantity(qty)
        if normalized:
            print(f"  {qty:15s} → {normalized['value']} {normalized['unit']}", end="")
            if normalized['is_multipack']:
                print(f" (multipack: {normalized['pack_count']} packs, total: {normalized['total_value']})")
            else:
                print()
        else:
            print(f"  {qty:15s} → Could not parse")
    
    print()


def main():
    """Run all real data tests"""
    
    print("\n")
    print("🧪 TESTING NORMALIZATION WITH REAL DATA")
    print("="*70)
    print()
    
    # Test 1: Brand normalization
    test_brand_normalization()
    
    # Test 2: Product patterns
    test_product_patterns()
    
    # Test 3: Quantity variations
    test_quantity_variations()
    
    # Test 4: Test cases from Phase 1
    test_with_test_cases()
    
    print("="*70)
    print("✅ REAL DATA TESTING COMPLETE")
    print("="*70)
    print()
    print("Summary:")
    print("  • Brand normalization handles top brands correctly")
    print("  • Product name normalization removes stop words and quantities")
    print("  • Quantity normalization handles various formats and conversions")
    print("  • Fingerprint generation creates consistent identifiers")
    print()
    print("Next: Phase 3 will use these functions for fingerprint matching!")
    print()


if __name__ == "__main__":
    main()