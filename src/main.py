import pandas as pd
import sys
import time
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from config import *
from normalizer import normalize_brand, normalize_product_name, normalize_quantity, create_fingerprint
from matcher import find_or_create_normalized_product
from config.database import DatabaseManager

def print_header():
    """Print application header"""
    print("=" * 80)
    print(" " * 20 + "PRODUCT NORMALIZATION & COMBINATION SYSTEM")
    print("=" * 80)
    print()

def print_section(title):
    """Print section header"""
    print()
    print(f"{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}")

def load_products(file_path):
    """Load products from CSV file"""
    print_section("📂 LOADING INPUT DATA")
    
    try:
        df_products = pd.read_csv(file_path)
        print(f"✅ Successfully loaded {len(df_products):,} products from {file_path}")
        
        # Data validation
        required_columns = ['brand_name', 'product_name', 'platform']
        missing_cols = [col for col in required_columns if col not in df_products.columns]
        
        if missing_cols:
            print(f"❌ ERROR: Missing required columns: {missing_cols}")
            return None
            
        return df_products
        
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {file_path}")
        print(f"   Please place 'products_table.csv' in the data/ folder")
        return None
    except Exception as e:
        print(f"❌ ERROR loading data: {e}")
        return None

def display_data_summary(df):
    """Display dataset summary statistics"""
    print()
    print("📊 DATASET OVERVIEW:")
    print(f"   ├─ Total Products: {len(df):,}")
    print(f"   ├─ Columns: {len(df.columns)}")
    print(f"   ├─ Unique Brands: {df['brand_name'].nunique():,}")
    print(f"   ├─ Unique Products: {df['product_name'].nunique():,}")
    print(f"   ├─ Platforms: {', '.join(df['platform'].unique())}")
    
    if 'category' in df.columns:
        print(f"   ├─ Categories: {df['category'].nunique():,}")
    
    print(f"   └─ Date Range: {df['created_at'].min() if 'created_at' in df.columns else 'N/A'} to {df['created_at'].max() if 'created_at' in df.columns else 'N/A'}")

def normalize_products(df):
    """Apply normalization to all products"""
    print_section("🧹 NORMALIZING PRODUCTS")
    
    start_time = time.time()
    
    print("   Processing brand names...")
    df['brand_normalized'] = df['brand_name'].apply(normalize_brand)
    
    print("   Processing product names...")
    df['product_normalized'] = df['product_name'].apply(normalize_product_name)
    
    print("   Processing quantities...")
    df['quantity_normalized'] = df['quantity'].apply(normalize_quantity) if 'quantity' in df.columns else None
    
    print("   Generating fingerprints...")
    df['fingerprint'] = df.apply(
        lambda row: create_fingerprint(
            row['brand_normalized'], 
            row['product_normalized'],
            row['quantity_normalized'] if 'quantity_normalized' in row and pd.notna(row['quantity_normalized']) else ''
        ), 
        axis=1
    )
    
    elapsed = time.time() - start_time
    print(f"✅ Normalized {len(df):,} products in {elapsed:.2f}s")
    
    return df

def process_matching(df, db_manager):
    """Process product matching through multiple stages"""
    print_section("🔍 PRODUCT MATCHING")
    
    stats = {
        'stage1_matches': 0,
        'stage2_matches': 0,
        'new_products': 0,
        'total_processed': len(df)
    }
    
    print(f"   Processing {len(df):,} products...")
    print()
    
    start_time = time.time()
    
    # Process each product
    for idx, row in df.iterrows():
        if (idx + 1) % 100 == 0:
            print(f"   Progress: {idx + 1:,}/{len(df):,} ({(idx + 1) / len(df) * 100:.1f}%)", end='\r')
        
        product_id, match_stage = find_or_create_normalized_product(
            row=row,
            db_manager=db_manager
        )
        
        # Update statistics
        if match_stage == 'fingerprint':
            stats['stage1_matches'] += 1
        elif match_stage == 'fuzzy':
            stats['stage2_matches'] += 1
        elif match_stage == 'new':
            stats['new_products'] += 1
        
        # Store product_id back to dataframe
        df.at[idx, 'product_id'] = product_id
    
    print()  # Clear progress line
    elapsed = time.time() - start_time
    
    print()
    print("✅ MATCHING COMPLETE")
    print()
    print("📊 MATCHING STATISTICS:")
    print(f"   ├─ Stage 1 (Fingerprint): {stats['stage1_matches']:,} ({stats['stage1_matches']/stats['total_processed']*100:.1f}%)")
    print(f"   ├─ Stage 2 (Fuzzy Match): {stats['stage2_matches']:,} ({stats['stage2_matches']/stats['total_processed']*100:.1f}%)")
    print(f"   ├─ New Products Created: {stats['new_products']:,} ({stats['new_products']/stats['total_processed']*100:.1f}%)")
    print(f"   ├─ Total Processed: {stats['total_processed']:,}")
    print(f"   └─ Processing Time: {elapsed:.2f}s ({stats['total_processed']/elapsed:.0f} products/sec)")
    
    return df, stats

