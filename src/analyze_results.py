"""
Results Analysis Script - Analyze matching results and quality

File Location: product-normalization-hackathon/src/analyze_results.py

This script analyzes the output of Phase 3 matching to evaluate
accuracy and identify areas for improvement.
"""

import pandas as pd
import sys
import os
from collections import Counter

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    NORMALIZED_PRODUCTS_OUTPUT,
    PRODUCTS_OUTPUT_FILE
)


class ResultsAnalyzer:
    """Analyze matching results and generate quality reports"""
    
    def __init__(self):
        """Initialize analyzer"""
        self.df_products = None
        self.df_normalized = None
    
    def load_results(self) -> bool:
        """
        Load processing results from output files
        
        Returns:
            True if successful, False otherwise
        """
        print("="*70)
        print("LOADING RESULTS")
        print("="*70)
        print()
        
        # Load normalized products
        if not os.path.exists(NORMALIZED_PRODUCTS_OUTPUT):
            print(f"❌ File not found: {NORMALIZED_PRODUCTS_OUTPUT}")
            return False
        
        # Load products
        if not os.path.exists(PRODUCTS_OUTPUT_FILE):
            print(f"❌ File not found: {PRODUCTS_OUTPUT_FILE}")
            return False
        
        try:
            self.df_normalized = pd.read_csv(NORMALIZED_PRODUCTS_OUTPUT)
            self.df_products = pd.read_csv(PRODUCTS_OUTPUT_FILE)
            
            print(f"✅ Loaded normalized products")
            print(f"✅ Loaded products with mappings")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading files: {e}")
            return False
    
    def analyze_match_distribution(self):
        """Analyze how products are distributed across normalized products"""
        print("="*70)
        print("MATCH DISTRIBUTION ANALYSIS")
        print("="*70)
        print()
        
        # Count products per normalized_product
        products_per_normalized = self.df_products['product_id'].value_counts()
        
        print("Products per Normalized Product:")
        print(f"  Mean:     {products_per_normalized.mean():.2f}")
        print(f"  Median:   {products_per_normalized.median():.0f}")
        print(f"  Max:      {products_per_normalized.max()}")
        print(f"  Min:      {products_per_normalized.min()}")
        print()
        
        # Distribution breakdown
        print("Distribution Breakdown:")
        
        singles = (products_per_normalized == 1).sum()
        doubles = (products_per_normalized == 2).sum()
        triples = (products_per_normalized == 3).sum()
        quads_plus = (products_per_normalized >= 4).sum()
        
        total = len(products_per_normalized)
        
        print(f"  Single product (no matches):  {singles:>6} ({singles/total*100:>5.1f}%)")
        print(f"  2 products matched:           {doubles:>6} ({doubles/total*100:>5.1f}%)")
        print(f"  3 products matched:           {triples:>6} ({triples/total*100:>5.1f}%)")
        print(f"  4+ products matched:          {quads_plus:>6} ({quads_plus/total*100:>5.1f}%)")
        print()
        
        # Top matched products
        print("Top 10 Most Matched Products:")
        top_matched = products_per_normalized.head(10)
        
        for i, (product_id, count) in enumerate(top_matched.items(), 1):
            # Get product details
            norm_product = self.df_normalized[self.df_normalized['id'] == product_id].iloc[0]
            print(f"  {i:2d}. {norm_product['brand_name']} - {norm_product['product_name'][:40]:40s} ({count} matches)")
        
        print()
    
    def analyze_platform_coverage(self):
        """Analyze how products are distributed across platforms"""
        print("="*70)
        print("PLATFORM COVERAGE ANALYSIS")
        print("="*70)
        print()
        
        if 'platform' not in self.df_products.columns:
            print("⚠️  Platform column not found in products data")
            return
        
        # Products appearing on multiple platforms
        products_by_platform = self.df_products.groupby('product_id')['platform'].apply(list)
        
        multi_platform_count = sum(len(set(platforms)) > 1 for platforms in products_by_platform)
        single_platform_count = sum(len(set(platforms)) == 1 for platforms in products_by_platform)
        
        total = len(products_by_platform)
        
        print("Cross-Platform Products:")
        print(f"  Products on multiple platforms:  {multi_platform_count:>6} ({multi_platform_count/total*100:>5.1f}%)")
        print(f"  Products on single platform:     {single_platform_count:>6} ({single_platform_count/total*100:>5.1f}%)")
        print()
        
        # Platform combinations
        platform_combos = Counter()
        for platforms in products_by_platform:
            platform_set = tuple(sorted(set(platforms)))
            platform_combos[platform_set] += 1
        
        print("Top Platform Combinations:")
        for i, (combo, count) in enumerate(platform_combos.most_common(10), 1):
            combo_str = " + ".join(combo)
            print(f"  {i:2d}. {combo_str:40s} {count:>6} products")
        
        print()
    
    def analyze_brand_coverage(self):
        """Analyze brand distribution"""
        print("="*70)
        print("BRAND ANALYSIS")
        print("="*70)
        print()
        
        if 'normalized_brand' in self.df_products.columns:
            brand_counts = self.df_products['normalized_brand'].value_counts()
            
            print(f"Total Unique Brands: {len(brand_counts)}")
            print()
            
            print("Top 15 Brands by Product Count:")
            for i, (brand, count) in enumerate(brand_counts.head(15).items(), 1):
                print(f"  {i:2d}. {brand:30s} {count:>6} products")
            
            print()
    
    def analyze_quantity_patterns(self):
        """Analyze quantity patterns in matched products"""
        print("="*70)
        print("QUANTITY PATTERN ANALYSIS")
        print("="*70)
        print()
        
        # Products with quantities
        has_quantity = self.df_products['quantity'].notna().sum()
        total = len(self.df_products)
        
        print(f"Products with quantity information: {has_quantity} ({has_quantity/total*100:.1f}%)")
        print()
        
        # Most common quantities
        if has_quantity > 0:
            quantity_counts = self.df_products['quantity'].value_counts().head(15)
            
            print("Top 15 Most Common Quantities:")
            for i, (qty, count) in enumerate(quantity_counts.items(), 1):
                print(f"  {i:2d}. {qty:20s} {count:>6} products")
            
            print()
    
    def find_potential_false_negatives(self, sample_size: int = 10):
        """
        Find products that might be the same but weren't matched
        (same brand + similar product name but different product_id)
        
        Args:
            sample_size: Number of examples to show
        """
        print("="*70)
        print("POTENTIAL FALSE NEGATIVES (Manual Review Needed)")
        print("="*70)
        print()
        
        print("These products have the same brand and similar names but weren't matched:")
        print("This could indicate issues with normalization or need for fuzzy matching.")
        print()
        
        # Group by normalized brand
        if 'normalized_brand' not in self.df_products.columns:
            print("⚠️  Normalized brand column not found")
            return
        
        candidates = []
        
        for brand in self.df_products['normalized_brand'].unique()[:50]:  # Check first 50 brands
            brand_products = self.df_products[self.df_products['normalized_brand'] == brand]
            
            if len(brand_products) < 2:
                continue
            
            # Group by product_id
            product_groups = brand_products.groupby('product_id')
            
            if len(product_groups) < 2:
                continue
            
            # Compare product names within same brand
            for pid1, group1 in product_groups:
                name1 = group1.iloc[0]['normalized_product']
                
                for pid2, group2 in product_groups:
                    if pid1 >= pid2:
                        continue
                    
                    name2 = group2.iloc[0]['normalized_product']
                    
                    # Simple similarity check (word overlap)
                    words1 = set(str(name1).split())
                    words2 = set(str(name2).split())
                    
                    if len(words1) == 0 or len(words2) == 0:
                        continue
                    
                    overlap = len(words1 & words2)
                    min_words = min(len(words1), len(words2))
                    
                    if min_words > 0:
                        similarity = overlap / min_words
                        
                        # High similarity but different product_id
                        if similarity >= 0.7:
                            candidates.append({
                                'brand': brand,
                                'name1': name1,
                                'name2': name2,
                                'similarity': similarity,
                                'count1': len(group1),
                                'count2': len(group2)
                            })
        
        # Sort by similarity
        candidates.sort(key=lambda x: x['similarity'], reverse=True)
        
        for i, candidate in enumerate(candidates[:sample_size], 1):
            print(f"Example {i}:")
            print(f"  Brand: {candidate['brand']}")
            print(f"  Product 1: {candidate['name1']} ({candidate['count1']} variants)")
            print(f"  Product 2: {candidate['name2']} ({candidate['count2']} variants)")
            print(f"  Similarity: {candidate['similarity']*100:.0f}%")
            print()
    
    def generate_quality_report(self):
        """Generate overall quality assessment"""
        print("="*70)
        print("QUALITY ASSESSMENT")
        print("="*70)
        print()
        
        total_products = len(self.df_products)
        total_normalized = len(self.df_normalized)
        
        reduction_ratio = (1 - total_normalized / total_products) * 100
        
        print("Overall Metrics:")
        print(f"  Input Products:       {total_products}")
        print(f"  Normalized Products:  {total_normalized}")
        print(f"  Reduction:            {reduction_ratio:.2f}%")
        print()
        
        # Products per normalized (average matching)
        products_per_normalized = self.df_products['product_id'].value_counts()
        avg_matches = products_per_normalized.mean()
        
        print("Matching Quality:")
        print(f"  Average products per normalized: {avg_matches:.2f}")
        print()
        
        # Assessment
        print("Assessment:")
        
        if reduction_ratio < 10:
            print("  ⚠️  Low reduction ratio - most products are unique")
            print("      → This is expected for Stage 1 (fingerprint matching)")
            print("      → Stage 2 (fuzzy matching) will improve this")
        elif reduction_ratio < 30:
            print("  ✅ Moderate reduction - fingerprint matching working")
            print("      → Fuzzy matching in Stage 2 will find more matches")
        else:
            print("  ✅ Good reduction - many exact matches found")
        
        print()
        
        if avg_matches < 1.5:
            print("  ⚠️  Few products matched together")
            print("      → Most normalized products represent single variants")
            print("      → Normal for Stage 1, will improve in Stage 2")
        else:
            print("  ✅ Products being matched across platforms")
        
        print()
    
    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        print("\n")
        print("📊 STARTING RESULTS ANALYSIS")
        print("="*70)
        print()
        
        if not self.load_results():
            return False
        
        # Run all analyses
        self.analyze_match_distribution()
        self.analyze_platform_coverage()
        self.analyze_brand_coverage()
        self.analyze_quantity_patterns()
        self.find_potential_false_negatives(sample_size=5)
        self.generate_quality_report()
        
        print("="*70)
        print("✅ ANALYSIS COMPLETE")
        print("="*70)
        print()
        
        return True


def main():
    """Main execution"""
    analyzer = ResultsAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()