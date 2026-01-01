"""
Normalization Module - Core text normalization functions

File Location: product-normalization-hackathon/src/normalizer.py

This module contains all normalization logic for brands, product names,
and quantities to enable accurate product matching.
"""

import re
import unicodedata
from typing import Optional, Dict, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    BRAND_ALIASES,
    ALL_STOP_WORDS,
    QUANTITY_UNITS,
    UNIT_MULTIPLIERS,
    COMPILED_QUANTITY_PATTERNS
)


class TextNormalizer:
    """
    Handles all text normalization operations for product matching
    """
    
    def __init__(self):
        """Initialize the normalizer with configuration"""
        self.brand_aliases = {k.lower(): v.lower() for k, v in BRAND_ALIASES.items()}
        self.stop_words = {word.lower() for word in ALL_STOP_WORDS}
        self.quantity_units = {k.lower(): v.lower() for k, v in QUANTITY_UNITS.items()}
        self.unit_multipliers = {k.lower(): v for k, v in UNIT_MULTIPLIERS.items()}
    
    # ========================================================================
    # BASIC TEXT CLEANING
    # ========================================================================
    
    def clean_text(self, text: str) -> str:
        """
        Basic text cleaning: lowercase, remove special chars, normalize spaces
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text string
            
        Example:
            "Tata-Tea™ Gold" → "tata tea gold"
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove accents and special unicode characters
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('utf-8')
        
        # Remove trademark symbols, registered marks, etc.
        text = re.sub(r'[™®©]', '', text)
        
        # Replace special punctuation with spaces
        text = re.sub(r'[_\-/\\|]', ' ', text)
        
        # Remove other punctuation except dots (for decimals in quantities)
        text = re.sub(r'[^\w\s\.]', ' ', text)
        
        # Normalize multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def remove_stop_words(self, text: str) -> str:
        """
        Remove stop words from text
        
        Args:
            text: Cleaned text string
            
        Returns:
            Text with stop words removed
            
        Example:
            "tata tea gold premium pack" → "tata tea gold"
        """
        words = text.split()
        filtered_words = [word for word in words if word not in self.stop_words]
        return ' '.join(filtered_words)
    
    # ========================================================================
    # BRAND NORMALIZATION
    # ========================================================================
    
    def normalize_brand(self, brand_name: str) -> str:
        """
        Normalize brand name using alias mapping and cleaning
        
        Args:
            brand_name: Raw brand name
            
        Returns:
            Normalized brand name
            
        Examples:
            "Himalaya Herbals" → "himalaya"
            "Mother Dairy" → "motherdairy"
            "Britannia Marie Gold" → "britannia"
        """
        if not brand_name or not isinstance(brand_name, str):
            return ""
        
        # Clean the text
        brand_clean = self.clean_text(brand_name)
        
        # Check if this brand has an alias mapping
        if brand_clean in self.brand_aliases:
            return self.brand_aliases[brand_clean]
        
        # Check for partial matches (e.g., "britannia good day" → "britannia")
        for alias, normalized in self.brand_aliases.items():
            if brand_clean.startswith(alias + ' ') or brand_clean == alias:
                return normalized
        
        # Remove common stop words from brand names
        brand_clean = self.remove_stop_words(brand_clean)
        
        # Remove extra spaces
        brand_clean = ' '.join(brand_clean.split())
        
        return brand_clean
    
    # ========================================================================
    # PRODUCT NAME NORMALIZATION
    # ========================================================================
    
    def normalize_product_name(self, product_name: str, remove_quantity: bool = True) -> str:
        """
        Normalize product name by removing stop words, quantities, and extra info
        
        Args:
            product_name: Raw product name
            remove_quantity: Whether to remove quantity info from product name
            
        Returns:
            Normalized product name
            
        Examples:
            "Tata Tea Gold Premium Pack 500g" → "tata tea gold"
            "Amul Butter Pack 100g" → "amul butter"
            "Maggi 2-Minute Noodles Masala" → "maggi minute noodles masala"
        """
        if not product_name or not isinstance(product_name, str):
            return ""
        
        # Clean the text
        product_clean = self.clean_text(product_name)
        
        # Remove quantity information if requested
        if remove_quantity:
            product_clean = self._remove_quantities(product_clean)
        
        # Remove stop words
        product_clean = self.remove_stop_words(product_clean)
        
        # Remove numbers that aren't part of product identity
        # Keep numbers if they're part of product name (e.g., "7up", "5050")
        words = product_clean.split()
        filtered_words = []
        
        for i, word in enumerate(words):
            # Keep if it's a known product with numbers (like "7up", "5050")
            if word.isdigit() and len(word) > 2:
                # Skip standalone large numbers (likely quantities)
                continue
            # Keep numbers that are part of product identity
            elif re.match(r'^\d+[a-z]+', word) or re.match(r'^[a-z]+\d+', word):
                filtered_words.append(word)
            # Keep non-numeric words
            elif not word.replace('.', '').isdigit():
                filtered_words.append(word)
        
        product_clean = ' '.join(filtered_words)
        
        # Remove extra spaces
        product_clean = ' '.join(product_clean.split())
        
        return product_clean.strip()
    
    def _remove_quantities(self, text: str) -> str:
        """
        Remove quantity patterns from text
        
        Args:
            text: Text potentially containing quantities
            
        Returns:
            Text with quantities removed
        """
        # Remove all quantity patterns
        for pattern in COMPILED_QUANTITY_PATTERNS:
            text = pattern.sub('', text)
        
        # Clean up any remaining measurement units standing alone
        text = re.sub(r'\b(kg|kgs|g|gm|gms|gram|grams|l|ltr|litre|ml|pc|pcs|pack)\b', '', text, flags=re.IGNORECASE)
        
        # Remove x patterns (like "x 2", "x2")
        text = re.sub(r'\s*x\s*\d+', '', text, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    # ========================================================================
    # QUANTITY NORMALIZATION
    # ========================================================================
    
    def normalize_quantity(self, quantity: str) -> Optional[Dict[str, any]]:
        """
        Normalize quantity to standard format with base units
        
        Args:
            quantity: Raw quantity string (e.g., "500g", "1.5kg", "250 ml x 2")
            
        Returns:
            Dictionary with normalized quantity info or None if invalid
            {
                'value': float,        # Numerical value in base units
                'unit': str,          # Base unit ('gram' or 'ml' or 'piece')
                'original': str,      # Original quantity string
                'is_multipack': bool, # Whether it's a multipack
                'pack_count': int     # Number of packs (1 if not multipack)
            }
            
        Examples:
            "500g" → {'value': 500.0, 'unit': 'gram', 'original': '500g', ...}
            "1.5kg" → {'value': 1500.0, 'unit': 'gram', 'original': '1.5kg', ...}
            "250 ml x 2" → {'value': 250.0, 'unit': 'ml', 'is_multipack': True, 'pack_count': 2}
        """
        if not quantity or not isinstance(quantity, str):
            return None
        
        quantity_clean = quantity.lower().strip()
        
        # Try to match multipack pattern first
        multipack_match = re.search(
            r'(\d+\.?\d*)\s*(kg|kgs|g|gm|gms|gram|grams|l|ltr|litre|litres|liter|liters|ml)\s*x\s*(\d+)',
            quantity_clean,
            re.IGNORECASE
        )
        
        if multipack_match:
            value_str = multipack_match.group(1)
            unit = multipack_match.group(2).lower()
            pack_count = int(multipack_match.group(3))
            
            value = float(value_str)
            
            # Convert to base unit
            if unit in self.unit_multipliers:
                value = value * self.unit_multipliers[unit]
            
            base_unit = self.quantity_units.get(unit, unit)
            
            return {
                'value': value,
                'unit': base_unit,
                'original': quantity,
                'is_multipack': True,
                'pack_count': pack_count,
                'total_value': value * pack_count
            }
        
        # Try standard quantity pattern
        standard_match = re.search(
            r'(\d+\.?\d*)\s*(kg|kgs|g|gm|gms|gram|grams|l|ltr|litre|litres|liter|liters|ml|pc|pcs|piece|pieces|pack|u)',
            quantity_clean,
            re.IGNORECASE
        )
        
        if standard_match:
            value_str = standard_match.group(1)
            unit = standard_match.group(2).lower()
            
            value = float(value_str)
            
            # Convert to base unit
            if unit in self.unit_multipliers:
                value = value * self.unit_multipliers[unit]
            
            base_unit = self.quantity_units.get(unit, unit)
            
            return {
                'value': value,
                'unit': base_unit,
                'original': quantity,
                'is_multipack': False,
                'pack_count': 1,
                'total_value': value
            }
        
        # If no pattern matches, return None
        return None
    
    def quantities_match(self, qty1: str, qty2: str, tolerance: float = 0.05) -> bool:
        """
        Check if two quantities represent the same amount
        
        Args:
            qty1: First quantity string
            qty2: Second quantity string
            tolerance: Acceptable difference percentage (default 5%)
            
        Returns:
            True if quantities match within tolerance
            
        Examples:
            "500g", "0.5kg" → True
            "250ml", "250 ml" → True
            "100g x 2", "200g" → False (different - multipack vs single)
        """
        q1 = self.normalize_quantity(qty1)
        q2 = self.normalize_quantity(qty2)
        
        if not q1 or not q2:
            return False
        
        # Must be same unit
        if q1['unit'] != q2['unit']:
            return False
        
        # Compare single pack values (not total for multipacks)
        # This ensures "100g x 2" != "100g" but "100g x 2" == "100g x 2"
        if q1['value'] == q2['value'] and q1['pack_count'] == q2['pack_count']:
            return True
        
        # Allow small tolerance for floating point errors
        diff = abs(q1['value'] - q2['value'])
        avg = (q1['value'] + q2['value']) / 2
        
        if avg > 0 and (diff / avg) <= tolerance:
            return q1['pack_count'] == q2['pack_count']
        
        return False
    
    # ========================================================================
    # FINGERPRINT GENERATION
    # ========================================================================
    
    def create_fingerprint(self, brand: str, product_name: str, quantity: Optional[str] = None) -> str:
        """
        Create a unique fingerprint for product matching
        
        The fingerprint combines normalized brand, product name, and optionally quantity
        into a single string that can be used for exact matching.
        
        Args:
            brand: Brand name
            product_name: Product name
            quantity: Optional quantity string
            
        Returns:
            Fingerprint string for matching
            
        Examples:
            ("Amul", "Butter Pack 100g", "100g") → "amul_butter_100_gram"
            ("Tata Tea", "Gold Premium 500g", "500g") → "tata_tea_gold_500_gram"
        """
        # Normalize components
        brand_norm = self.normalize_brand(brand)
        product_norm = self.normalize_product_name(product_name, remove_quantity=True)
        
        # Combine brand and product
        parts = []
        
        if brand_norm:
            parts.extend(brand_norm.split())
        
        if product_norm:
            parts.extend(product_norm.split())
        
        # Add normalized quantity if provided
        if quantity:
            qty_norm = self.normalize_quantity(quantity)
            if qty_norm:
                # Add quantity value and unit
                parts.append(f"{int(qty_norm['value'])}")
                parts.append(qty_norm['unit'])
        
        # Sort words alphabetically for consistency
        parts.sort()
        
        # Join with underscore
        fingerprint = '_'.join(parts)
        
        return fingerprint
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def extract_quantity_from_name(self, product_name: str) -> Optional[str]:
        """
        Extract quantity information from product name
        
        Args:
            product_name: Product name potentially containing quantity
            
        Returns:
            Extracted quantity string or None
            
        Example:
            "Amul Butter 100g Pack" → "100g"
        """
        for pattern in COMPILED_QUANTITY_PATTERNS:
            match = pattern.search(product_name.lower())
            if match:
                return match.group(0)
        
        return None
    
    def get_base_quantity(self, quantity: str) -> Tuple[float, str]:
        """
        Get quantity in base units (gram or ml)
        
        Args:
            quantity: Quantity string
            
        Returns:
            Tuple of (value, unit) in base units
            
        Example:
            "1.5kg" → (1500.0, "gram")
        """
        qty_norm = self.normalize_quantity(quantity)
        if qty_norm:
            return (qty_norm['value'], qty_norm['unit'])
        return (0.0, "")


# ============================================================================
# CONVENIENCE FUNCTIONS (for easy import)
# ============================================================================

# Global normalizer instance
_normalizer = TextNormalizer()

def normalize_brand(brand: str) -> str:
    """Convenience function to normalize brand"""
    return _normalizer.normalize_brand(brand)

def normalize_product_name(product_name: str) -> str:
    """Convenience function to normalize product name"""
    return _normalizer.normalize_product_name(product_name)

def normalize_quantity(quantity: str) -> Optional[Dict]:
    """Convenience function to normalize quantity"""
    return _normalizer.normalize_quantity(quantity)

def create_fingerprint(brand: str, product_name: str, quantity: Optional[str] = None) -> str:
    """Convenience function to create fingerprint"""
    return _normalizer.create_fingerprint(brand, product_name, quantity)

def quantities_match(qty1: str, qty2: str) -> bool:
    """Convenience function to check if quantities match"""
    return _normalizer.quantities_match(qty1, qty2)

