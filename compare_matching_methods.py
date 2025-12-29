"""
Compare Fingerprint-Only vs Fingerprint+Fuzzy Matching

File Location: product-normalization-hackathon/compare_matching_methods.py

This script runs both matching methods and compares results.
"""

import pandas as pd
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.fuzzy_matcher import FuzzyProductMatcher
from src.config import PRODUCTS_INPUT_FILE


def run_comparison(sample_size: int = None):
    """
    Run both matching methods and compare results
    
    Args:
        sample_size: Number of products to process (None for all)
    """
    print("\n")
    print("="*70)
    print("MATCHING METHODS COMPARISON")
    print("="*70)
    print()
    
    # Load data
    print("📂 Loading data...")
    df = pd.read_csv(PRODUCTS_INPUT_FILE)
    
    if sample_size:
        df = df.head(sample_size)
        print(f"   Using sample of {sample_size} products")
    
    print(f"   Loaded {len(df)} products")
    print()
    
    products = df.to_dict('records')
    
    # ========================================================================
    # Method 1: Fingerprint Only
    # ========================================================================
    
    print("="*70)
    print("METHOD 1: FINGERPRINT MATCHING ONLY")
    print("="*70)
    print()
    
    matcher_fingerprint = FuzzyProductMatcher(enable_fuzzy=False)
    
    start_time = datetime.now()
    
    for product in products:
        matcher_fingerprint.find_or_create_normalized_product(
            brand_name=product.get('brand_name', ''),
            product_name=product.get('product_name', ''),
            quantity=product.get('quantity'),
            category=product.get('category')
        )
    
    time_fingerprint = (datetime.now() - start_time).total_seconds()
    
    stats_fingerprint = matcher_fingerprint.get_statistics()
    
    print(f"⏱️  Time: {time_fingerprint:.2f} seconds")
    print(f"📊 Results:")
    print(f"   Total Processed:        {stats_fingerprint['total_products_processed']}")
    print(f"   Matches Found:          {stats_fingerprint['fingerprint_matches']}")
    print(f"   New Products:           {stats_fingerprint['new_normalized_products']}")
    print(f"   Match Rate:             {stats_fingerprint['match_rate_percent']:.2f}%")
    print()
    
    # ========================================================================
    # Method 2: Fingerprint + Fuzzy
    # ========================================================================
    
    print("="*70)
    print("METHOD 2: FINGERPRINT + FUZZY MATCHING")
    print("="*70)
    print()
    
    matcher_fuzzy = FuzzyProductMatcher(enable_fuzzy=True)
    
    start_time = datetime.now()
    
    for product in products:
        matcher_fuzzy.find_or_create_normalized_product(
            brand_name=product.get('brand_name', ''),
            product_name=product.get('product_name', ''),
            quantity=product.get('quantity'),
            category=product.get('category')
        )
    
    time_fuzzy = (datetime.now() - start_time).total_seconds()
    
    stats_fuzzy = matcher_fuzzy.get_statistics()
    
    print(f"⏱️  Time: {time_fuzzy:.2f} seconds")
    print(f"📊 Results:")
    print(f"   Total Processed:        {stats_fuzzy['total_products_processed']}")
    print(f"   Fingerprint Matches:    {stats_fuzzy['fingerprint_matches']}")
    print(f"   Fuzzy Matches:          {stats_fuzzy['fuzzy_matches']}")
    print(f"   Total Matches:          {stats_fuzzy['fingerprint_matches'] + stats_fuzzy['fuzzy_matches']}")
    print(f"   New Products:           {stats_fuzzy['new_normalized_products']}")
    print(f"   Match Rate:             {stats_fuzzy['total_match_rate_percent']:.2f}%")
    print()
    
    # ========================================================================
    # Comparison
    # ========================================================================
    
    print("="*70)
    print("COMPARISON")
    print("="*70)
    print()
    
    # Match rate improvement
    improvement = stats_fuzzy['total_match_rate_percent'] - stats_fingerprint['match_rate_percent']
    
    print("Match Rate:")
    print(f"   Fingerprint Only:       {stats_fingerprint['match_rate_percent']:.2f}%")
    print(f"   Fingerprint + Fuzzy:    {stats_fuzzy['total_match_rate_percent']:.2f}%")
    print(f"   Improvement:            +{improvement:.2f}%")
    print()
    
    # Additional matches from fuzzy
    additional_matches = stats_fuzzy['fuzzy_matches']
    reduction_improvement = (stats_fingerprint['new_normalized_products'] - stats_fuzzy['new_normalized_products'])
    
    print("Additional Matches from Fuzzy:")
    print(f"   Extra Matches:          {additional_matches}")
    print(f"   Products Deduplicated:  {reduction_improvement}")
    print()
    
    # Performance comparison
    time_diff = time_fuzzy - time_fingerprint
    time_diff_percent = (time_diff / time_fingerprint) * 100 if time_fingerprint > 0 else 0
    
    print("Performance:")
    print(f"   Fingerprint Time:       {time_fingerprint:.2f} seconds")
    print(f"   Fuzzy Time:             {time_fuzzy:.2f} seconds")
    print(f"   Time Overhead:          +{time_diff:.2f} seconds (+{time_diff_percent:.1f}%)")
    print()
    
    # Speed comparison
    speed_fingerprint = stats_fingerprint['total_products_processed'] / time_fingerprint
    speed_fuzzy = stats_fuzzy['total_products_processed'] / time_fuzzy
    
    print(f"   Fingerprint Speed:      {speed_fingerprint:.0f} products/second")
    print(f"   Fuzzy Speed:            {speed_fuzzy:.0f} products/second")
    print()
    
    # Recommendation
    print("="*70)
    print("RECOMMENDATION")
    print("="*70)
    print()
    
    if improvement > 5:
        print("✅ RECOMMENDATION: Use Fuzzy Matching")
        print(f"   Reason: Significant improvement (+{improvement:.2f}%) with acceptable overhead")
    elif improvement > 2:
        print("⚡ RECOMMENDATION: Use Fuzzy Matching (if time permits)")
        print(f"   Reason: Moderate improvement (+{improvement:.2f}%)")
    else:
        print("⚠️  RECOMMENDATION: Fingerprint may be sufficient")
        print(f"   Reason: Minimal improvement (+{improvement:.2f}%)")
    
    print()
    print("="*70)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare matching methods')
    parser.add_argument('--sample', type=int, default=None,
                      help='Number of products to process (default: all)')
    
    args = parser.parse_args()
    
    run_comparison(sample_size=args.sample)


if __name__ == "__main__":
    main()