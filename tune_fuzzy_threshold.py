"""
Fuzzy Matching Threshold Tuning

File Location: product-normalization-hackathon/tune_fuzzy_threshold.py

This script helps find the optimal fuzzy matching threshold.
"""

import pandas as pd
import sys
import os
from fuzzywuzzy import fuzz

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.normalizer import TextNormalizer
from src.config import PRODUCTS_INPUT_FILE, TEST_CASES_FILE
import json


class ThresholdTuner:
    """Tune fuzzy matching threshold using test cases"""
    
    def __init__(self):
        """Initialize tuner"""
        self.normalizer = TextNormalizer()
        self.test_cases = []
    
    def load_test_cases(self, file_path: str = TEST_CASES_FILE) -> bool:
        """
        Load test cases from JSON file
        
        Args:
            file_path: Path to test cases JSON
            
        Returns:
            True if successful
        """
        if not os.path.exists(file_path):
            print(f"❌ Test cases file not found: {file_path}")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            self.test_cases = json.load(f)
        
        print(f"✅ Loaded {len(self.test_cases)} test cases")
        return True
    
    def calculate_similarity(self, product1: dict, product2: dict) -> int:
        """
        Calculate similarity score between two products
        
        Args:
            product1: First product dict
            product2: Second product dict
            
        Returns:
            Similarity score (0-100)
        """
        # Normalize both products
        brand1 = self.normalizer.normalize_brand(product1['brand'])
        brand2 = self.normalizer.normalize_brand(product2['brand'])
        
        product_name1 = self.normalizer.normalize_product_name(product1['product'])
        product_name2 = self.normalizer.normalize_product_name(product2['product'])
        
        # Brands must match
        if brand1 != brand2:
            return 0
        
        # Calculate product name similarity
        score = fuzz.token_sort_ratio(product_name1, product_name2)
        
        return score
    
    def evaluate_threshold(self, threshold: int) -> dict:
        """
        Evaluate matching quality at a given threshold
        
        Args:
            threshold: Fuzzy match threshold (0-100)
            
        Returns:
            Dictionary with metrics
        """
        true_positives = 0  # Should match and does match
        true_negatives = 0  # Should not match and doesn't match
        false_positives = 0  # Should not match but does match
        false_negatives = 0  # Should match but doesn't match
        
        for test_case in self.test_cases:
            should_match = test_case.get('should_match', True)
            products = test_case.get('products', [])
            
            if len(products) < 2:
                continue
            
            # Compare first two products
            score = self.calculate_similarity(products[0], products[1])
            does_match = score >= threshold
            
            if should_match and does_match:
                true_positives += 1
            elif not should_match and not does_match:
                true_negatives += 1
            elif not should_match and does_match:
                false_positives += 1
            elif should_match and not does_match:
                false_negatives += 1
        
        # Calculate metrics
        total = true_positives + true_negatives + false_positives + false_negatives
        
        accuracy = 0
        precision = 0
        recall = 0
        f1_score = 0
        
        if total > 0:
            accuracy = (true_positives + true_negatives) / total
        
        if (true_positives + false_positives) > 0:
            precision = true_positives / (true_positives + false_positives)
        
        if (true_positives + false_negatives) > 0:
            recall = true_positives / (true_positives + false_negatives)
        
        if (precision + recall) > 0:
            f1_score = 2 * (precision * recall) / (precision + recall)
        
        return {
            'threshold': threshold,
            'true_positives': true_positives,
            'true_negatives': true_negatives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score
        }
    
    def find_optimal_threshold(self, min_threshold: int = 70, max_threshold: int = 95) -> int:
        """
        Find optimal threshold by testing range
        
        Args:
            min_threshold: Minimum threshold to test
            max_threshold: Maximum threshold to test
            
        Returns:
            Optimal threshold value
        """
        print()
        print("="*70)
        print("THRESHOLD TUNING")
        print("="*70)
        print()
        
        results = []
        
        print("Testing thresholds from {} to {}...".format(min_threshold, max_threshold))
        print()
        
        for threshold in range(min_threshold, max_threshold + 1, 5):
            metrics = self.evaluate_threshold(threshold)
            results.append(metrics)
        
        # Print results table
        print("Threshold | Accuracy | Precision | Recall | F1-Score | TP | FP | FN | TN")
        print("-"*70)
        
        for metrics in results:
            print(f"   {metrics['threshold']:3d}    |  {metrics['accuracy']*100:5.1f}%  |   {metrics['precision']*100:5.1f}%   | {metrics['recall']*100:5.1f}% |  {metrics['f1_score']*100:5.1f}%  | {metrics['true_positives']:2d} | {metrics['false_positives']:2d} | {metrics['false_negatives']:2d} | {metrics['true_negatives']:2d}")
        
        print()
        
        # Find best threshold (highest F1-score)
        best = max(results, key=lambda x: x['f1_score'])
        
        print("="*70)
        print("OPTIMAL THRESHOLD")
        print("="*70)
        print()
        print(f"Best Threshold:  {best['threshold']}")
        print(f"F1-Score:        {best['f1_score']*100:.2f}%")
        print(f"Accuracy:        {best['accuracy']*100:.2f}%")
        print(f"Precision:       {best['precision']*100:.2f}%")
        print(f"Recall:          {best['recall']*100:.2f}%")
        print()
        
        return best['threshold']
    
    def test_specific_cases(self, threshold: int):
        """
        Test specific cases and show which ones pass/fail
        
        Args:
            threshold: Threshold to test
        """
        print()
        print("="*70)
        print(f"TESTING SPECIFIC CASES (Threshold: {threshold})")
        print("="*70)
        print()
        
        for i, test_case in enumerate(self.test_cases[:10], 1):  # Show first 10
            should_match = test_case.get('should_match', True)
            products = test_case.get('products', [])
            
            if len(products) < 2:
                continue
            
            score = self.calculate_similarity(products[0], products[1])
            does_match = score >= threshold
            
            # Determine status
            if should_match == does_match:
                status = "✅ CORRECT"
            else:
                status = "❌ WRONG"
            
            print(f"Test Case {i}: {status}")
            print(f"  Should Match: {should_match}")
            print(f"  Does Match:   {does_match} (score: {score}%)")
            print(f"  Product 1: {products[0]['brand']} - {products[0]['product']}")
            print(f"  Product 2: {products[1]['brand']} - {products[1]['product']}")
            print()


def main():
    """Main execution"""
    tuner = ThresholdTuner()
    
    # Load test cases
    if not tuner.load_test_cases():
        print("⚠️  No test cases available for tuning")
        print("   Using default threshold from config")
        return
    
    # Find optimal threshold
    optimal = tuner.find_optimal_threshold(min_threshold=75, max_threshold=95)
    
    # Test specific cases
    tuner.test_specific_cases(optimal)
    
    # Recommendation
    print("="*70)
    print("RECOMMENDATION")
    print("="*70)
    print()
    print(f"Update config.py with:")
    print(f"  FUZZY_MATCH_THRESHOLD = {optimal}")
    print()


if __name__ == "__main__":
    main()