def save_outputs(df, db_manager):
    """Save output files"""
    print_section("💾 SAVING OUTPUTS")
    
    try:
        # Create output directory if it doesn't exist
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Export normalized products
        normalized_df = db_manager.export_normalized_products()
        normalized_output = OUTPUT_DIR / "normalized_products.csv"
        normalized_df.to_csv(normalized_output, index=False)
        print(f"✅ Saved {len(normalized_df):,} normalized products to: {normalized_output}")
        
        # Export products with mappings
        products_output = OUTPUT_DIR / "products_updated.csv"
        df.to_csv(products_output, index=False)
        print(f"✅ Saved {len(df):,} products with mappings to: {products_output}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR saving outputs: {e}")
        return False

def print_summary(stats, start_time):
    """Print final summary"""
    print_section("✨ EXECUTION SUMMARY")
    
    total_time = time.time() - start_time
    
    print(f"   ├─ Total Products Processed: {stats['total_processed']:,}")
    print(f"   ├─ Fingerprint Matches: {stats['stage1_matches']:,}")
    print(f"   ├─ Fuzzy Matches: {stats['stage2_matches']:,}")
    print(f"   ├─ New Normalized Products: {stats['new_products']:,}")
    print(f"   ├─ Total Execution Time: {total_time:.2f}s")
    print(f"   └─ Average Speed: {stats['total_processed']/total_time:.0f} products/sec")
    print()
    print("=" * 80)
    print(" " * 30 + "🎉 PROCESSING COMPLETE!")
    print("=" * 80)

def main():
    """Main execution function"""
    
    overall_start = time.time()
    
    print_header()
    
    # Step 1: Load data
    df_products = load_products(PRODUCTS_INPUT_FILE)
    if df_products is None:
        return
    
    display_data_summary(df_products)
    
    # Step 2: Initialize database
    print_section("🔗 DATABASE CONNECTION")
    db_manager = DatabaseManager()
    
    try:
        db_manager.connect()
        print("✅ Connected to PostgreSQL database")
        print(f"   Database: {DB_CONFIG['database']}")
        print(f"   Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    except Exception as e:
        print(f"❌ ERROR: Could not connect to database: {e}")
        print()
        print("💡 TROUBLESHOOTING:")
        print("   1. Ensure Docker container is running: docker-compose up -d")
        print("   2. Check if port 5432 is available")
        print("   3. Stop local PostgreSQL: brew services stop postgresql")
        return
    
    # Step 3: Normalize products
    df_products = normalize_products(df_products)
    
    # Step 4: Process matching
    df_products, stats = process_matching(df_products, db_manager)
    
    # Step 5: Save outputs
    if not save_outputs(df_products, db_manager):
        print("⚠️  Warning: Output files could not be saved")
    
    # Step 6: Close database connection
    db_manager.close()
    print()
    print("🔌 Database connection closed")
    
    # Step 7: Print summary
    print_summary(stats, overall_start)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("⚠️  Process interrupted by user")
        print("=" * 80)
        sys.exit(0)
    except Exception as e:
        print()
        print(f"❌ FATAL ERROR: {e}")
        print("=" * 80)
        sys.exit(1)