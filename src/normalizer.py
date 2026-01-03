import re
import unicodedata
from typing import Optional, Dict, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app_config import (
    BRAND_ALIASES,
    ALL_STOP_WORDS,
    QUANTITY_UNITS,
    UNIT_MULTIPLIERS,
    COMPILED_QUANTITY_PATTERNS
)


class TextNormalizer:
    def __init__(self):
        self.brand_aliases = {k.lower(): v.lower() for k, v in BRAND_ALIASES.items()}
        self.stop_words = {word.lower() for word in ALL_STOP_WORDS}
        self.quantity_units = {k.lower(): v.lower() for k, v in QUANTITY_UNITS.items()}
        self.unit_multipliers = {k.lower(): v for k, v in UNIT_MULTIPLIERS.items()}
    
    def clean_text(self, text: str) -> str:
        if not text or not isinstance(text, str):
            return ""
        
        text = text.lower().strip()
        
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('utf-8')
        
        text = re.sub(r'[™®©]', '', text)
        
        text = re.sub(r'[_\-/\\|]', ' ', text)
        
        text = re.sub(r'[^\w\s\.]', ' ', text)
        
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def remove_stop_words(self, text: str) -> str:
        words = text.split()
        filtered_words = [word for word in words if word not in self.stop_words]
        return ' '.join(filtered_words)
    
    def normalize_brand(self, brand_name: str) -> str:
        if not brand_name or not isinstance(brand_name, str):
            return ""
        
        brand_clean = self.clean_text(brand_name)
        
        if brand_clean in self.brand_aliases:
            return self.brand_aliases[brand_clean]
        
        for alias, normalized in self.brand_aliases.items():
            if brand_clean.startswith(alias + ' ') or brand_clean == alias:
                return normalized
        
        brand_clean = self.remove_stop_words(brand_clean)
        
        brand_clean = ' '.join(brand_clean.split())
        
        return brand_clean

    
    def normalize_product_name(self, product_name: str, remove_quantity: bool = True) -> str:
        if not product_name or not isinstance(product_name, str):
            return ""
        
        product_clean = self.clean_text(product_name)
        
        if remove_quantity:
            product_clean = self._remove_quantities(product_clean)
        
        product_clean = self.remove_stop_words(product_clean)
        
        words = product_clean.split()
        filtered_words = []
        
        for i, word in enumerate(words):
            if word.isdigit() and len(word) > 2:
                continue
            elif re.match(r'^\d+[a-z]+', word) or re.match(r'^[a-z]+\d+', word):
                filtered_words.append(word)
            elif not word.replace('.', '').isdigit():
                filtered_words.append(word)
        
        product_clean = ' '.join(filtered_words)
        
        product_clean = ' '.join(product_clean.split())
        
        return product_clean.strip()
    
    def _remove_quantities(self, text: str) -> str:
        for pattern in COMPILED_QUANTITY_PATTERNS:
            text = pattern.sub('', text)
        
        text = re.sub(r'\b(kg|kgs|g|gm|gms|gram|grams|l|ltr|litre|ml|pc|pcs|pack)\b', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\s*x\s*\d+', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def normalize_quantity(self, quantity: str) -> Optional[Dict[str, any]]:
        if not quantity or not isinstance(quantity, str):
            return None
        
        quantity_clean = quantity.lower().strip()
        
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
        
        standard_match = re.search(
            r'(\d+\.?\d*)\s*(kg|kgs|g|gm|gms|gram|grams|l|ltr|litre|litres|liter|liters|ml|pc|pcs|piece|pieces|pack|u)',
            quantity_clean,
            re.IGNORECASE
        )
        
        if standard_match:
            value_str = standard_match.group(1)
            unit = standard_match.group(2).lower()
            
            value = float(value_str)
            
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
        
        return None
    
    def quantities_match(self, qty1: str, qty2: str, tolerance: float = 0.05) -> bool:
        q1 = self.normalize_quantity(qty1)
        q2 = self.normalize_quantity(qty2)
        
        if not q1 or not q2:
            return False
        
        if q1['unit'] != q2['unit']:
            return False
        
        if q1['value'] == q2['value'] and q1['pack_count'] == q2['pack_count']:
            return True
        
        diff = abs(q1['value'] - q2['value'])
        avg = (q1['value'] + q2['value']) / 2
        
        if avg > 0 and (diff / avg) <= tolerance:
            return q1['pack_count'] == q2['pack_count']
        
        return False
    
    def create_fingerprint(self, brand: str, product_name: str, quantity: Optional[str] = None) -> str:
        brand_norm = self.normalize_brand(brand)
        product_norm = self.normalize_product_name(product_name, remove_quantity=True)
        
        parts = []
        
        if brand_norm:
            parts.extend(brand_norm.split())
        
        if product_norm:
            parts.extend(product_norm.split())
        
        if quantity:
            qty_norm = self.normalize_quantity(quantity)
            if qty_norm:
                parts.append(f"{int(qty_norm['value'])}")
                parts.append(qty_norm['unit'])
        
        parts.sort()
        
        fingerprint = '_'.join(parts)
        
        return fingerprint
    
    def extract_quantity_from_name(self, product_name: str) -> Optional[str]:
        for pattern in COMPILED_QUANTITY_PATTERNS:
            match = pattern.search(product_name.lower())
            if match:
                return match.group(0)
        
        return None
    
    def get_base_quantity(self, quantity: str) -> Tuple[float, str]:
        qty_norm = self.normalize_quantity(quantity)
        if qty_norm:
            return (qty_norm['value'], qty_norm['unit'])
        return (0.0, "")

_normalizer = TextNormalizer()

def normalize_brand(brand: str) -> str:
    return _normalizer.normalize_brand(brand)

def normalize_product_name(product_name: str) -> str:
    return _normalizer.normalize_product_name(product_name)

def normalize_quantity(quantity: str) -> Optional[Dict]:
    return _normalizer.normalize_quantity(quantity)

def create_fingerprint(brand: str, product_name: str, quantity: Optional[str] = None) -> str:
    return _normalizer.create_fingerprint(brand, product_name, quantity)

def quantities_match(qty1: str, qty2: str) -> bool:
    return _normalizer.quantities_match(qty1, qty2)

