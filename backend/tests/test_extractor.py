"""Unit tests for AI extractor service."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.extractor import extract_disclosure_info


class TestExtractDisclosureInfo:
    """Tests for extract_disclosure_info function."""

    @pytest.mark.asyncio
    async def test_extract_returns_required_fields(self, mock_openai_response):
        """Test that extraction returns all required fields."""
        with patch("app.services.extractor.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_openai_response)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            with patch("app.services.extractor.settings") as mock_settings:
                mock_settings.openai_api_key = "test-key"

                result = await extract_disclosure_info("Sample document text")

                assert "title" in result
                assert "description" in result
                assert "key_differences" in result
                assert "inventors" in result

    @pytest.mark.asyncio
    async def test_extract_title_is_string(self, mock_openai_response):
        """Test that title is returned as a string."""
        with patch("app.services.extractor.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_openai_response)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            with patch("app.services.extractor.settings") as mock_settings:
                mock_settings.openai_api_key = "test-key"

                result = await extract_disclosure_info("Sample document text")

                assert isinstance(result["title"], str)
                assert len(result["title"]) > 0

    @pytest.mark.asyncio
    async def test_extract_inventors_is_list(self, mock_openai_response):
        """Test that inventors is returned as a list."""
        with patch("app.services.extractor.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_openai_response)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            with patch("app.services.extractor.settings") as mock_settings:
                mock_settings.openai_api_key = "test-key"

                result = await extract_disclosure_info("Sample document text")

                assert isinstance(result["inventors"], list)

    @pytest.mark.asyncio
    async def test_extract_converts_list_to_string(self):
        """Test that list values are converted to bullet-point strings."""
        response_with_list = {
            "title": "Test Title",
            "description": "Test description",
            "key_differences": ["Point 1", "Point 2", "Point 3"],
            "inventors": [],
        }

        with patch("app.services.extractor.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(response_with_list)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            with patch("app.services.extractor.settings") as mock_settings:
                mock_settings.openai_api_key = "test-key"

                result = await extract_disclosure_info("Sample document text")

                assert isinstance(result["key_differences"], str)
                assert "• Point 1" in result["key_differences"]
                assert "• Point 2" in result["key_differences"]

    @pytest.mark.asyncio
    async def test_extract_handles_markdown_json(self):
        """Test that markdown-wrapped JSON is properly parsed."""
        response_data = {
            "title": "Test Title",
            "description": "Test description",
            "key_differences": "Novel approach",
            "inventors": [],
        }

        with patch("app.services.extractor.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            # Wrap in markdown code block
            mock_response.choices[0].message.content = f"```json\n{json.dumps(response_data)}\n```"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            with patch("app.services.extractor.settings") as mock_settings:
                mock_settings.openai_api_key = "test-key"

                result = await extract_disclosure_info("Sample document text")

                assert result["title"] == "Test Title"

    @pytest.mark.asyncio
    async def test_extract_raises_on_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        with patch("app.services.extractor.settings") as mock_settings:
            mock_settings.openai_api_key = ""

            with pytest.raises(ValueError) as exc_info:
                await extract_disclosure_info("Sample document text")

            assert "API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_raises_on_invalid_json(self):
        """Test that invalid JSON response raises ValueError."""
        with patch("app.services.extractor.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "This is not valid JSON"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            with patch("app.services.extractor.settings") as mock_settings:
                mock_settings.openai_api_key = "test-key"

                with pytest.raises(ValueError) as exc_info:
                    await extract_disclosure_info("Sample document text")

                assert "Invalid JSON" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_raises_on_missing_required_field(self):
        """Test that missing required field raises ValueError."""
        incomplete_response = {
            "title": "Test Title",
            # Missing description and key_differences
        }

        with patch("app.services.extractor.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(incomplete_response)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            with patch("app.services.extractor.settings") as mock_settings:
                mock_settings.openai_api_key = "test-key"

                with pytest.raises(ValueError) as exc_info:
                    await extract_disclosure_info("Sample document text")

                assert "Missing required field" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_raises_on_empty_response(self):
        """Test that empty AI response raises ValueError."""
        with patch("app.services.extractor.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = None
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            with patch("app.services.extractor.settings") as mock_settings:
                mock_settings.openai_api_key = "test-key"

                with pytest.raises(ValueError) as exc_info:
                    await extract_disclosure_info("Sample document text")

                assert "Empty response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_handles_missing_inventors(self):
        """Test that missing inventors defaults to empty list."""
        response_without_inventors = {
            "title": "Test Title",
            "description": "Test description",
            "key_differences": "Novel approach",
            # No inventors field
        }

        with patch("app.services.extractor.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(response_without_inventors)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            with patch("app.services.extractor.settings") as mock_settings:
                mock_settings.openai_api_key = "test-key"

                result = await extract_disclosure_info("Sample document text")

                assert result["inventors"] == []
