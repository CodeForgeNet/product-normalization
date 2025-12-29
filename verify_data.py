import pandas as pd
import os

def verify_csv_files():
    """Verify that CSV files exist and are readable"""
    
    data_dir = 'data'
    
    # Check products_table.csv
    products_file = os.path.join(data_dir, 'products_table.csv')
    
    if not os.path.exists(products_file):
        print(f"❌ ERROR: {products_file} not found!")
        print(f"   Please place products_table.csv in the {data_dir}/ folder")
        return False
    
    try:
        df_products = pd.read_csv(products_file)
        print(f"✅ products_table.csv loaded successfully")
        print(f"   Rows: {len(df_products)}")
        print(f"   Columns: {list(df_products.columns)}")
        print()
        
        # Show first few rows
        print("First 3 rows:")
        print(df_products.head(3))
        print()
        
        # Check for required columns
        required_cols = ['brand_name', 'product_name', 'platform']
        missing_cols = [col for col in required_cols if col not in df_products.columns]
        
        if missing_cols:
            print(f"⚠️  WARNING: Missing columns: {missing_cols}")
        else:
            print(f"✅ All required columns present")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR reading CSV: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("CSV Data Verification")
    print("="*60)
    print()
    
    verify_csv_files()