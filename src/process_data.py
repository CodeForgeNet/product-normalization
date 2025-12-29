"""
Data Processing Script - Process CSV and generate outputs

File Location: product-normalization-hackathon/src/process_data.py

This script reads the input CSV, processes all products through
the matching pipeline, and generates output files.
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.matcher import ProductMatcher
from config import (
    PRODUCTS_INPUT_FILE,
    NORMALIZED_PRODUCTS_OUTPUT,
    PRODUCTS_OUTPUT_FILE,
    BATCH_SIZE
)


class DataProcessor:
    """Process product data through matching pipeline"""
    
    def __init__(self):
        """Initialize processor with matcher"""
        self.matcher = ProductMatcher()
        self.df_products = None
        self.df_normalized = None
    
    def load_data(self, file_path: str = PRODUCTS_INPUT_FILE) -> bool:
        """
        Load products from CSV file
        
        Args:
            file_path: Path to input CSV file
            
        Returns:
            True if successful, False otherwise
        """
        print("="*70)
        print("LOADING DATA")
        print("="*70)
        print()
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        try:
            print(f"📂 Loading: {file_path}")
            self.df_products = pd.read_csv(file_path)
            print(f"✅ Loaded {len(self.df_products):,} products")
            print()
            
            # Show sample
            print("Sample data:")
            print(self.df_products[['brand_name', 'product_name', 'quantity', 'platform']].head(3))
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return False
    
    def process_all_products(self) -> bool:
        """
        Process all products through matching pipeline
        
        Returns:
            True if successful, False otherwise
        """
        if self.df_products is None:
            print("❌ No data loaded. Call load_data() first.")
            return False
        
        print("="*70)
        print("PROCESSING PRODUCTS")
        print("="*70)
        print()
        
        try:
            # Convert DataFrame to list of dicts
            products = self.df_products.to_dict('records')
            
            # Process through matcher
            start_time = datetime.now()
            
            processed_products = self.matcher.process_products_batch(
                products=products,
                batch_size=BATCH_SIZE
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Convert back to DataFrame
            self.df_products = pd.DataFrame(processed_products)
            
            print(f"✅ Processing complete in {duration:.2f} seconds")
            print(f"   Speed: {len(products)/duration:.0f} products/second")
            print()
            
            # Print statistics
            self.matcher.print_statistics()
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing products: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_normalized_products(self):
        """Generate normalized products DataFrame"""
        print()
        print("="*70)
        print("GENERATING NORMALIZED PRODUCTS")
        print("="*70)
        print()
        
        normalized_data = self.matcher.export_normalized_products_to_dict()
        self.df_normalized = pd.DataFrame(normalized_data)
        
        print(f"✅ Generated {len(self.df_normalized):,} unique normalized products")
        print()
        
        # Show sample
        print("Sample normalized products:")
        print(self.df_normalized[['id', 'brand_name', 'product_name', 'quantity']].head(5))
        print()
    
    def save_outputs(self) -> bool:
        """
        Save processed data to output files
        
        Returns:
            True if successful, False otherwise
        """
        print("="*70)
        print("SAVING OUTPUT FILES")
        print("="*70)
        print()
        
        try:
            # Save normalized products
            print(f"💾 Saving normalized products to: {NORMALIZED_PRODUCTS_OUTPUT}")
            self.df_normalized.to_csv(NORMALIZED_PRODUCTS_OUTPUT, index=False)
            print(f"✅ Saved {len(self.df_normalized):,} normalized products")
            print()
            
            # Save products with product_id
            print(f"💾 Saving products with mappings to: {PRODUCTS_OUTPUT_FILE}")
            self.df_products.to_csv(PRODUCTS_OUTPUT_FILE, index=False)
            print(f"✅ Saved {len(self.df_products):,} products")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving files: {e}")
            return False
    
    def generate_report(self):
        """Generate processing report"""
        print("="*70)
        print("PROCESSING REPORT")
        print("="*70)
        print()
        
        stats = self.matcher.get_statistics()
        
        print("Input:")
        print(f"  Total Products:               {stats['total_products_processed']:>10,}")
        print()
        
        print("Output:")
        print(f"  Unique Normalized Products:   {stats['new_normalized_products']:>10,}")
        print(f"  Products Matched:             {stats['fingerprint_matches']:>10,}")
        print()
        
        print("Quality Metrics:")
        print(f"  Match Rate:                   {stats['match_rate_percent']:>10.2f}%")
        print(f"  Failed Normalizations:        {stats['failed_normalizations']:>10,}")
        print()
        
        # Reduction ratio
        reduction = 0
        if stats['total_products_processed'] > 0:
            reduction = (1 - stats['new_normalized_products'] / stats['total_products_processed']) * 100
        
        print(f"  Reduction Ratio:              {reduction:>10.2f}%")
        print(f"  (Reduced from {stats['total_products_processed']:,} to {stats['new_normalized_products']:,} unique products)")
        print()
        
        # Platform distribution
        if 'platform' in self.df_products.columns:
            print("Platform Distribution:")
            platform_counts = self.df_products['platform'].value_counts()
            for platform, count in platform_counts.items():
                print(f"  {platform:20s} {count:>10,} products")
            print()
        
        # Top brands
        if 'normalized_brand' in self.df_products.columns:
            print("Top 10 Brands (by product count):")
            top_brands = self.df_products['normalized_brand'].value_counts().head(10)
            for i, (brand, count) in enumerate(top_brands.items(), 1):
                print(f"  {i:2d}. {brand:30s} {count:>6,} products")
            print()
        
        print("="*70)
    
    def run_full_pipeline(self) -> bool:
        """
        Run the complete processing pipeline
        
        Returns:
            True if successful, False otherwise
        """
        print("\n")
        print("🚀 STARTING FULL PROCESSING PIPELINE")
        print("="*70)
        print()
        
        # Step 1: Load data
        if not self.load_data():
            return False
        
        # Step 2: Process products
        if not self.process_all_products():
            return False
        
        # Step 3: Generate normalized products
        self.generate_normalized_products()
        
        # Step 4: Save outputs
        if not self.save_outputs():
            return False
        
        # Step 5: Generate report
        self.generate_report()
        
        print("="*70)
        print("✅ PIPELINE COMPLETE!")
        print("="*70)
        print()
        
        print("Output files generated:")
        print(f"  📄 {NORMALIZED_PRODUCTS_OUTPUT}")
        print(f"  📄 {PRODUCTS_OUTPUT_FILE}")
        print()
        
        return True


def main():
    """Main execution function"""
    processor = DataProcessor()
    success = processor.run_full_pipeline()
    
    if success:
        print("🎉 Processing completed successfully!")
    else:
        print("❌ Processing failed. Check errors above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)