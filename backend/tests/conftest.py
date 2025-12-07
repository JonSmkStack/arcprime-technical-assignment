"""Pytest configuration and fixtures."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# Set test environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("OPENAI_API_KEY", "test-key")


@pytest.fixture
def sample_pdf_path():
    """Path to sample PDF for testing."""
    return "/home/jon/arcprime-technical-assignment/docs/FinFET.pdf"


@pytest.fixture
def sample_pdf_bytes(sample_pdf_path):
    """Read sample PDF as bytes."""
    with open(sample_pdf_path, "rb") as f:
        return f.read()


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for extraction."""
    return {
        "title": "Test Invention Title",
        "description": "This is a test description of the invention.",
        "key_differences": "• Novel approach\n• Better performance",
        "inventors": [
            {"name": "John Doe", "email": "john@example.com"},
            {"name": "Jane Smith", "email": "jane@example.com"},
        ],
    }


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Create a mock OpenAI client."""
    import json

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def invalid_pdf_bytes():
    """Invalid PDF content for error testing."""
    return b"This is not a valid PDF file"


@pytest.fixture
def empty_pdf_bytes():
    """Minimal valid PDF with no text content."""
    # This is a minimal valid PDF structure
    return b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer << /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""
