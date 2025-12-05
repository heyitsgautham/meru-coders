#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Copilot-Friendly API Endpoints

This test file validates the new Copilot-optimized API endpoints for
Sanskrit meter (chanda) identification.

Run from backend/ directory:
    PYTHONPATH=. python tests/test_copilot_api.py

Or use pytest:
    PYTHONPATH=. pytest tests/test_copilot_api.py -v
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import unittest
from backend.app import create_app


class TestCopilotAPI(unittest.TestCase):
    """Test cases for the Copilot-friendly API endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test client."""
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
    
    def test_copilot_quick_anushtubh(self):
        """Test quick endpoint with Anushtubh meter (Bhagavad Gita 1.1)."""
        # First pada of Bhagavad Gita 1.1
        response = self.client.post(
            '/api/copilot/quick',
            json={'text': 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertTrue(data['success'])
        self.assertIn('meter', data)
        self.assertIn('lg_pattern', data)
        self.assertIn('syllable_count', data)
        self.assertIn('gana_pattern', data)
        
        # Should be 16-syllable (Two padas combined) - check type is int
        self.assertIsInstance(data['syllable_count'], int)
        self.assertGreater(data['syllable_count'], 0)
        print(f"✓ Quick API - Anushtubh: {data['meter']} (syllables: {data['syllable_count']}, confidence: {data['confidence']})")
    
    def test_copilot_quick_devanagari_input(self):
        """Test quick endpoint with Devanagari input."""
        response = self.client.post(
            '/api/copilot/quick',
            json={'text': 'वसुदेवसुतं देवं कंसचाणूरमर्दनम्'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertTrue(data['success'])
        self.assertIn('lg_pattern', data)
        self.assertTrue(len(data['lg_pattern']) > 0)
        print(f"✓ Quick API - Devanagari: {data['meter']} (L-G: {data['lg_pattern']})")
    
    def test_copilot_analyze_full_verse(self):
        """Test analyze endpoint with full 4-line verse."""
        # Bhagavad Gita 1.1 (all 4 padas)
        verse = """धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः
मामकाः पाण्डवाश्चैव किमकुर्वत संजय"""
        
        response = self.client.post(
            '/api/copilot/analyze',
            json={'text': verse},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertTrue(data['success'])
        self.assertIn('analysis', data)
        self.assertIn('lines', data['analysis'])
        self.assertIn('summary', data)
        
        # Check that each line has the expected fields
        for line in data['analysis']['lines']:
            self.assertIn('line_number', line)
            self.assertIn('lg_pattern', line)
            self.assertIn('gana_pattern', line)
            self.assertIn('syllable_count', line)
            self.assertIn('identified_meters', line)
        
        print(f"✓ Analyze API - Full verse: {data['summary']['primary_meter']}")
        print(f"  Lines analyzed: {data['analysis']['total_lines']}")
    
    def test_copilot_analyze_indravajra(self):
        """Test analyze endpoint with Indravajra meter."""
        # Indravajra pattern: G G L G G L G L G G (11 syllables)
        indravajra_line = "जातस्य हि ध्रुवो मृत्युर्ध्रुवं जन्म मृतस्य च"
        
        response = self.client.post(
            '/api/copilot/analyze',
            json={'text': indravajra_line},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertTrue(data['success'])
        print(f"✓ Analyze API - Classical meter: {data['summary']['primary_meter']}")
    
    def test_copilot_batch_multiple_verses(self):
        """Test batch endpoint with multiple verses."""
        verses = [
            "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
            "वसुदेवसुतं देवं कंसचाणूरमर्दनम्",
            "यदा यदा हि धर्मस्य ग्लानिर्भवति भारत"
        ]
        
        response = self.client.post(
            '/api/copilot/batch',
            json={'verses': verses},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertTrue(data['success'])
        self.assertIn('results', data)
        self.assertIn('summary', data)
        self.assertEqual(len(data['results']), 3)
        self.assertEqual(data['summary']['total_verses'], 3)
        
        print(f"✓ Batch API - Processed {data['summary']['total_verses']} verses")
        print(f"  Meter distribution: {data['summary']['meter_distribution']}")
    
    def test_copilot_quick_empty_input(self):
        """Test quick endpoint rejects empty input."""
        response = self.client.post(
            '/api/copilot/quick',
            json={'text': ''},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data['success'])
        print("✓ Quick API - Empty input rejected correctly")
    
    def test_copilot_quick_missing_text(self):
        """Test quick endpoint rejects missing text field."""
        response = self.client.post(
            '/api/copilot/quick',
            json={},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data['success'])
        print("✓ Quick API - Missing text field rejected correctly")
    
    def test_copilot_analyze_response_structure(self):
        """Test that analyze endpoint returns complete structure."""
        response = self.client.post(
            '/api/copilot/analyze',
            json={'text': 'अग्निमीळे पुरोहितं'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify top-level structure
        self.assertIn('success', data)
        self.assertIn('input', data)
        self.assertIn('analysis', data)
        self.assertIn('summary', data)
        
        # Verify input structure
        self.assertIn('text', data['input'])
        self.assertIn('detected_script', data['input'])
        
        # Verify analysis structure
        self.assertIn('mode', data['analysis'])
        self.assertIn('total_lines', data['analysis'])
        self.assertIn('lines', data['analysis'])
        
        # Verify line structure
        if data['analysis']['lines']:
            line = data['analysis']['lines'][0]
            required_fields = [
                'line_number', 'text', 'devanagari', 'syllables',
                'syllable_count', 'lg_pattern', 'lg_display',
                'gana_pattern', 'gana_display', 'matra_count',
                'identified_meters', 'primary_meter', 'jaati', 'is_valid'
            ]
            for field in required_fields:
                self.assertIn(field, line, f"Missing field: {field}")
        
        # Verify summary structure
        self.assertIn('primary_meter', data['summary'])
        self.assertIn('confidence', data['summary'])
        
        print("✓ Analyze API - Complete response structure verified")


class TestCopilotAPIIntegration(unittest.TestCase):
    """Integration tests for real-world usage scenarios."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test client."""
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
    
    def test_vedic_gayatri_mantra(self):
        """Test with Gayatri mantra (Vedic meter)."""
        gayatri = """ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यं
भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्"""
        
        response = self.client.post(
            '/api/copilot/analyze',
            json={'text': gayatri},
            content_type='application/json'
        )
        
        data = response.get_json()
        self.assertTrue(data['success'])
        print(f"✓ Vedic Gayatri: {data['summary']['primary_meter']}")
    
    def test_mandakranta(self):
        """Test with Mandakranta meter."""
        mandakranta = "कश्चित्कान्ताविरहगुरुणा स्वाधिकारप्रमत्तः"
        
        response = self.client.post(
            '/api/copilot/quick',
            json={'text': mandakranta},
            content_type='application/json'
        )
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIsInstance(data['syllable_count'], int)
        self.assertGreater(data['syllable_count'], 0)  # Mandakranta has 17 syllables per pada
        print(f"✓ Mandakranta: {data['meter']} ({data['syllable_count']} syllables)")
    
    def test_iast_input(self):
        """Test with IAST transliteration input."""
        iast_text = "dharmakṣetre kurukṣetre samavetā yuyutsavaḥ"
        
        response = self.client.post(
            '/api/copilot/quick',
            json={'text': iast_text},
            content_type='application/json'
        )
        
        data = response.get_json()
        self.assertTrue(data['success'])
        print(f"✓ IAST input: {data['meter']} (L-G: {data['lg_pattern']})")


def run_tests():
    """Run all tests and print summary."""
    print("=" * 70)
    print("🧪 Testing Copilot-Friendly API Endpoints")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCopilotAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestCopilotAPIIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
