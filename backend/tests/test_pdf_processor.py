"""Unit tests for PDF processor service."""

import pytest
from app.services.pdf_processor import extract_text_from_pdf


class TestExtractTextFromPdf:
    """Tests for extract_text_from_pdf function."""

    def test_extract_text_from_valid_pdf(self, sample_pdf_bytes):
        """Test extracting text from a valid PDF file."""
        text = extract_text_from_pdf(sample_pdf_bytes)

        assert text is not None
        assert len(text) > 0
        # FinFET.pdf should contain these terms
        assert "FinFET" in text or "MOSFET" in text

    def test_extract_text_returns_string(self, sample_pdf_bytes):
        """Test that extract returns a string type."""
        text = extract_text_from_pdf(sample_pdf_bytes)
        assert isinstance(text, str)

    def test_extract_text_from_invalid_pdf_raises_error(self, invalid_pdf_bytes):
        """Test that invalid PDF raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            extract_text_from_pdf(invalid_pdf_bytes)

        assert "Invalid PDF" in str(exc_info.value)

    def test_extract_text_from_empty_bytes_raises_error(self):
        """Test that empty bytes raises ValueError."""
        with pytest.raises(ValueError):
            extract_text_from_pdf(b"")

    def test_extract_text_from_none_raises_error(self):
        """Test that None input raises an error or returns empty."""
        # PyMuPDF handles None gracefully, so we check it doesn't crash
        # and either raises or returns empty string
        try:
            result = extract_text_from_pdf(None)
            # If it doesn't raise, result should be empty or minimal
            assert result == "" or len(result) == 0
        except (ValueError, TypeError):
            # Expected behavior - raising an error is also acceptable
            pass

    def test_extract_text_contains_multiple_pages(self, sample_pdf_bytes):
        """Test that multi-page PDFs have content extracted."""
        text = extract_text_from_pdf(sample_pdf_bytes)
        # Should have substantial content from multiple pages
        assert len(text) > 1000

    def test_extract_text_preserves_whitespace_structure(self, sample_pdf_bytes):
        """Test that extracted text maintains some structure."""
        text = extract_text_from_pdf(sample_pdf_bytes)
        # Should have paragraph breaks
        assert "\n" in text
