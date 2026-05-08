import pytest
from unittest.mock import patch
from app.services.ai_service import ai_status

class TestAIService:
    def test_ai_status_groq_configured(self):
        """Test AI status with Groq provider and configured API key"""
        mock_settings = {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "test_key",
            "GROQ_MODEL": "llama2-70b",
            "OPENAI_API_KEY": "",
            "OPENAI_MODEL": "",
            "ENABLE_AI_ASSISTANT": True
        }
        
        with patch('app.services.ai_service.SETTINGS', mock_settings):
            result = ai_status()
            
            assert result == {
                "provider": "groq",
                "model": "llama2-70b",
                "configured": True,
                "enabled": True,
                "mode": "rag_llm"
            }

    def test_ai_status_groq_not_configured(self):
        """Test AI status with Groq provider but no API key"""
        mock_settings = {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "",
            "GROQ_MODEL": "llama2-70b",
            "OPENAI_API_KEY": "",
            "OPENAI_MODEL": "",
            "ENABLE_AI_ASSISTANT": False
        }
        
        with patch('app.services.ai_service.SETTINGS', mock_settings):
            result = ai_status()
            
            assert result == {
                "provider": "groq",
                "model": "llama2-70b",
                "configured": False,
                "enabled": False,
                "mode": "rag_llm"
            }

    def test_ai_status_openai_configured(self):
        """Test AI status with OpenAI provider and configured API key"""
        mock_settings = {
            "LLM_PROVIDER": "openai",
            "GROQ_API_KEY": "",
            "GROQ_MODEL": "",
            "OPENAI_API_KEY": "openai_key",
            "OPENAI_MODEL": "gpt-4",
            "ENABLE_AI_ASSISTANT": True
        }
        
        with patch('app.services.ai_service.SETTINGS', mock_settings):
            result = ai_status()
            
            assert result == {
                "provider": "openai",
                "model": "gpt-4",
                "configured": True,
                "enabled": True,
                "mode": "rag_llm"
            }

    def test_ai_status_openai_not_configured(self):
        """Test AI status with OpenAI provider but no API key"""
        mock_settings = {
            "LLM_PROVIDER": "openai",
            "GROQ_API_KEY": "",
            "GROQ_MODEL": "",
            "OPENAI_API_KEY": "",
            "OPENAI_MODEL": "gpt-4",
            "ENABLE_AI_ASSISTANT": False
        }
        
        with patch('app.services.ai_service.SETTINGS', mock_settings):
            result = ai_status()
            
            assert result == {
                "provider": "openai",
                "model": "gpt-4",
                "configured": False,
                "enabled": False,
                "mode": "rag_llm"
            }