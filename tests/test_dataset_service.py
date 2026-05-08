import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.services.dataset_service import list_vegetables, get_vegetable, get_kpis, _pct_change

class TestDatasetService:
    def test_list_vegetables(self, temp_config_dir):
        """Test listing vegetables returns catalog data"""
        config_path = Path(temp_config_dir) / "config" / "vegetables.json"
        
        with patch('app.services.config_service.CONFIG_PATH', config_path):
            result = list_vegetables()
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]['id'] == 'test_cabbage'

    def test_get_vegetable_success(self, temp_processed_dir, temp_config_dir):
        """Test getting vegetable data successfully"""
        config_path = Path(temp_config_dir) / "config" / "vegetables.json"
        
        with patch('app.services.config_service.CONFIG_PATH', config_path):
            with patch('app.services.dataset_service.PROCESSED_DIR', temp_processed_dir):
                result = get_vegetable('test_cabbage')
                
                assert 'meta' in result
                assert 'rows' in result
                assert 'columns' in result
                assert 'metrics' in result
                assert 'min_year' in result
                assert 'max_year' in result
                
                assert result['meta']['id'] == 'test_cabbage'
                assert result['min_year'] == 2020
                assert result['max_year'] == 2022
                assert len(result['rows']) == 3

    def test_get_vegetable_not_found(self, temp_config_dir):
        """Test getting vegetable with invalid dataset_id"""
        config_path = Path(temp_config_dir) / "config" / "vegetables.json"
        
        with patch('app.services.config_service.CONFIG_PATH', config_path):
            with pytest.raises(KeyError):
                get_vegetable('nonexistent_id')

    def test_get_vegetable_file_not_found(self, temp_config_dir):
        """Test getting vegetable when CSV file doesn't exist"""
        config_path = Path(temp_config_dir) / "config" / "vegetables.json"
        
        with patch('app.services.config_service.CONFIG_PATH', config_path):
            with pytest.raises(FileNotFoundError):
                get_vegetable('test_cabbage')

    def test_get_kpis_success(self, temp_processed_dir, temp_config_dir):
        """Test getting KPIs for all vegetables"""
        config_path = Path(temp_config_dir) / "config" / "vegetables.json"
        
        with patch('app.services.config_service.CONFIG_PATH', config_path):
            with patch('app.services.dataset_service.PROCESSED_DIR', temp_processed_dir):
                result = get_kpis()
                
                assert isinstance(result, list)
                assert len(result) == 1  # Only test_cabbage has CSV
                kpi = result[0]
                assert kpi['dataset_id'] == 'test_cabbage'
                assert kpi['vegetable'] == 'Cabbage'
                assert kpi['year'] == 2022
                assert kpi['production'] == 1200.0
                assert kpi['production_delta_pct'] == pytest.approx(9.09, rel=1e-2)  # (1200-1100)/1100 * 100

    def test_get_kpis_no_files(self, temp_config_dir):
        """Test getting KPIs when no CSV files exist"""
        config_path = Path(temp_config_dir) / "config" / "vegetables.json"
        
        with patch('app.services.config_service.CONFIG_PATH', config_path):
            with patch('app.services.dataset_service.PROCESSED_DIR', Path(temp_config_dir) / "data" / "processed"):
                result = get_kpis()
                
                assert result == []

    def test_pct_change_normal(self):
        """Test percentage change calculation with normal values"""
        result = _pct_change(100, 110)
        assert result == 10.0

    def test_pct_change_zero_prev(self):
        """Test percentage change when previous value is zero"""
        result = _pct_change(0, 100)
        assert result == 0.0

    def test_pct_change_zero_curr(self):
        """Test percentage change when current value is zero"""
        result = _pct_change(100, 0)
        assert result == -100.0

    def test_pct_change_invalid_values(self):
        """Test percentage change with invalid string values"""
        result = _pct_change("invalid", "also_invalid")
        assert result == 0.0

    def test_pct_change_none_values(self):
        """Test percentage change with None values"""
        result = _pct_change(None, None)
        assert result == 0.0