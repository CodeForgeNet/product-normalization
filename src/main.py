"""
Main execution script for product normalization
"""

import pandas as pd
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from config import *

def main():
    """Main execution function"""
    
    print("="*70)
    print(" Product Normalization & Combination System")
    print("="*70)
    print()
    
    # Step 1: Load data
    print("📂 Loading data...")
    try:
        df_products = pd.read_csv(PRODUCTS_INPUT_FILE)
        print(f"✅ Loaded {len(df_products)} products from {PRODUCTS_INPUT_FILE}")
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {PRODUCTS_INPUT_FILE}")
        print("   Please place products_table.csv in the data/ folder")
        return
    except Exception as e:
        print(f"❌ ERROR loading data: {e}")
        return
    
    print()
    print("Dataset Overview:")
    print(f"  Total Products: {len(df_products)}")
    print(f"  Columns: {list(df_products.columns)}")
    print(f"  Unique Brands: {df_products['brand_name'].nunique()}")
    print(f"  Platforms: {df_products['platform'].unique()}")
    
    print()
    print("✅ Phase 0 Complete - Setup Successful!")
    print()
    print("Next Steps:")
    print("  - Phase 1: Run data exploration")
    print("  - Phase 2: Implement normalization functions")

if __name__ == "__main__":
    main()