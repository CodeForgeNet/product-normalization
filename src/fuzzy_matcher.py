"""
Fuzzy Matching Module - Stage 2: Fuzzy String Matching

File Location: product-normalization-hackathon/src/fuzzy_matcher.py

This module provides fuzzy string matching functionality
to catch products that are similar but not identical.
"""

import sys
import os
from typing import Optional, Dict, List, Tuple
from fuzzywuzzy import fuzz

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_config import FUZZY_MATCH_THRESHOLD, MAX_CANDIDATES_FUZZY


def fuzzy_match_product(
    brand_normalized: str,
    product_normalized: str,
    quantity_normalized: str,
    db_manager
) -> Optional[Dict]:
    """
    Fuzzy match product against existing normalized products
    
    Stage 2 of the matching pipeline. This function searches for similar products
    when exact fingerprint matching fails.
    
    Args:
        brand_normalized: Normalized brand name
        product_normalized: Normalized product name
        quantity_normalized: Normalized quantity
        db_manager: DatabaseManager instance
        
    Returns:
        Matched normalized product dict or None if no match found
        
    Example:
        Input: brand="tata", product="tea gold", quantity="500_gram"
        Matches: "tea gold premium" with 88% similarity
    """
    
    # Get candidates with same brand
    candidate_list = db_manager.find_normalized_products_by_brand(brand_normalized)
    
    if not candidate_list:
        return None
    
    best_match = None
    best_score = 0
    
    for candidate in candidate_list:
        # Calculate fuzzy similarity using token_sort_ratio
        # This handles word order differences well
        score = fuzz.token_sort_ratio(product_normalized, candidate['product_name'])
        
        if score >= FUZZY_MATCH_THRESHOLD and score > best_score:
            # Check if quantities match (if both present)
            if quantity_normalized and candidate.get('quantity'):
                if _quantities_compatible(quantity_normalized, candidate['quantity']):
                    best_score = score
                    best_match = candidate
            else:
                # If no quantity comparison needed
                best_score = score
                best_match = candidate
    
    return best_match


def _quantities_compatible(qty1: str, qty2: str) -> bool:
    """
    Check if two normalized quantities are compatible
    
    For fuzzy matching, we're more lenient:
    - Empty strings are compatible with anything
    - Otherwise must be exact match
    
    Args:
        qty1: First normalized quantity
        qty2: Second normalized quantity
        
    Returns:
        True if compatible, False otherwise
    """
    if not qty1 or not qty2:
        return True
    
    return qty1 == qty2


def calculate_similarity(text1: str, text2: str) -> int:
    """
    Calculate similarity score between two strings
    
    Args:
        text1: First string
        text2: Second string
        
    Returns:
        Similarity score (0-100)
    """
    return fuzz.token_sort_ratio(text1, text2)


# ============================================================================
# CLASS-BASED FUZZY MATCHER (For standalone use)
# ============================================================================

