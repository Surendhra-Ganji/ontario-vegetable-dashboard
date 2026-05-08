import pytest
import json
from pathlib import Path
from unittest.mock import patch
from app.services.config_service import load_vegetable_catalog, vegetable_lookup

class TestConfigService:
    def test_load_vegetable_catalog_success(self, temp_config_dir):
        """Test loading vegetable catalog from valid JSON file"""
        config_path = Path(temp_config_dir) / "config" / "vegetables.json"
        
        with patch('app.services.config_service.CONFIG_PATH', config_path):
            result = load_vegetable_catalog()
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]['id'] == 'test_cabbage'
            assert result[1]['name'] == 'Test Tomato'

    def test_load_vegetable_catalog_file_not_found(self):
        """Test loading when config file doesn't exist"""
        with patch('app.services.config_service.CONFIG_PATH', Path('/nonexistent/path.json')):
            with pytest.raises(FileNotFoundError):
                load_vegetable_catalog()

    def test_load_vegetable_catalog_invalid_json(self, tmp_path):
        """Test loading with invalid JSON"""
        invalid_config = tmp_path / "invalid.json"
        invalid_config.write_text("{invalid json")
        
        with patch('app.services.config_service.CONFIG_PATH', invalid_config):
            with pytest.raises(json.JSONDecodeError):
                load_vegetable_catalog()

    def test_vegetable_lookup_success(self, temp_config_dir):
        """Test creating lookup dictionary"""
        config_path = Path(temp_config_dir) / "config" / "vegetables.json"
        
        with patch('app.services.config_service.CONFIG_PATH', config_path):
            result = vegetable_lookup()
            
            assert isinstance(result, dict)
            assert 'test_cabbage' in result
            assert 'test_tomato' in result
            assert result['test_cabbage']['display_name'] == 'Cabbage'
            assert result['test_tomato']['dataset_slug'] == 'test-tomato-data'