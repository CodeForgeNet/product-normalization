"""
Product Matching Module - Stage 1: Fingerprint Matching

File Location: product-normalization-hackathon/src/matcher.py

This module implements the fingerprint-based exact matching engine
for identifying duplicate products across platforms.
"""

import sys
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.normalizer import TextNormalizer


class ProductMatcher:
    """
    Stage 1: Fingerprint-based exact matching
    
    This matcher uses normalized fingerprints to identify exact product matches.
    It's the first and fastest stage of the matching pipeline.
    """
    
    def __init__(self):
        """Initialize the matcher with normalizer and storage"""
        self.normalizer = TextNormalizer()
        
        # In-memory storage for normalized products
        # Key: fingerprint, Value: normalized_product dict
        self.fingerprint_index = {}
        
        # Counter for assigning IDs to normalized products
        self.next_normalized_id = 1
        
        # Statistics
        self.stats = {
            'total_products_processed': 0,
            'fingerprint_matches': 0,
            'new_normalized_products': 0,
            'failed_normalizations': 0
        }
    
    # ========================================================================
    # CORE MATCHING LOGIC
    # ========================================================================
    
    def find_or_create_normalized_product(
        self,
        brand_name: str,
        product_name: str,
        quantity: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict:
        """
        Find existing normalized product or create new one using fingerprint
        
        Args:
            brand_name: Raw brand name
            product_name: Raw product name
            quantity: Optional quantity string
            category: Optional category
            
        Returns:
            Dictionary with normalized product info including 'product_id'
            
        Example:
            Input: ("Amul", "Butter 100g", "100g", "Dairy")
            Output: {
                'product_id': 1,
                'brand_name': 'amul',
                'product_name': 'amul butter',
                'quantity': '100g',
                'fingerprint': '100_amul_butter_gram',
                'category': 'Dairy',
                'is_new': False
            }
        """
        self.stats['total_products_processed'] += 1
        
        try:
            # Normalize components
            brand_norm = self.normalizer.normalize_brand(brand_name)
            product_norm = self.normalizer.normalize_product_name(product_name)
            
            # Create fingerprint
            fingerprint = self.normalizer.create_fingerprint(
                brand_name,
                product_name,
                quantity
            )
            
            # Check if fingerprint exists
            if fingerprint in self.fingerprint_index:
                # Match found!
                self.stats['fingerprint_matches'] += 1
                normalized_product = self.fingerprint_index[fingerprint].copy()
                normalized_product['is_new'] = False
                normalized_product['match_type'] = 'fingerprint'
                return normalized_product
            
            # No match - create new normalized product
            normalized_product = self._create_normalized_product(
                brand_norm=brand_norm,
                product_norm=product_norm,
                quantity=quantity,
                category=category,
                fingerprint=fingerprint,
                original_brand=brand_name,
                original_product=product_name
            )
            
            # Store in index
            self.fingerprint_index[fingerprint] = normalized_product
            self.stats['new_normalized_products'] += 1
            
            normalized_product['is_new'] = True
            normalized_product['match_type'] = 'new'
            return normalized_product
            
        except Exception as e:
            self.stats['failed_normalizations'] += 1
            print(f"❌ Error normalizing product: {brand_name} - {product_name}")
            print(f"   Error: {e}")
            return None
    
    def _create_normalized_product(
        self,
        brand_norm: str,
        product_norm: str,
        quantity: Optional[str],
        category: Optional[str],
        fingerprint: str,
        original_brand: str,
        original_product: str
    ) -> Dict:
        """
        Create a new normalized product entry
        
        Args:
            brand_norm: Normalized brand name
            product_norm: Normalized product name
            quantity: Original quantity string
            category: Product category
            fingerprint: Generated fingerprint
            original_brand: Original brand name (for reference)
            original_product: Original product name (for reference)
            
        Returns:
            Dictionary with normalized product information
        """
        normalized_product = {
            'product_id': self.next_normalized_id,
            'fingerprint': fingerprint,
            'brand_name': brand_norm,
            'product_name': product_norm,
            'quantity': quantity if quantity else None,
            'category': category if category else None,
            'created_at': datetime.now().isoformat(),
            'original_brand': original_brand,
            'original_product': original_product
        }
        
        self.next_normalized_id += 1
        return normalized_product
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def process_products_batch(
        self,
        products: List[Dict],
        batch_size: int = 1000
    ) -> List[Dict]:
        """
        Process a batch of products and assign product_ids
        
        Args:
            products: List of product dictionaries with keys:
                      'brand_name', 'product_name', 'quantity', 'category'
            batch_size: Number of products to process at once
            
        Returns:
            List of products with added 'product_id' field
        """
        results = []
        total = len(products)
        
        print(f"📦 Processing {total:,} products in batches of {batch_size:,}...")
        print()
        
        for i in range(0, total, batch_size):
            batch = products[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"  Batch {batch_num}/{total_batches}: Processing {len(batch):,} products...", end=" ")
            
            batch_results = []
            for product in batch:
                normalized = self.find_or_create_normalized_product(
                    brand_name=product.get('brand_name', ''),
                    product_name=product.get('product_name', ''),
                    quantity=product.get('quantity'),
                    category=product.get('category')
                )
                
                if normalized:
                    # Add product_id to original product
                    product_with_id = product.copy()
                    product_with_id['product_id'] = normalized['product_id']
                    product_with_id['normalized_brand'] = normalized['brand_name']
                    product_with_id['normalized_product'] = normalized['product_name']
                    product_with_id['fingerprint'] = normalized['fingerprint']
                    product_with_id['is_new_normalized'] = normalized['is_new']
                    batch_results.append(product_with_id)
            
            results.extend(batch_results)
            print(f"✅ Done")
        
        print()
        return results
    
    # ========================================================================
    # STATISTICS & REPORTING
    # ========================================================================
    
    def get_statistics(self) -> Dict:
        """
        Get matching statistics
        
        Returns:
            Dictionary with statistics
        """
        total_processed = self.stats['total_products_processed']
        fingerprint_matches = self.stats['fingerprint_matches']
        
        match_rate = 0
        if total_processed > 0:
            match_rate = (fingerprint_matches / total_processed) * 100
        
        return {
            'total_products_processed': total_processed,
            'fingerprint_matches': fingerprint_matches,
            'new_normalized_products': self.stats['new_normalized_products'],
            'failed_normalizations': self.stats['failed_normalizations'],
            'match_rate_percent': round(match_rate, 2),
            'unique_fingerprints': len(self.fingerprint_index)
        }
    
    def print_statistics(self):
        """Print detailed matching statistics"""
        stats = self.get_statistics()
        
        print("="*70)
        print("FINGERPRINT MATCHING STATISTICS")
        print("="*70)
        print()
        print(f"Total Products Processed:     {stats['total_products_processed']:>10,}")
        print(f"Fingerprint Matches Found:    {stats['fingerprint_matches']:>10,}")
        print(f"New Normalized Products:      {stats['new_normalized_products']:>10,}")
        print(f"Failed Normalizations:        {stats['failed_normalizations']:>10,}")
        print()
        print(f"Match Rate:                   {stats['match_rate_percent']:>10.2f}%")
        print(f"Unique Fingerprints:          {stats['unique_fingerprints']:>10,}")
        print()
        print("="*70)
    
    def get_normalized_products_list(self) -> List[Dict]:
        """
        Get list of all normalized products
        
        Returns:
            List of normalized product dictionaries
        """
        return list(self.fingerprint_index.values())
    
    def get_normalized_product_by_id(self, product_id: int) -> Optional[Dict]:
        """
        Get normalized product by product_id
        
        Args:
            product_id: Product ID to lookup
            
        Returns:
            Normalized product dict or None
        """
        for normalized_product in self.fingerprint_index.values():
            if normalized_product['product_id'] == product_id:
                return normalized_product
        return None
    
    def get_products_by_fingerprint(self, fingerprint: str) -> Optional[Dict]:
        """
        Get normalized product by fingerprint
        
        Args:
            fingerprint: Fingerprint to lookup
            
        Returns:
            Normalized product dict or None
        """
        return self.fingerprint_index.get(fingerprint)
    
    # ========================================================================
    # EXPORT METHODS
    # ========================================================================
    
    def export_normalized_products_to_dict(self) -> List[Dict]:
        """
        Export normalized products for saving to CSV
        
        Returns:
            List of dictionaries ready for DataFrame conversion
        """
        export_data = []
        
        for normalized_product in self.fingerprint_index.values():
            export_data.append({
                'id': normalized_product['product_id'],
                'fingerprint': normalized_product['fingerprint'],
                'brand_name': normalized_product['brand_name'],
                'product_name': normalized_product['product_name'],
                'quantity': normalized_product.get('quantity', ''),
                'category': normalized_product.get('category', ''),
                'created_at': normalized_product.get('created_at', ''),
                'original_brand': normalized_product.get('original_brand', ''),
                'original_product': normalized_product.get('original_product', '')
            })
        
        return export_data
    
    # ========================================================================
    # DEBUG & INSPECTION
    # ========================================================================
    
    def find_duplicates_by_brand_product(self, limit: int = 10) -> List[Dict]:
        """
        Find products with same brand+product but different quantities
        (these should have different fingerprints)
        
        Args:
            limit: Maximum number of examples to return
            
        Returns:
            List of duplicate groups
        """
        # Group by brand + product (without quantity)
        groups = {}
        
        for normalized in self.fingerprint_index.values():
            key = f"{normalized['brand_name']}|||{normalized['product_name']}"
            if key not in groups:
                groups[key] = []
            groups[key].append(normalized)
        
        # Find groups with multiple entries
        duplicates = []
        for key, items in groups.items():
            if len(items) > 1:
                duplicates.append({
                    'brand_product': key,
                    'count': len(items),
                    'variants': items
                })
        
        # Sort by count descending
        duplicates.sort(key=lambda x: x['count'], reverse=True)
        
        return duplicates[:limit]
    
    def inspect_fingerprint(self, fingerprint: str):
        """
        Inspect a fingerprint and show what it matches
        
        Args:
            fingerprint: Fingerprint to inspect
        """
        product = self.get_products_by_fingerprint(fingerprint)
        
        if product:
            print(f"Fingerprint: {fingerprint}")
            print(f"  Product ID: {product['product_id']}")
            print(f"  Brand: {product['brand_name']}")
            print(f"  Product: {product['product_name']}")
            print(f"  Quantity: {product.get('quantity', 'N/A')}")
            print(f"  Category: {product.get('category', 'N/A')}")
            print(f"  Original Brand: {product.get('original_brand', 'N/A')}")
            print(f"  Original Product: {product.get('original_product', 'N/A')}")
        else:
            print(f"Fingerprint not found: {fingerprint}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_matcher() -> ProductMatcher:
    """Create and return a new ProductMatcher instance"""
    return ProductMatcher()


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("PRODUCT MATCHER MODULE - DEMO")
    print("="*70)
    print()
    
    # Create matcher
    matcher = ProductMatcher()
    
    # Test products
    test_products = [
        # Same product, different platforms
        {'brand_name': 'Amul', 'product_name': 'Butter 100g', 'quantity': '100g', 'category': 'Dairy'},
        {'brand_name': 'Amul', 'product_name': 'Butter Pack 100g', 'quantity': '100 g', 'category': 'Dairy'},
        
        # Same product, different quantities (should NOT match)
        {'brand_name': 'Amul', 'product_name': 'Butter 200g', 'quantity': '200g', 'category': 'Dairy'},
        
        # Different product
        {'brand_name': 'Amul', 'product_name': 'Cheese Slices', 'quantity': '200g', 'category': 'Dairy'},
        
        # Brand alias test
        {'brand_name': 'Himalaya Herbals', 'product_name': 'Face Wash', 'quantity': '100ml', 'category': 'Beauty'},
        {'brand_name': 'Himalaya', 'product_name': 'Face Wash', 'quantity': '100ml', 'category': 'Beauty'},
        
        # Tata Tea variants
        {'brand_name': 'Tata Tea', 'product_name': 'Gold Premium 500g', 'quantity': '500g', 'category': 'Beverages'},
        {'brand_name': 'Tata Tea', 'product_name': 'Gold 500g Pack', 'quantity': '500g', 'category': 'Beverages'},
        {'brand_name': 'Tata', 'product_name': 'Tea Gold', 'quantity': '500g', 'category': 'Beverages'},
    ]
    
    print("Processing test products...")
    print()
    
    for i, product in enumerate(test_products, 1):
        print(f"Product {i}:")
        print(f"  Input: {product['brand_name']} - {product['product_name']} ({product['quantity']})")
        
        result = matcher.find_or_create_normalized_product(
            brand_name=product['brand_name'],
            product_name=product['product_name'],
            quantity=product['quantity'],
            category=product['category']
        )
        
        if result:
            status = "🆕 NEW" if result['is_new'] else "✅ MATCHED"
            print(f"  {status}")
            print(f"  Product ID: {result['product_id']}")
            print(f"  Fingerprint: {result['fingerprint']}")
            print(f"  Normalized: {result['brand_name']} - {result['product_name']}")
        
        print()
    
    # Print statistics
    matcher.print_statistics()
    
    # Show duplicate variants
    print()
    print("="*70)
    print("PRODUCTS WITH MULTIPLE QUANTITY VARIANTS")
    print("="*70)
    print()
    
    duplicates = matcher.find_duplicates_by_brand_product(limit=5)
    for dup in duplicates:
        print(f"Brand + Product: {dup['brand_product']}")
        print(f"  Variants: {dup['count']}")
        for variant in dup['variants']:
            print(f"    - ID {variant['product_id']}: {variant['quantity']} (fingerprint: {variant['fingerprint']})")
        print()
    
    print("="*70)
    print("✅ Matcher module demo complete!")
    print("="*70)