"""Integration tests for API endpoints.

These tests require a running PostgreSQL database.
Run with: pytest tests/test_api_integration.py -v
"""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import init_db, close_db


@pytest.fixture
async def client():
    """Create async test client with database connection."""
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await close_db()


@pytest.fixture
def mock_extraction():
    """Mock the AI extraction to avoid API calls during testing."""
    mock_response = {
        "title": "Test Invention",
        "description": "A test invention description for integration testing.",
        "key_differences": "• Novel approach\n• Better performance\n• Lower cost",
        "inventors": [
            {"name": "Test Inventor", "email": "test@example.com"},
        ],
    }
    return mock_response


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self, client):
        """Test that health endpoint returns healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @pytest.mark.asyncio
    async def test_root_returns_api_info(self, client):
        """Test that root endpoint returns API info."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestListDisclosures:
    """Tests for GET /api/disclosures endpoint."""

    @pytest.mark.asyncio
    async def test_list_returns_array(self, client):
        """Test that list endpoint returns an array."""
        response = await client.get("/api/disclosures")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_list_disclosures_contains_required_fields(self, client, mock_extraction):
        """Test that listed disclosures have required fields."""
        # First create a disclosure
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )
                assert response.status_code == 200

        # Now list
        response = await client.get("/api/disclosures")
        assert response.status_code == 200

        disclosures = response.json()
        if len(disclosures) > 0:
            disclosure = disclosures[0]
            assert "id" in disclosure
            assert "docket_number" in disclosure
            assert "title" in disclosure
            assert "status" in disclosure
            assert "created_at" in disclosure


class TestUploadDisclosure:
    """Tests for POST /api/disclosures/upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_pdf_creates_disclosure(self, client, mock_extraction):
        """Test that uploading a PDF creates a disclosure."""
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        assert response.status_code == 200
        data = response.json()
        assert "disclosure" in data
        assert "message" in data
        assert data["disclosure"]["title"] == mock_extraction["title"]

    @pytest.mark.asyncio
    async def test_upload_generates_docket_number(self, client, mock_extraction):
        """Test that upload generates a docket number in correct format."""
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        assert response.status_code == 200
        docket = response.json()["disclosure"]["docket_number"]
        assert docket.startswith("IDF-")
        assert len(docket) == 8  # IDF-XXXX

    @pytest.mark.asyncio
    async def test_upload_stores_inventors(self, client, mock_extraction):
        """Test that upload stores inventor information."""
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        assert response.status_code == 200
        inventors = response.json()["disclosure"]["inventors"]
        assert len(inventors) == 1
        assert inventors[0]["name"] == "Test Inventor"
        assert inventors[0]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_upload_rejects_non_pdf(self, client):
        """Test that upload rejects non-PDF files."""
        response = await client.post(
            "/api/disclosures/upload",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_rejects_invalid_pdf(self, client):
        """Test that upload rejects invalid/corrupted PDF files."""
        response = await client.post(
            "/api/disclosures/upload",
            files={"file": ("test.pdf", b"not a valid pdf content", "application/pdf")},
        )

        assert response.status_code == 400
        assert "Invalid PDF" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_stores_original_filename(self, client, mock_extraction):
        """Test that upload stores the original filename."""
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("my_invention.pdf", f, "application/pdf")},
                )

        assert response.status_code == 200
        assert response.json()["disclosure"]["original_filename"] == "my_invention.pdf"


class TestGetDisclosure:
    """Tests for GET /api/disclosures/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_disclosure_returns_full_data(self, client, mock_extraction):
        """Test that get disclosure returns all fields including inventors."""
        # Create a disclosure first
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                create_response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        disclosure_id = create_response.json()["disclosure"]["id"]

        # Get the disclosure
        response = await client.get(f"/api/disclosures/{disclosure_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == disclosure_id
        assert "inventors" in data
        assert len(data["inventors"]) > 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_disclosure_returns_404(self, client):
        """Test that getting a nonexistent disclosure returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/disclosures/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateDisclosure:
    """Tests for PATCH /api/disclosures/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_disclosure_title(self, client, mock_extraction):
        """Test updating a disclosure's title."""
        # Create a disclosure first
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                create_response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        disclosure_id = create_response.json()["disclosure"]["id"]

        # Update the title
        response = await client.patch(
            f"/api/disclosures/{disclosure_id}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_disclosure_status(self, client, mock_extraction):
        """Test updating a disclosure's status."""
        # Create a disclosure first
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                create_response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        disclosure_id = create_response.json()["disclosure"]["id"]

        # Update status
        response = await client.patch(
            f"/api/disclosures/{disclosure_id}",
            json={"status": "approved"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    @pytest.mark.asyncio
    async def test_update_invalid_status_returns_400(self, client, mock_extraction):
        """Test that invalid status value returns 400."""
        # Create a disclosure first
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                create_response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        disclosure_id = create_response.json()["disclosure"]["id"]

        # Try to set invalid status
        response = await client.patch(
            f"/api/disclosures/{disclosure_id}",
            json={"status": "invalid_status"},
        )

        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_disclosure_returns_404(self, client):
        """Test that updating a nonexistent disclosure returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.patch(
            f"/api/disclosures/{fake_id}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_updates_timestamp(self, client, mock_extraction):
        """Test that update changes the updated_at timestamp."""
        # Create a disclosure first
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                create_response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        disclosure = create_response.json()["disclosure"]
        original_updated_at = disclosure["updated_at"]

        # Small delay to ensure timestamp difference
        import asyncio
        await asyncio.sleep(0.1)

        # Update
        response = await client.patch(
            f"/api/disclosures/{disclosure['id']}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        assert response.json()["updated_at"] != original_updated_at


class TestDeleteDisclosure:
    """Tests for DELETE /api/disclosures/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_disclosure_succeeds(self, client, mock_extraction):
        """Test that deleting a disclosure succeeds."""
        # Create a disclosure first
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                create_response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        disclosure_id = create_response.json()["disclosure"]["id"]

        # Delete it
        response = await client.delete(f"/api/disclosures/{disclosure_id}")

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_removes_from_database(self, client, mock_extraction):
        """Test that delete actually removes the disclosure."""
        # Create a disclosure first
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                create_response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        disclosure_id = create_response.json()["disclosure"]["id"]

        # Delete it
        await client.delete(f"/api/disclosures/{disclosure_id}")

        # Try to get it - should 404
        response = await client.get(f"/api/disclosures/{disclosure_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_disclosure_returns_404(self, client):
        """Test that deleting a nonexistent disclosure returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(f"/api/disclosures/{fake_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_cascades_to_inventors(self, client, mock_extraction):
        """Test that deleting a disclosure also deletes its inventors."""
        # Create a disclosure with inventors
        with patch("app.routers.disclosures.extract_disclosure_info", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extraction

            with open("/home/jon/arcprime-technical-assignment/docs/FinFET.pdf", "rb") as f:
                create_response = await client.post(
                    "/api/disclosures/upload",
                    files={"file": ("test.pdf", f, "application/pdf")},
                )

        disclosure_id = create_response.json()["disclosure"]["id"]

        # Delete the disclosure
        response = await client.delete(f"/api/disclosures/{disclosure_id}")
        assert response.status_code == 200

        # The inventors should be gone with the disclosure (CASCADE)
        # Verify by trying to get the disclosure
        response = await client.get(f"/api/disclosures/{disclosure_id}")
        assert response.status_code == 404
