"""
Fuzzy Matching Module - Stage 2: Fuzzy String Matching

File Location: product-normalization-hackathon/src/fuzzy_matcher.py

This module extends the fingerprint matcher with fuzzy string matching
to catch products that are similar but not identical.
"""

import sys
import os
from typing import Optional, Dict, List, Tuple
from fuzzywuzzy import fuzz


# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.matcher import ProductMatcher
from src.normalizer import TextNormalizer
from src.config import (
    FUZZY_MATCH_THRESHOLD,
    MAX_CANDIDATES_FUZZY
)


class FuzzyProductMatcher(ProductMatcher):
    """
    Stage 1 + Stage 2: Fingerprint + Fuzzy Matching
    
    This matcher first tries exact fingerprint matching (Stage 1),
    then falls back to fuzzy string matching (Stage 2) if no exact match found.
    """
    
    def __init__(self, enable_fuzzy: bool = True):
        """
        Initialize fuzzy matcher
        
        Args:
            enable_fuzzy: Whether to enable fuzzy matching (True) or only fingerprint (False)
        """
        super().__init__()
        self.enable_fuzzy = enable_fuzzy
        
        # Additional indexes for fuzzy matching
        self.brand_index = {}  # Key: normalized_brand, Value: list of product_ids
        
        # Fuzzy matching statistics
        self.stats['fuzzy_matches'] = 0
        self.stats['fuzzy_candidates_checked'] = 0
        self.stats['fuzzy_no_candidates'] = 0
    
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
        Override parent method to also index by brand
        """
        normalized_product = super()._create_normalized_product(
            brand_norm=brand_norm,
            product_norm=product_norm,
            quantity=quantity,
            category=category,
            fingerprint=fingerprint,
            original_brand=original_brand,
            original_product=original_product
        )
        
        # Index by brand for fuzzy matching
        self._index_by_brand(normalized_product)
        
        return normalized_product
    
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
        
        return candidates
    
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
            # This handles word order differences well
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
        self.stats['total_products_processed'] += 1
        
        try:
            # Normalize components
            brand_norm = self.normalizer.normalize_brand(brand_name)
            product_norm = self.normalizer.normalize_product_name(product_name)
            
            # STAGE 1: Try fingerprint matching first
            fingerprint = self.normalizer.create_fingerprint(
                brand_name,
                product_name,
                quantity
            )
            
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
                    self.stats['fuzzy_no_candidates'] += 0
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
                        if self._quantities_compatible(quantity, best_match.get('quantity')):
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
            
            # Store in fingerprint index
            self.fingerprint_index[fingerprint] = normalized_product
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
    
    def _quantities_compatible(self, qty1: Optional[str], qty2: Optional[str]) -> bool:
        """
        Check if two quantities are compatible for fuzzy matching
        
        For fuzzy matching, we're more lenient:
        - If both have no quantity info, they're compatible
        - If one has quantity and other doesn't, they're compatible
        - If both have quantities, they must match
        
        Args:
            qty1: First quantity string
            qty2: Second quantity string
            
        Returns:
            True if compatible, False otherwise
        """
        # If either is None/empty, consider compatible
        if not qty1 or not qty2:
            return True
        
        # If both have quantities, they should match
        return self.normalizer.quantities_match(qty1, qty2)
    
    def get_statistics(self) -> Dict:
        """
        Get matching statistics including fuzzy matching stats
        
        Returns:
            Dictionary with statistics
        """
        stats = super().get_statistics()
        
        # Add fuzzy stats
        stats['fuzzy_matches'] = self.stats['fuzzy_matches']
        stats['fuzzy_candidates_checked'] = self.stats['fuzzy_candidates_checked']
        stats['fuzzy_no_candidates'] = self.stats['fuzzy_no_candidates']
        
        # Calculate combined match rate
        total_matches = self.stats['fingerprint_matches'] + self.stats['fuzzy_matches']
        total_processed = self.stats['total_products_processed']
        
        if total_processed > 0:
            stats['total_match_rate_percent'] = round((total_matches / total_processed) * 100, 2)
        else:
            stats['total_match_rate_percent'] = 0
        
        return stats
    
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

