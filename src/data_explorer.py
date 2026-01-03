import pandas as pd
import re
from collections import Counter
import json
import os

class DataExplorer:

    def __init__(self, csv_path):
        print(f"📂 Loading data from: {csv_path}")
        self.df = pd.read_csv(csv_path)
        self.analysis_results = {}
        print(f"✅ Loaded {len(self.df):,} products")
        print()
    
    def basic_overview(self):
        print("="*70)
        print("1. BASIC DATASET OVERVIEW")
        print("="*70)
        
        results = {
            'total_products': len(self.df),
            'total_columns': len(self.df.columns),
            'columns': list(self.df.columns),
            'missing_values': {}
        }
        
        print(f"Total Products: {results['total_products']:,}")
        print(f"Total Columns: {results['total_columns']}")
        print()
        
        print("Columns:")
        for i, col in enumerate(self.df.columns, 1):
            missing = self.df[col].isna().sum()
            missing_pct = (missing / len(self.df)) * 100
            results['missing_values'][col] = {
                'count': int(missing),
                'percentage': round(missing_pct, 2)
            }
            print(f"  {i:2d}. {col:25s} - Missing: {missing:4d} ({missing_pct:.1f}%)")
        
        print()
        self.analysis_results['basic_overview'] = results
        return results
    
    def analyze_brands(self):
        print("="*70)
        print("2. BRAND ANALYSIS")
        print("="*70)
        
        if 'brand_name' not in self.df.columns:
            print("❌ 'brand_name' column not found!")
            return None
        
        brands = self.df['brand_name'].dropna()
        unique_brands = brands.nunique()
        
        print(f"Total Unique Brands: {unique_brands:,}")
        print()
        
        print("Top 20 Brands by Product Count:")
        top_brands = brands.value_counts().head(20)
        for i, (brand, count) in enumerate(top_brands.items(), 1):
            print(f"  {i:2d}. {brand:30s} - {count:4d} products")
        
        print()
        
        print("Potential Brand Variations (for aliases):")
        brand_variations = self._find_brand_variations(brands.unique())
        
        for base_brand, variations in list(brand_variations.items())[:15]:
            if variations:
                print(f"  '{base_brand}':")
                for var in variations[:3]:  
                    print(f"    → {var}")
        
        print()
        
        results = {
            'unique_brands': unique_brands,
            'top_brands': top_brands.to_dict(),
            'brand_variations': brand_variations
        }
        
        self.analysis_results['brand_analysis'] = results
        return results
    
    def _find_brand_variations(self, brands):
        variations = {}
        brands_lower = {b: b.lower().strip() for b in brands}
        
        for brand, brand_lower in brands_lower.items():
            similar = []
            for other_brand, other_lower in brands_lower.items():
                if brand != other_brand:
                    if brand_lower in other_lower or other_lower in brand_lower:
                        similar.append(other_brand)
                    elif self._has_common_words(brand_lower, other_lower):
                        similar.append(other_brand)
            
            if similar:
                variations[brand] = similar
        
        return variations
    
    def _has_common_words(self, str1, str2):
        words1 = set(str1.split())
        words2 = set(str2.split())
        common = words1 & words2
        return len(common) >= 2  
    
    def analyze_product_names(self):
        print("="*70)
        print("3. PRODUCT NAME ANALYSIS")
        print("="*70)
        
        if 'product_name' not in self.df.columns:
            print("❌ 'product_name' column not found!")
            return None
        
        products = self.df['product_name'].dropna()
        
        print(f"Total Unique Product Names: {products.nunique():,}")
        print()
        
        all_words = []
        for product in products:
            words = re.findall(r'\b[a-zA-Z]+\b', str(product).lower())
            all_words.extend(words)
        
        word_freq = Counter(all_words)
        
        print("Most Common Words in Product Names (potential stop words):")
        for word, count in word_freq.most_common(30):
            print(f"  {word:15s} - {count:5d} occurrences")
        
        print()
        
        packaging_terms = [
            'pack', 'bottle', 'jar', 'box', 'tin', 'pouch', 'combo',
            'set', 'packet', 'piece', 'pcs', 'container', 'can'
        ]
        
        print("Packaging Terms Found:")
        packaging_found = {}
        for term in packaging_terms:
            count = sum(1 for p in products if term in str(p).lower())
            if count > 0:
                packaging_found[term] = count
                print(f"  {term:15s} - {count:5d} products")
        
        print()
        
        results = {
            'unique_products': products.nunique(),
            'common_words': dict(word_freq.most_common(50)),
            'packaging_terms': packaging_found
        }
        
        self.analysis_results['product_name_analysis'] = results
        return results
    
    def analyze_quantities(self):
        print("="*70)
        print("4. QUANTITY ANALYSIS")
        print("="*70)
        
        if 'quantity' not in self.df.columns:
            print("❌ 'quantity' column not found!")
            print("   Checking if quantity is embedded in product_name...")
            self._extract_quantities_from_names()
            return None
        
        quantities = self.df['quantity'].dropna()
        
        print(f"Products with Quantity Info: {len(quantities):,} ({len(quantities)/len(self.df)*100:.1f}%)")
        print()
        
        patterns = {
            'weight_kg': r'(\d+\.?\d*)\s*(kg|kgs)',
            'weight_g': r'(\d+\.?\d*)\s*(g|gm|gms|gram|grams)',
            'volume_l': r'(\d+\.?\d*)\s*(l|ltr|litre|litres|liter|liters)',
            'volume_ml': r'(\d+\.?\d*)\s*(ml|milliliter|millilitre)',
            'count': r'(\d+)\s*(pack|piece|pcs|pc)',
            'multipack': r'(\d+)\s*x\s*(\d+\.?\d*)\s*([a-z]+)'
        }
        
        pattern_matches = {}
        
        for pattern_name, pattern in patterns.items():
            matches = []
            for qty in quantities:
                match = re.search(pattern, str(qty).lower())
                if match:
                    matches.append(match.group(0))
            
            if matches:
                pattern_matches[pattern_name] = {
                    'count': len(matches),
                    'examples': list(set(matches))[:10]
                }
        
        print("Quantity Patterns Found:")
        for pattern_name, data in pattern_matches.items():
            print(f"\n  {pattern_name.upper()} ({data['count']} occurrences):")
            print(f"    Examples: {', '.join(data['examples'][:5])}")
        
        print()
        

        print("Sample Quantities (first 20 unique):")
        for i, qty in enumerate(quantities.unique()[:20], 1):
            print(f"  {i:2d}. {qty}")
        
        print()
        
        results = {
            'products_with_quantity': len(quantities),
            'patterns': pattern_matches,
            'unique_quantities': len(quantities.unique()),
            'sample_quantities': list(quantities.unique()[:50])
        }
        
        self.analysis_results['quantity_analysis'] = results
        return results
    
    def _extract_quantities_from_names(self):

        print("   Attempting to extract from product_name column...")
        
        if 'product_name' not in self.df.columns:
            return
        
        qty_pattern = r'(\d+\.?\d*)\s*(kg|g|gm|l|ml|litre|liter)'
        
        quantities_found = 0
        examples = []
        
        for product in self.df['product_name'].dropna():
            match = re.search(qty_pattern, str(product).lower())
            if match:
                quantities_found += 1
                if len(examples) < 10:
                    examples.append(match.group(0))
        
        print(f"   Found quantity info in {quantities_found} product names")
        if examples:
            print(f"   Examples: {', '.join(examples[:5])}")
        print()
    
    def analyze_platforms(self):

        print("="*70)
        print("5. PLATFORM ANALYSIS")
        print("="*70)
        
        if 'platform' not in self.df.columns:
            print("❌ 'platform' column not found!")
            return None
        
        platforms = self.df['platform'].value_counts()
        
        print("Products per Platform:")
        for platform, count in platforms.items():
            pct = (count / len(self.df)) * 100
            print(f"  {platform:15s} - {count:5d} products ({pct:.1f}%)")
        
        print()
        
        results = {
            'platforms': platforms.to_dict(),
            'total_platforms': len(platforms)
        }
        
        self.analysis_results['platform_analysis'] = results
        return results
    
    def analyze_categories(self):

        print("="*70)
        print("6. CATEGORY ANALYSIS")
        print("="*70)
        
        if 'category' not in self.df.columns:
            print("⚠️  'category' column not found - skipping category analysis")
            print()
            return None
        
        categories = self.df['category'].dropna()
        unique_categories = categories.nunique()
        
        print(f"Total Unique Categories: {unique_categories:,}")
        print()
        
        print("Top 15 Categories:")
        top_categories = categories.value_counts().head(15)
        for i, (category, count) in enumerate(top_categories.items(), 1):
            print(f"  {i:2d}. {category:40s} - {count:4d} products")
        
        print()
        
        results = {
            'unique_categories': unique_categories,
            'top_categories': top_categories.to_dict()
        }
        
        self.analysis_results['category_analysis'] = results
        return results
    
    def find_duplicate_patterns(self):

        print("="*70)
        print("7. DUPLICATE PATTERN ANALYSIS")
        print("="*70)
        
        self.df['brand_lower'] = self.df['brand_name'].str.lower().str.strip()
        self.df['product_lower'] = self.df['product_name'].str.lower().str.strip()
        
        duplicates = self.df.groupby(['brand_lower', 'product_lower']).size()
        duplicates = duplicates[duplicates > 1].sort_values(ascending=False)
        
        print(f"Found {len(duplicates)} product name combinations appearing multiple times")
        print()
        
        if len(duplicates) > 0:
            print("Top 15 Duplicate Patterns (Same Brand + Product Name):")
            for i, ((brand, product), count) in enumerate(duplicates.head(15).items(), 1):
                print(f"  {i:2d}. {brand} - {product[:50]:50s} ({count} occurrences)")
            
            print()
            
            if len(duplicates) > 0:
                first_dup = duplicates.index[0]
                brand, product = first_dup
                
                print("Example: Showing all entries for first duplicate:")
                dup_examples = self.df[
                    (self.df['brand_lower'] == brand) & 
                    (self.df['product_lower'] == product)
                ][['platform', 'brand_name', 'product_name', 'quantity', 'price']]
                
                print(dup_examples.to_string(index=False))
                print()
        
        top_dups_dict = {}
        for (brand, product), count in duplicates.head(20).items():
            key = f"{brand}|||{product}"  
            top_dups_dict[key] = count
        
        results = {
            'duplicate_count': len(duplicates),
            'top_duplicates': top_dups_dict
        }
        
        self.analysis_results['duplicate_analysis'] = results
        return results
    
    def generate_test_cases(self):
        print("="*70)
        print("8. GENERATING TEST CASES")
        print("="*70)
        
        test_cases = []
        
        if 'platform' in self.df.columns:
            self.df['brand_product'] = (
                self.df['brand_name'].str.lower() + '|||' + 
                self.df['product_name'].str.lower()
            )
            
            multi_platform = self.df.groupby('brand_product')['platform'].nunique()
            multi_platform = multi_platform[multi_platform > 1]
            
            print(f"Found {len(multi_platform)} products appearing on multiple platforms")
            print()
            
            print("Sample Test Cases (products that should match):")
            print()
            
            for i, brand_product in enumerate(multi_platform.index[:10], 1):
                matches = self.df[self.df['brand_product'] == brand_product]
                
                if len(matches) >= 2:
                    test_case = {
                        'test_id': i,
                        'should_match': True,
                        'products': []
                    }
                    
                    print(f"Test Case {i}: (Should MATCH)")
                    for idx, row in matches.head(2).iterrows():
                        product_info = {
                            'platform': row['platform'],
                            'brand': row['brand_name'],
                            'product': row['product_name'],
                            'quantity': row.get('quantity', 'N/A')
                        }
                        test_case['products'].append(product_info)
                        print(f"  [{row['platform']:10s}] {row['brand_name']} - {row['product_name']}")
                    
                    test_cases.append(test_case)
                    print()
        
        test_cases_file = 'output/test_cases.json'
        with open(test_cases_file, 'w', encoding='utf-8') as f:
            json.dump(test_cases, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Test cases saved to: {test_cases_file}")
        print()
        
        return test_cases
    
    def run_complete_analysis(self):
        print("\n")
        print("🔍 STARTING COMPLETE DATA EXPLORATION & ANALYSIS")
        print("="*70)
        print()
        
        self.basic_overview()
        self.analyze_brands()
        self.analyze_product_names()
        self.analyze_quantities()
        self.analyze_platforms()
        self.analyze_categories()
        self.find_duplicate_patterns()
        self.generate_test_cases()
        self.save_analysis_report()
        
        print()
        print("Key Findings:")
        print(f"Total Products: {self.analysis_results['basic_overview']['total_products']:,}")
        print(f"Unique Brands: {self.analysis_results['brand_analysis']['unique_brands']:,}")
        print(f"Platforms: {self.analysis_results['platform_analysis']['total_platforms']}")
        
        if 'duplicate_analysis' in self.analysis_results:
            print(f"Potential Duplicates: {self.analysis_results['duplicate_analysis']['duplicate_count']:,}")
        


def main():
    import sys
    import os
    
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app_config import PRODUCTS_INPUT_FILE
    
    if not os.path.exists(PRODUCTS_INPUT_FILE):
        print(f"❌ ERROR: Input file not found: {PRODUCTS_INPUT_FILE}")
        return
    
    explorer = DataExplorer(PRODUCTS_INPUT_FILE)
    explorer.run_complete_analysis()


if __name__ == "__main__":
    main()