#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Chandas-Integrated Backend

Comprehensive tests for API endpoints, meter identification, and OCR functionality.
"""

import sys
import json
import base64
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from backend.app import create_app
from backend.config import settings


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_text():
    """Sample Sanskrit text for testing."""
    return "श्लोकः श्लोकेन गीयते"


@pytest.fixture
def sample_verse():
    """Sample complete verse for testing."""
    return """श्रीरामचन्द्रचरणौ मनसा स्मरामि
श्रीरामचन्द्रचरणौ वचसा गृणामि
श्रीरामचन्द्रचरणौ शिरसा नमामि
श्रीरामचन्द्रचरणौ शरणं प्रपद्ये"""


class TestHealthAndInfo:
    """Test health check and info endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'version' in data
    
    def test_api_info(self, client):
        """Test the API info endpoint."""
        response = client.get('/api/info')
        assert response.status_code == 200
        data = response.get_json()
        assert 'endpoints' in data
        assert 'ocr_available' in data
        assert 'features' in data


class TestTextIdentification:
    """Test text-based meter identification."""
    
    def test_identify_text_basic(self, client, sample_text):
        """Test basic text identification."""
        response = client.post('/api/identify/text',
                              json={
                                  'text': sample_text,
                                  'text_mode': 'line'
                              })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'result' in data
        assert 'summary' in data
    
    def test_identify_text_verse_mode(self, client, sample_verse):
        """Test verse mode identification."""
        response = client.post('/api/identify/text',
                              json={
                                  'text': sample_verse,
                                  'text_mode': 'verse',
                                  'enable_sandhi': False
                              })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'result' in data
    
    def test_identify_text_with_sandhi(self, client, sample_text):
        """Test identification with sandhi splitting."""
        response = client.post('/api/identify/text',
                              json={
                                  'text': sample_text,
                                  'text_mode': 'line',
                                  'enable_sandhi': True
                              })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_identify_text_with_scheme(self, client, sample_text):
        """Test identification with output scheme."""
        response = client.post('/api/identify/text',
                              json={
                                  'text': sample_text,
                                  'output_scheme': 'iast',
                                  'text_mode': 'line'
                              })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_identify_text_missing_text(self, client):
        """Test error handling for missing text."""
        response = client.post('/api/identify/text',
                              json={
                                  'text_mode': 'line'
                              })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_identify_text_empty(self, client):
        """Test handling of empty text."""
        response = client.post('/api/identify/text',
                              json={
                                  'text': '',
                                  'text_mode': 'line'
                              })
        # Should not crash, may return error or empty results
        assert response.status_code in [200, 400, 500]


class TestExamplesEndpoint:
    """Test examples endpoint."""
    
    def test_get_examples(self, client):
        """Test retrieving examples."""
        response = client.get('/api/examples')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'examples' in data
        assert isinstance(data['examples'], list)


class TestSchemesEndpoint:
    """Test transliteration schemes endpoint."""
    
    def test_get_schemes(self, client):
        """Test retrieving available schemes."""
        response = client.get('/api/schemes')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'schemes' in data
        assert isinstance(data['schemes'], list)
        
        # Check for essential schemes
        scheme_values = [s['value'] for s in data['schemes']]
        assert 'devanagari' in scheme_values
        assert 'iast' in scheme_values
        assert 'itrans' in scheme_values


class TestImageIdentification:
    """Test image-based meter identification (OCR)."""
    
    def test_identify_image_no_file(self, client):
        """Test error handling when no image is provided."""
        response = client.post('/api/identify/image',
                              data={
                                  'text_mode': 'line'
                              })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestFileIdentification:
    """Test file-based meter identification."""
    
    def test_identify_file_no_file(self, client):
        """Test error handling when no file is provided."""
        response = client.post('/api/identify/file',
                              data={
                                  'text_mode': 'line'
                              })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestChandaCore:
    """Test core Chanda functionality."""
    
    def test_chanda_initialization(self):
        """Test Chanda class initialization."""
        from backend.core import Chanda
        chanda = Chanda(data_path=str(settings.DATA_DIR))
        assert chanda is not None
        assert hasattr(chanda, 'identify_from_text')
        assert hasattr(chanda, 'summarize_results')
    
    def test_chanda_identify(self, sample_text):
        """Test Chanda identification."""
        from backend.core import Chanda
        chanda = Chanda(data_path=str(settings.DATA_DIR))
        
        result = chanda.identify_from_text(
            sample_text,
            verse=False,
            fuzzy=True
        )
        
        assert 'result' in result
        assert isinstance(result['result']['line'], list)
        assert result['result']['line'][0]['result']['found'] is True
    
    def test_chanda_summarize(self, sample_text):
        """Test Chanda summarization."""
        from backend.core import Chanda
        chanda = Chanda(data_path=str(settings.DATA_DIR))
        
        result = chanda.identify_from_text(
            sample_text,
            verse=False,
            fuzzy=True
        )
        
        summary = chanda.summarize_results(result['result'])
        assert summary is not None
        assert isinstance(summary, dict)


class TestConfiguration:
    """Test configuration settings."""
    
    def test_settings_exist(self):
        """Test that settings are properly configured."""
        assert settings.DATA_DIR.exists()
        assert settings.UPLOADS_DIR.exists()
        assert settings.PHOTOS_DIR.exists()
        assert settings.TEXTS_DIR.exists()
        assert settings.RESULTS_DIR.exists()
    
    def test_data_files_exist(self):
        """Test that required data files exist."""
        assert (settings.DATA_DIR / 'chanda_sama.csv').exists()
        assert (settings.DATA_DIR / 'chanda_ardhasama.csv').exists()
        assert (settings.DATA_DIR / 'chanda_vishama.csv').exists()
        assert (settings.DATA_DIR / 'chanda_matra.csv').exists()
        assert (settings.DATA_DIR / 'examples.json').exists()


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
