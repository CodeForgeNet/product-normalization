"""
Product Matching Module - Multi-Stage Matching Engine

File Location: product-normalization-hackathon/src/matcher.py
"""

import sys
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from normalizer import normalize_brand, normalize_product_name, normalize_quantity, create_fingerprint

# Don't import fuzzy_matcher here to avoid circular import
# from src.fuzzy_matcher import fuzzy_match_product  # REMOVED


def find_or_create_normalized_product(row, db_manager) -> Tuple[int, str]:
    """
    Find existing normalized product or create new one using multi-stage matching
    
    This is the main entry point for the matching pipeline used by main.py
    
    Args:
        row: Pandas DataFrame row with product data
        db_manager: DatabaseManager instance
        
    Returns:
        Tuple of (product_id, match_stage)
        - product_id: int - ID of normalized product
        - match_stage: str - 'fingerprint', 'fuzzy', or 'new'
    """
    
    # Extract data from row
    brand_name = row.get('brand_name', '')
    product_name = row.get('product_name', '')
    quantity = row.get('quantity', '')
    category = row.get('category', '')
    
    # Get normalized values
    brand_norm = row.get('brand_normalized', normalize_brand(brand_name))
    product_norm = row.get('product_normalized', normalize_product_name(product_name))
    quantity_norm = row.get('quantity_normalized', normalize_quantity(quantity))
    # Sanitize quantity_norm (convert dict to string if needed)
    if isinstance(quantity_norm, dict):
        val = quantity_norm.get('value', 0)
        unit = quantity_norm.get('unit', '')
        # Format integer values without decimal point
        if val == int(val):
            val = int(val)
        quantity_norm = f"{val} {unit}"
    
    # Sanitize category (handle NaN/float)
    if category is not None and not isinstance(category, str):
        category = None
        
    fingerprint = row.get('fingerprint', create_fingerprint(brand_norm, product_norm, quantity_norm))
    
    # Stage 1: Try fingerprint matching
    existing_product = db_manager.find_normalized_product_by_fingerprint(fingerprint)
    if existing_product:
        return existing_product['id'], 'fingerprint'
    
    # Stage 2: Try fuzzy matching (import here to avoid circular dependency)
    try:
        from fuzzy_matcher import fuzzy_match_product
        
        fuzzy_match = fuzzy_match_product(
            brand_normalized=brand_norm,
            product_normalized=product_norm,
            quantity_normalized=quantity_norm,
            db_manager=db_manager
        )
        
        if fuzzy_match:
            return fuzzy_match['id'], 'fuzzy'
    except ImportError:
        # If fuzzy matcher not available, skip this stage
        pass
    

    # Stage 3: Create new normalized product
    new_product_id = db_manager.insert_normalized_product(
        fingerprint=fingerprint,
        brand_name=brand_norm,
        product_name=product_norm,
        quantity=quantity_norm,
        category=category
    )
    
    return new_product_id, 'new'


class ProductMatcher:
    """
    Stage 1: Fingerprint-based exact matching
    
    This matcher uses normalized fingerprints to identify exact product matches.
    It's the first and fastest stage of the matching pipeline.
    """
    
    def __init__(self):
        """Initialize the matcher with normalizer and storage"""
        
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
    
    def find_or_create_normalized_product_standalone(
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
        """
        self.stats['total_products_processed'] += 1
        
        try:
            # Normalize components
            brand_norm = normalize_brand(brand_name)
            product_norm = normalize_product_name(product_name)
            quantity_norm = normalize_quantity(quantity) if quantity else ''
            
            # Create fingerprint
            fingerprint = create_fingerprint(
                brand_norm,
                product_norm,
                quantity_norm
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
        """Create a new normalized product entry"""
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
        """Process a batch of products and assign product_ids"""
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
                normalized = self.find_or_create_normalized_product_standalone(
                    brand_name=product.get('brand_name', ''),
                    product_name=product.get('product_name', ''),
                    quantity=product.get('quantity'),
                    category=product.get('category')
                )
                
                if normalized:
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
        """Get matching statistics"""
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
        """Get list of all normalized products"""
        return list(self.fingerprint_index.values())
    
    def get_normalized_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get normalized product by product_id"""
        for normalized_product in self.fingerprint_index.values():
            if normalized_product['product_id'] == product_id:
                return normalized_product
        return None
    
    def get_products_by_fingerprint(self, fingerprint: str) -> Optional[Dict]:
        """Get normalized product by fingerprint"""
        return self.fingerprint_index.get(fingerprint)
    
    def export_normalized_products_to_dict(self) -> List[Dict]:
        """Export normalized products for saving to CSV"""
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


def create_matcher() -> ProductMatcher:
    """Create and return a new ProductMatcher instance"""
    return ProductMatcher()