class FuzzyProductMatcher:
    """
    Standalone fuzzy matcher with in-memory storage
    
    This class can be used independently for testing or when database
    integration is not needed.
    """
    
    def __init__(self, enable_fuzzy: bool = True):
        """
        Initialize fuzzy matcher
        
        Args:
            enable_fuzzy: Whether to enable fuzzy matching (True) or only fingerprint (False)
        """
        self.enable_fuzzy = enable_fuzzy
        
        # In-memory storage
        self.fingerprint_index = {}  # Key: fingerprint, Value: normalized_product dict
        self.brand_index = {}  # Key: normalized_brand, Value: list of product_ids
        
        # Counter for IDs
        self.next_normalized_id = 1
        
        # Statistics
        self.stats = {
            'total_products_processed': 0,
            'fingerprint_matches': 0,
            'fuzzy_matches': 0,
            'new_normalized_products': 0,
            'failed_normalizations': 0,
            'fuzzy_candidates_checked': 0,
            'fuzzy_no_candidates': 0
        }
    
    def _index_by_brand(self, normalized_product: Dict):
        """
        Add normalized product to brand index for fuzzy matching
        
        Args:
            normalized_product: Normalized product dictionary
        """
        brand = normalized_product['brand_name']
        product_id = normalized_product['product_id']
        
        if brand not in self.brand_index:
            self.brand_index[brand] = []
        
        self.brand_index[brand].append(product_id)
    
    def _get_candidates_by_brand(self, brand_norm: str) -> List[Dict]:
        """
        Get candidate normalized products with the same brand
        
        Args:
            brand_norm: Normalized brand name
            
        Returns:
            List of candidate normalized products
        """
        if brand_norm not in self.brand_index:
            return []
        
        product_ids = self.brand_index[brand_norm]
        candidates = []
        
        for product_id in product_ids:
            normalized_product = self.get_normalized_product_by_id(product_id)
            if normalized_product:
                candidates.append(normalized_product)
        
        # Limit candidates for performance
        return candidates[:MAX_CANDIDATES_FUZZY]
    
    def _fuzzy_match_product_name(
        self,
        product_name: str,
        candidates: List[Dict],
        threshold: int = FUZZY_MATCH_THRESHOLD
    ) -> Optional[Tuple[Dict, int]]:
        """
        Find best fuzzy match among candidates
        
        Args:
            product_name: Normalized product name to match
            candidates: List of candidate normalized products
            threshold: Minimum similarity score (0-100)
            
        Returns:
            Tuple of (best_match, score) or None if no match above threshold
        """
        if not candidates:
            return None
        
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            candidate_name = candidate['product_name']
            
            # Use token_sort_ratio for best results
            score = fuzz.token_sort_ratio(product_name, candidate_name)
            
            self.stats['fuzzy_candidates_checked'] += 1
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        # Return match only if above threshold
        if best_score >= threshold:
            return (best_match, best_score)
        
        return None
    
    def find_or_create_normalized_product(
        self,
        brand_name: str,
        product_name: str,
        quantity: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict:
        """
        Find existing normalized product using fingerprint + fuzzy matching,
        or create new one
        
        Args:
            brand_name: Raw brand name
            product_name: Raw product name
            quantity: Optional quantity string
            category: Optional category
            
        Returns:
            Dictionary with normalized product info including 'product_id'
        """
        from normalizer import normalize_brand, normalize_product_name, create_fingerprint
        
        self.stats['total_products_processed'] += 1
        
        try:
            # Normalize components
            brand_norm = normalize_brand(brand_name)
            product_norm = normalize_product_name(product_name)
            
            # STAGE 1: Try fingerprint matching first
            fingerprint = create_fingerprint(brand_norm, product_norm, quantity or '')
            
            if fingerprint in self.fingerprint_index:
                # Exact match found!
                self.stats['fingerprint_matches'] += 1
                normalized_product = self.fingerprint_index[fingerprint].copy()
                normalized_product['is_new'] = False
                normalized_product['match_type'] = 'fingerprint'
                normalized_product['match_score'] = 100
                return normalized_product
            
            # STAGE 2: Try fuzzy matching (if enabled)
            if self.enable_fuzzy:
                # Get candidates with same brand
                candidates = self._get_candidates_by_brand(brand_norm)
                
                if not candidates:
                    self.stats['fuzzy_no_candidates'] += 1
                else:
                    # Try fuzzy matching on product name
                    fuzzy_result = self._fuzzy_match_product_name(
                        product_norm,
                        candidates,
                        threshold=FUZZY_MATCH_THRESHOLD
                    )
                    
                    if fuzzy_result:
                        best_match, score = fuzzy_result
                        
                        # Check if quantities are compatible
                        if _quantities_compatible(quantity or '', best_match.get('quantity', '')):
                            # Fuzzy match found!
                            self.stats['fuzzy_matches'] += 1
                            normalized_product = best_match.copy()
                            normalized_product['is_new'] = False
                            normalized_product['match_type'] = 'fuzzy'
                            normalized_product['match_score'] = score
                            return normalized_product
            
            # No match found - create new normalized product
            normalized_product = self._create_normalized_product(
                brand_norm=brand_norm,
                product_norm=product_norm,
                quantity=quantity,
                category=category,
                fingerprint=fingerprint,
                original_brand=brand_name,
                original_product=product_name
            )
            
            # Store in indexes
            self.fingerprint_index[fingerprint] = normalized_product
            self._index_by_brand(normalized_product)
            self.stats['new_normalized_products'] += 1
            
            normalized_product['is_new'] = True
            normalized_product['match_type'] = 'new'
            normalized_product['match_score'] = 0
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
        from datetime import datetime
        
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
    
    def get_normalized_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get normalized product by product_id"""
        for normalized_product in self.fingerprint_index.values():
            if normalized_product['product_id'] == product_id:
                return normalized_product
        return None
    
    def get_statistics(self) -> Dict:
        """Get matching statistics including fuzzy matching stats"""
        total_processed = self.stats['total_products_processed']
        total_matches = self.stats['fingerprint_matches'] + self.stats['fuzzy_matches']
        
        match_rate = 0
        total_match_rate = 0
        
        if total_processed > 0:
            match_rate = (self.stats['fingerprint_matches'] / total_processed) * 100
            total_match_rate = (total_matches / total_processed) * 100
        
        return {
            'total_products_processed': total_processed,
            'fingerprint_matches': self.stats['fingerprint_matches'],
            'fuzzy_matches': self.stats['fuzzy_matches'],
            'new_normalized_products': self.stats['new_normalized_products'],
            'failed_normalizations': self.stats['failed_normalizations'],
            'fuzzy_candidates_checked': self.stats['fuzzy_candidates_checked'],
            'match_rate_percent': round(match_rate, 2),
            'total_match_rate_percent': round(total_match_rate, 2),
            'unique_fingerprints': len(self.fingerprint_index)
        }
    
    def print_statistics(self):
        """Print detailed matching statistics including fuzzy matching"""
        stats = self.get_statistics()
        
        print("="*70)
        print("MATCHING STATISTICS (FINGERPRINT + FUZZY)")
        print("="*70)
        print()
        print(f"Total Products Processed:     {stats['total_products_processed']:>10,}")
        print()
        print("Stage 1 (Fingerprint):")
        print(f"  Exact Matches:              {stats['fingerprint_matches']:>10,}")
        print()
        print("Stage 2 (Fuzzy Matching):")
        print(f"  Fuzzy Matches:              {stats['fuzzy_matches']:>10,}")
        print(f"  Candidates Checked:         {stats['fuzzy_candidates_checked']:>10,}")
        print()
        print("Results:")
        print(f"  Total Matches:              {stats['fingerprint_matches'] + stats['fuzzy_matches']:>10,}")
        print(f"  New Normalized Products:    {stats['new_normalized_products']:>10,}")
        print(f"  Failed Normalizations:      {stats['failed_normalizations']:>10,}")
        print()
        print(f"Match Rates:")
        print(f"  Fingerprint Only:           {stats['match_rate_percent']:>10.2f}%")
        print(f"  Total (Fingerprint+Fuzzy):  {stats['total_match_rate_percent']:>10.2f}%")
        print()
        print(f"Unique Fingerprints:          {stats['unique_fingerprints']:>10,}")
        print()
        print("="*70)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_fuzzy_matcher(enable_fuzzy: bool = True) -> FuzzyProductMatcher:
    """Create and return a new FuzzyProductMatcher instance"""
    return FuzzyProductMatcher(enable_fuzzy=enable_fuzzy)