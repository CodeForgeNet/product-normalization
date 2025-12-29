"""
Output Formatter - Format data for database import

File Location: product-normalization-hackathon/src/output_formatter.py

This module formats processed data into database-ready CSV files.
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    NORMALIZED_PRODUCTS_OUTPUT,
    PRODUCTS_OUTPUT_FILE
)


class OutputFormatter:
    """Format processed data for database import"""
    
    def __init__(self):
        """Initialize formatter"""
        self.df_products = None
        self.df_normalized = None
    
    def load_processed_data(self) -> bool:
        """
        Load processed data from CSV files
        
        Returns:
            True if successful
        """
        print("="*70)
        print("LOADING PROCESSED DATA")
        print("="*70)
        print()
        
        if not os.path.exists(NORMALIZED_PRODUCTS_OUTPUT):
            print(f"❌ Normalized products file not found: {NORMALIZED_PRODUCTS_OUTPUT}")
            return False
        
        if not os.path.exists(PRODUCTS_OUTPUT_FILE):
            print(f"❌ Products file not found: {PRODUCTS_OUTPUT_FILE}")
            return False
        
        try:
            self.df_normalized = pd.read_csv(NORMALIZED_PRODUCTS_OUTPUT)
            self.df_products = pd.read_csv(PRODUCTS_OUTPUT_FILE)
            
            print(f"✅ Loaded normalized products")
            print(f"✅ Loaded products")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading files: {e}")
            return False
    
    def format_normalized_products(self) -> pd.DataFrame:
        """
        Format normalized_products for SQL Server import
        
        Returns:
            Formatted DataFrame
        """
        print("="*70)
        print("FORMATTING NORMALIZED PRODUCTS")
        print("="*70)
        print()
        
        # Create a copy
        df = self.df_normalized.copy()
        
        # Ensure required columns exist
        required_columns = ['id', 'fingerprint', 'brand_name', 'product_name']
        
        for col in required_columns:
            if col not in df.columns:
                print(f"⚠️  Missing required column: {col}")
        
        # Add vector column (placeholder for Phase 5 embeddings)
        if 'vector' not in df.columns:
            df['vector'] = None
        
        # Add category if missing
        if 'category' not in df.columns:
            df['category'] = None
        
        # Add updated_at timestamp
        if 'updated_at' not in df.columns:
            df['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Reorder columns to match database schema
        column_order = [
            'id',
            'fingerprint',
            'vector',
            'brand_name',
            'product_name',
            'quantity',
            'category',
            'updated_at'
        ]
        
        # Only include columns that exist
        final_columns = [col for col in column_order if col in df.columns]
        df = df[final_columns]
        
        # Handle NULL values
        df = df.fillna('')
        
        # Ensure text fields are strings
        text_columns = ['fingerprint', 'brand_name', 'product_name', 'quantity', 'category']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        print(f"✅ Formatted {len(df)} normalized products")
        print(f"   Columns: {list(df.columns)}")
        print()
        
        return df
    
    def format_products(self) -> pd.DataFrame:
        """
        Format products for SQL Server import
        
        Returns:
            Formatted DataFrame
        """
        print("="*70)
        print("FORMATTING PRODUCTS")
        print("="*70)
        print()
        
        # Create a copy
        df = self.df_products.copy()
        
        # Ensure required columns
        required_columns = ['id', 'platform', 'product_id', 'brand_name', 'product_name']
        
        for col in required_columns:
            if col not in df.columns:
                print(f"⚠️  Missing required column: {col}")
        
        # Add missing columns with defaults
        if 'platform_url' not in df.columns:
            df['platform_url'] = ''
        
        if 'mrp' not in df.columns:
            df['mrp'] = 0.0
        
        if 'price' not in df.columns:
            df['price'] = 0.0
        
        if 'discount' not in df.columns:
            df['discount'] = 0.0
        
        if 'image_url' not in df.columns:
            df['image_url'] = ''
        
        if 'available' not in df.columns:
            df['available'] = 1
        
        if 'updated_at' not in df.columns:
            df['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if 'created_at' not in df.columns:
            df['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if 'search' not in df.columns:
            df['search'] = ''
        
        # Reorder columns to match database schema
        column_order = [
            'id',
            'platform',
            'platform_url',
            'product_id',
            'brand_name',
            'product_name',
            'mrp',
            'price',
            'discount',
            'quantity',
            'category',
            'image_url',
            'available',
            'updated_at',
            'created_at',
            'search'
        ]
        
        # Only include columns that exist
        final_columns = [col for col in column_order if col in df.columns]
        df = df[final_columns]
        
        # Handle NULL values
        df = df.fillna('')
        
        # Ensure numeric fields are correct type
        numeric_columns = ['mrp', 'price', 'discount']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        # Ensure available is boolean/int
        if 'available' in df.columns:
            df['available'] = df['available'].astype(int)
        
        print(f"✅ Formatted {len(df)} products")
        print(f"   Columns: {list(df.columns)}")
        print()
        
        return df
    
    def save_formatted_outputs(self, normalized_df: pd.DataFrame, products_df: pd.DataFrame):
        """
        Save formatted DataFrames to CSV
        
        Args:
            normalized_df: Formatted normalized products
            products_df: Formatted products
        """
        print("="*70)
        print("SAVING FORMATTED OUTPUTS")
        print("="*70)
        print()
        
        # Save normalized products
        output_normalized = NORMALIZED_PRODUCTS_OUTPUT.replace('.csv', '_formatted.csv')
        normalized_df.to_csv(output_normalized, index=False, encoding='utf-8-sig')
        print(f"✅ Saved: {output_normalized}")
        
        # Save products
        output_products = PRODUCTS_OUTPUT_FILE.replace('.csv', '_formatted.csv')
        products_df.to_csv(output_products, index=False, encoding='utf-8-sig')
        print(f"✅ Saved: {output_products}")
        
        print()
        
        return output_normalized, output_products
    
    def generate_sample_data(self, sample_size: int = 100):
        """
        Generate sample data files for testing
        
        Args:
            sample_size: Number of records in sample
        """
        print("="*70)
        print("GENERATING SAMPLE DATA")
        print("="*70)
        print()
        
        # Sample from normalized products
        sample_normalized = self.df_normalized.head(sample_size)
        sample_file = NORMALIZED_PRODUCTS_OUTPUT.replace('.csv', '_sample.csv')
        sample_normalized.to_csv(sample_file, index=False)
        print(f"✅ Saved sample: {sample_file}")
        
        # Sample from products (get products matching the sampled normalized products)
        sample_ids = sample_normalized['id'].tolist()
        sample_products = self.df_products[self.df_products['product_id'].isin(sample_ids)]
        sample_file = PRODUCTS_OUTPUT_FILE.replace('.csv', '_sample.csv')
        sample_products.to_csv(sample_file, index=False)
        print(f"✅ Saved sample: {sample_file}")
        
        print()
    
    def validate_data_integrity(self) -> bool:
        """
        Validate data integrity between products and normalized_products
        
        Returns:
            True if validation passes
        """
        print("="*70)
        print("VALIDATING DATA INTEGRITY")
        print("="*70)
        print()
        
        issues = []
        
        # Check 1: All product_ids in products exist in normalized_products
        product_ids = set(self.df_products['product_id'].unique())
        normalized_ids = set(self.df_normalized['id'].unique())
        
        orphaned_ids = product_ids - normalized_ids
        
        if orphaned_ids:
            issues.append(f"Found {len(orphaned_ids)} orphaned product_ids in products table")
        else:
            print("✅ All product_ids reference valid normalized products")
        
        # Check 2: No duplicate IDs in normalized_products
        duplicate_ids = self.df_normalized[self.df_normalized['id'].duplicated()]
        
        if len(duplicate_ids) > 0:
            issues.append(f"Found {len(duplicate_ids)} duplicate IDs in normalized_products")
        else:
            print("✅ No duplicate IDs in normalized_products")
        
        # Check 3: No duplicate fingerprints
        duplicate_fingerprints = self.df_normalized[self.df_normalized['fingerprint'].duplicated()]
        
        if len(duplicate_fingerprints) > 0:
            issues.append(f"Found {len(duplicate_fingerprints)} duplicate fingerprints")
        else:
            print("✅ No duplicate fingerprints")
        
        # Check 4: Required fields are not empty
        required_fields = ['brand_name', 'product_name']
        
        for field in required_fields:
            if field in self.df_normalized.columns:
                empty_count = self.df_normalized[field].isna().sum() + (self.df_normalized[field] == '').sum()
                if empty_count > 0:
                    issues.append(f"Found {empty_count} empty values in {field}")
                else:
                    print(f"✅ No empty values in {field}")
        
        print()
        
        if issues:
            print("❌ VALIDATION FAILED:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ ALL VALIDATIONS PASSED")
            return True
        
        print()
    
    def run_formatting(self):
        """Run complete formatting pipeline"""
        print("\n")
        print("🎨 STARTING OUTPUT FORMATTING")
        print("="*70)
        print()
        
        # Load data
        if not self.load_processed_data():
            return False
        
        # Validate integrity
        self.validate_data_integrity()
        
        # Format data
        normalized_formatted = self.format_normalized_products()
        products_formatted = self.format_products()
        
        # Save formatted outputs
        self.save_formatted_outputs(normalized_formatted, products_formatted)
        
        # Generate samples
        self.generate_sample_data(sample_size=100)
        
        print("="*70)
        print("✅ FORMATTING COMPLETE")
        print("="*70)
        print()
        
        return True


def main():
    """Main execution"""
    formatter = OutputFormatter()
    formatter.run_formatting()


if __name__ == "__main__":
    main()