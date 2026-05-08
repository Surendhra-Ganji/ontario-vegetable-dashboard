import pytest
from unittest.mock import patch
from app.services.settings import get_setting, get_int, get_float

class TestSettings:
    def test_get_setting_with_value(self):
        """Test get_setting when environment variable exists"""
        with patch.dict('os.environ', {'TEST_VAR': 'test_value'}):
            result = get_setting('TEST_VAR')
            assert result == 'test_value'

    def test_get_setting_with_default(self):
        """Test get_setting with default when env var doesn't exist"""
        with patch.dict('os.environ', {}, clear=True):
            result = get_setting('NONEXISTENT', 'default_value')
            assert result == 'default_value'

    def test_get_setting_none_default(self):
        """Test get_setting with None default when env var doesn't exist"""
        with patch.dict('os.environ', {}, clear=True):
            result = get_setting('NONEXISTENT')
            assert result is None

    def test_get_int_valid(self):
        """Test get_int with valid integer string"""
        with patch.dict('os.environ', {'INT_VAR': '42'}):
            result = get_int('INT_VAR', 10)
            assert result == 42
            assert isinstance(result, int)

    def test_get_int_invalid(self):
        """Test get_int with invalid string returns default"""
        with patch.dict('os.environ', {'INT_VAR': 'not_a_number'}):
            result = get_int('INT_VAR', 10)
            assert result == 10

    def test_get_int_missing(self):
        """Test get_int with missing env var returns default"""
        with patch.dict('os.environ', {}, clear=True):
            result = get_int('MISSING_VAR', 25)
            assert result == 25

    def test_get_float_valid(self):
        """Test get_float with valid float string"""
        with patch.dict('os.environ', {'FLOAT_VAR': '3.14'}):
            result = get_float('FLOAT_VAR', 1.0)
            assert result == 3.14
            assert isinstance(result, float)

    def test_get_float_invalid(self):
        """Test get_float with invalid string returns default"""
        with patch.dict('os.environ', {'FLOAT_VAR': 'not_a_float'}):
            result = get_float('FLOAT_VAR', 2.5)
            assert result == 2.5

    def test_get_float_missing(self):
        """Test get_float with missing env var returns default"""
        with patch.dict('os.environ', {}, clear=True):
            result = get_float('MISSING_VAR', 1.5)
            assert result == 1.5