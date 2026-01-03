import sys
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.normalizer import normalize_brand, normalize_product_name, normalize_quantity, create_fingerprint

def find_or_create_normalized_product(row, db_manager) -> Tuple[int, str]:

    brand_name = row.get('brand_name', '')
    product_name = row.get('product_name', '')
    quantity = row.get('quantity', '')
    category = row.get('category', '')
    
    brand_norm = row.get('brand_normalized', normalize_brand(brand_name))
    product_norm = row.get('product_normalized', normalize_product_name(product_name))
    quantity_norm = row.get('quantity_normalized', normalize_quantity(quantity))

    if isinstance(quantity_norm, dict):
        val = quantity_norm.get('value', 0)
        unit = quantity_norm.get('unit', '')
        if val == int(val):
            val = int(val)
        quantity_norm = f"{val} {unit}"
    
    if category is not None and not isinstance(category, str):
        category = None
        
    fingerprint = row.get('fingerprint', create_fingerprint(brand_norm, product_norm, quantity_norm))
    
    existing_product = db_manager.find_normalized_product_by_fingerprint(fingerprint)
    if existing_product:
        return existing_product['id'], 'fingerprint'
    
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
        pass
    
    new_product_id = db_manager.insert_normalized_product(
        fingerprint=fingerprint,
        brand_name=brand_norm,
        product_name=product_norm,
        quantity=quantity_norm,
        category=category
    )
    
    return new_product_id, 'new'


class ProductMatcher:
    
    def __init__(self):
        self.fingerprint_index = {}
        self.next_normalized_id = 1
        
        self.stats = {
            'total_products_processed': 0,
            'fingerprint_matches': 0,
            'new_normalized_products': 0,
            'failed_normalizations': 0
        }
    
    
    def find_or_create_normalized_product_standalone(
        self,
        brand_name: str,
        product_name: str,
        quantity: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict:
        self.stats['total_products_processed'] += 1
        
        try:
            brand_norm = normalize_brand(brand_name)
            product_norm = normalize_product_name(product_name)
            quantity_norm = normalize_quantity(quantity) if quantity else ''
            
            fingerprint = create_fingerprint(
                brand_norm,
                product_norm,
                quantity_norm
            )
            
            if fingerprint in self.fingerprint_index:
                self.stats['fingerprint_matches'] += 1
                normalized_product = self.fingerprint_index[fingerprint].copy()
                normalized_product['is_new'] = False
                normalized_product['match_type'] = 'fingerprint'
                return normalized_product
            
            normalized_product = self._create_normalized_product(
                brand_norm=brand_norm,
                product_norm=product_norm,
                quantity=quantity,
                category=category,
                fingerprint=fingerprint,
                original_brand=brand_name,
                original_product=product_name
            )
            
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
    
    def process_products_batch(
        self,
        products: List[Dict],
        batch_size: int = 1000
    ) -> List[Dict]:
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
    
    def get_statistics(self) -> Dict:
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
        return list(self.fingerprint_index.values())
    
    def get_normalized_product_by_id(self, product_id: int) -> Optional[Dict]:
        for normalized_product in self.fingerprint_index.values():
            if normalized_product['product_id'] == product_id:
                return normalized_product
        return None
    
    def get_products_by_fingerprint(self, fingerprint: str) -> Optional[Dict]:
        return self.fingerprint_index.get(fingerprint)
    
    def export_normalized_products_to_dict(self) -> List[Dict]:
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
    return ProductMatcher()