#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Sloka Search API
Tests the fast fuzzy search mechanism for verse validation.
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest


class TestSlokaSearch(unittest.TestCase):
    """Test cases for sloka search functionality."""

    def test_normalize_sanskrit_text(self):
        """Test Sanskrit text normalization."""
        from backend.api.text_matching import normalize_sanskrit_text

        # Test basic normalization
        text = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"
        normalized = normalize_sanskrit_text(text)

        self.assertIsNotNone(normalized)
        self.assertIsInstance(normalized, str)
        self.assertFalse('।' in normalized)  # Punctuation removed

    def test_normalize_vedic_accents(self):
        """Test that Vedic accent marks are removed."""
        from backend.api.text_matching import normalize_sanskrit_text

        # Text with Vedic accents (॑ and ॒)
        text = "अग्नि॑मीळे पुरो॒हितं"
        normalized = normalize_sanskrit_text(text)

        self.assertIsNotNone(normalized)
        # Should not contain accent marks
        self.assertFalse('\u0951' in normalized)
        self.assertFalse('\u0952' in normalized)

    def test_normalize_empty_text(self):
        """Test normalization of empty text."""
        from backend.api.text_matching import normalize_sanskrit_text

        self.assertEqual(normalize_sanskrit_text(""), "")
        self.assertEqual(normalize_sanskrit_text(None), "")

    def test_calculate_similarity(self):
        """Test similarity calculation."""
        from backend.api.text_matching import calculate_similarity

        # Exact match should be 1.0
        similarity = calculate_similarity("धर्म", "धर्म")
        self.assertEqual(similarity, 1.0)

        # Different strings should be less than 1.0
        similarity = calculate_similarity("धर्म", "कर्म")
        self.assertLess(similarity, 1.0)
        self.assertGreater(similarity, 0.0)

        # Completely different strings
        similarity = calculate_similarity("abc", "xyz")
        self.assertLess(similarity, 0.5)


class TestSlokaSearchAPI(unittest.TestCase):
    """Integration tests for the sloka search API endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test client."""
        from backend.app import create_app
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_search_endpoint_exists(self):
        """Test that the search endpoint exists."""
        response = self.client.post('/api/sloka/search', json={'text': 'test'})
        # Should not be 404
        self.assertNotEqual(response.status_code, 404)

    def test_validate_endpoint_exists(self):
        """Test that the validate endpoint exists."""
        response = self.client.post('/api/sloka/validate', json={'text': 'test'})
        # Should not be 404
        self.assertNotEqual(response.status_code, 404)

    def test_search_requires_text(self):
        """Test that search requires text field."""
        response = self.client.post('/api/sloka/search', json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data['success'])

    def test_search_finds_rigveda_verse(self):
        """Search returns the Rigveda 1.1.1 row with its Gayatri label."""
        response = self.client.post('/api/sloka/search', json={
            'text': 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं',
            'threshold': 0.9,
            'limit': 5
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['match_count'], 1)
        best = data['matches'][0]
        self.assertEqual(best['chandas'], 'gāyatrī')
        self.assertGreaterEqual(best['similarity'], 0.9)

    def test_validate_partial_verse(self):
        """Validating the first two padas finds the full Rigveda 1.1.1 verse."""
        response = self.client.post('/api/sloka/validate', json={
            'text': 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं'
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['found'])
        self.assertEqual(data['chandas'], 'gāyatrī')
        self.assertEqual(data['difference_count'], 0)

if __name__ == '__main__':
    # Run only the unit tests (not integration tests) by default
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSlokaSearch)
    unittest.TextTestRunner(verbosity=2).run(suite)
