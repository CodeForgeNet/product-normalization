import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.normalizer import TextNormalizer


class TestTextNormalizer:
    def setup_method(self):
        self.normalizer = TextNormalizer()

    def test_brand_normalize_basic(self):
        assert self.normalizer.normalize_brand("Amul") == "amul"
        assert self.normalizer.normalize_brand("AMUL") == "amul"
        assert self.normalizer.normalize_brand("Tata") == "tata"
    
    def test_brand_normalize_aliases(self):
        assert self.normalizer.normalize_brand("Himalaya Herbals") == "himalaya"
        assert self.normalizer.normalize_brand("Mother Dairy") == "motherdairy"
        assert self.normalizer.normalize_brand("Coca Cola") == "cocacola"
        assert self.normalizer.normalize_brand("Coca-Cola") == "cocacola"
    
    def test_brand_normalize_variants(self):
        assert self.normalizer.normalize_brand("Britannia Marie Gold") == "britannia"
        assert self.normalizer.normalize_brand("Britannia Good Day") == "britannia"
        assert self.normalizer.normalize_brand("Nestle KitKat") == "nestle"
    
    def test_brand_normalize_special_chars(self):
        assert self.normalizer.normalize_brand("Tata-Tea") == "tata tea"
        assert self.normalizer.normalize_brand("L'Oreal") == "l oreal"
    
    def test_product_normalize_basic(self):
        result = self.normalizer.normalize_product_name("Butter")
        assert result == "butter"
    
    def test_product_normalize_with_stopwords(self):
        result = self.normalizer.normalize_product_name("Butter Pack Premium")
        assert "pack" not in result
        assert "premium" not in result
        assert "butter" in result
    
    def test_product_normalize_with_quantity(self):
        result = self.normalizer.normalize_product_name("Butter 100g Pack")
        assert "100" not in result
        assert "butter" in result
    
    def test_product_normalize_complex(self):
        result = self.normalizer.normalize_product_name(
            "Tata Tea Gold Premium Pack 500g"
        )
        assert "tata" in result or "tea" in result or "gold" in result
        assert "pack" not in result
        assert "premium" not in result
        assert "500" not in result
    
    
    def test_quantity_normalize_grams(self):
        result = self.normalizer.normalize_quantity("500g")
        assert result is not None
        assert result['value'] == 500.0
        assert result['unit'] == 'gram'
        assert result['is_multipack'] == False
    
    def test_quantity_normalize_kg_to_grams(self):
        result = self.normalizer.normalize_quantity("1.5kg")
        assert result is not None
        assert result['value'] == 1500.0
        assert result['unit'] == 'gram'
    
    def test_quantity_normalize_ml(self):
        result = self.normalizer.normalize_quantity("250ml")
        assert result is not None
        assert result['value'] == 250.0
        assert result['unit'] == 'ml'
    
    def test_quantity_normalize_liters_to_ml(self):
        result = self.normalizer.normalize_quantity("1.5l")
        assert result is not None
        assert result['value'] == 1500.0
        assert result['unit'] == 'ml'
    
    def test_quantity_normalize_multipack(self):
        result = self.normalizer.normalize_quantity("100g x 2")
        assert result is not None
        assert result['value'] == 100.0
        assert result['unit'] == 'gram'
        assert result['is_multipack'] == True
        assert result['pack_count'] == 2
        assert result['total_value'] == 200.0
    
    def test_quantity_normalize_with_spaces(self):
        result1 = self.normalizer.normalize_quantity("500 g")
        result2 = self.normalizer.normalize_quantity("500g")
        assert result1['value'] == result2['value']
        assert result1['unit'] == result2['unit']
    
    def test_quantities_match_same_unit(self):
        assert self.normalizer.quantities_match("500g", "500g") == True
        assert self.normalizer.quantities_match("250ml", "250ml") == True
    
    def test_quantities_match_different_format(self):
        assert self.normalizer.quantities_match("500g", "0.5kg") == True
        assert self.normalizer.quantities_match("1000ml", "1l") == True
        assert self.normalizer.quantities_match("1.5kg", "1500g") == True
    
    def test_quantities_not_match_different_values(self):
        assert self.normalizer.quantities_match("500g", "250g") == False
        assert self.normalizer.quantities_match("1l", "500ml") == False
    
    def test_quantities_multipack_matching(self):
        assert self.normalizer.quantities_match("100g x 2", "100g x 2") == True
        assert self.normalizer.quantities_match("100g x 2", "200g") == False
        assert self.normalizer.quantities_match("100g x 2", "100g") == False
    
    def test_fingerprint_basic(self):
        fp = self.normalizer.create_fingerprint("Amul", "Butter", "100g")
        assert isinstance(fp, str)
        assert len(fp) > 0
        assert "amul" in fp
        assert "butter" in fp
    
    def test_fingerprint_consistency(self):
        fp1 = self.normalizer.create_fingerprint("Tata", "Tea Gold", "500g")
        fp2 = self.normalizer.create_fingerprint("Tata", "Tea Gold", "500g")
        assert fp1 == fp2
    
    def test_fingerprint_similar_products(self):
        fp1 = self.normalizer.create_fingerprint("Tata Tea", "Gold Premium", "500g")
        fp2 = self.normalizer.create_fingerprint("Tata Tea", "Gold", "500g")
        assert isinstance(fp1, str) and isinstance(fp2, str)
    
    def test_fingerprint_without_quantity(self):
        fp = self.normalizer.create_fingerprint("Amul", "Butter", None)
        assert isinstance(fp, str)
        assert "amul" in fp
        assert "butter" in fp
    
    def test_empty_inputs(self):
        assert self.normalizer.normalize_brand("") == ""
        assert self.normalizer.normalize_brand(None) == ""
        assert self.normalizer.normalize_product_name("") == ""
        assert self.normalizer.normalize_quantity("") is None
    
    def test_special_characters(self):
        result = self.normalizer.normalize_brand("Coca-Cola™")
        assert "™" not in result
        assert "cocacola" in result or "coca" in result
    
    def test_unicode_handling(self):
        result = self.normalizer.clean_text("Café")
        assert "cafe" in result.lower()


def run_tests():
    import traceback
    
    test_class = TestTextNormalizer()
    test_class.setup_method()
    
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    print("="*70)
    print("RUNNING NORMALIZATION TESTS")
    print("="*70)
    print()
    
    for method_name in test_methods:
        method = getattr(test_class, method_name)
        try:
            method()
            print(f"✅ {method_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {method_name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {method_name} (Exception)")
            print(f"   Error: {e}")
            traceback.print_exc()
            failed += 1
    
    print()
    print("="*70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)