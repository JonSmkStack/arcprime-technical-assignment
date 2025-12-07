import csv
import io
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, Response

from app.database import get_connection, get_next_docket_number
from app.models import (
    Disclosure,
    DisclosureWithInventors,
    DisclosureUpdate,
    Inventor,
    StatusHistoryEntry,
    UploadResponse,
)
from app.services.pdf_processor import extract_text_from_pdf
from app.services.extractor import extract_disclosure_info
from app.services import storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/disclosures", tags=["disclosures"])


@router.get("", response_model=list[Disclosure])
async def list_disclosures(
    search: str | None = None,
    status: str | None = None,
):
    """List all disclosures with optional search and filter."""
    async with get_connection() as conn:
        query = """
            SELECT id, docket_number, title, description, key_differences,
                   status, review_notes, original_filename, pdf_object_key, created_at, updated_at
            FROM disclosures
            WHERE 1=1
        """
        params = []
        param_idx = 1

        if search:
            query += f"""
                AND (
                    title ILIKE ${param_idx}
                    OR description ILIKE ${param_idx}
                    OR docket_number ILIKE ${param_idx}
                )
            """
            params.append(f"%{search}%")
            param_idx += 1

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status)
            param_idx += 1

        query += " ORDER BY created_at DESC"

        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]


@router.get("/export/csv")
async def export_disclosures_csv(
    search: str | None = None,
    status: str | None = None,
):
    """Export disclosures to CSV with inventor information."""
    async with get_connection() as conn:
        # Build query with same filters as list endpoint
        query = """
            SELECT d.id, d.docket_number, d.title, d.description, d.key_differences,
                   d.status, d.review_notes, d.original_filename, d.created_at, d.updated_at
            FROM disclosures d
            WHERE 1=1
        """
        params = []
        param_idx = 1

        if search:
            query += f"""
                AND (
                    d.title ILIKE ${param_idx}
                    OR d.description ILIKE ${param_idx}
                    OR d.docket_number ILIKE ${param_idx}
                )
            """
            params.append(f"%{search}%")
            param_idx += 1

        if status:
            query += f" AND d.status = ${param_idx}"
            params.append(status)
            param_idx += 1

        query += " ORDER BY d.created_at DESC"

        rows = await conn.fetch(query, *params)

        # Get inventors for each disclosure
        disclosure_ids = [row["id"] for row in rows]
        inventors_by_disclosure = {}

        if disclosure_ids:
            inventor_rows = await conn.fetch(
                """
                SELECT disclosure_id, name, email
                FROM inventors
                WHERE disclosure_id = ANY($1)
                ORDER BY created_at
                """,
                disclosure_ids,
            )
            for inv in inventor_rows:
                did = inv["disclosure_id"]
                if did not in inventors_by_disclosure:
                    inventors_by_disclosure[did] = {"names": [], "emails": []}
                inventors_by_disclosure[did]["names"].append(inv["name"])
                if inv["email"]:
                    inventors_by_disclosure[did]["emails"].append(inv["email"])

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Docket Number",
            "Title",
            "Description",
            "Key Differences",
            "Status",
            "Review Notes",
            "Original Filename",
            "Inventor Names",
            "Inventor Emails",
            "Created At",
            "Updated At",
        ])

        # Write data rows
        for row in rows:
            inv_data = inventors_by_disclosure.get(row["id"], {"names": [], "emails": []})
            writer.writerow([
                row["docket_number"],
                row["title"],
                row["description"],
                row["key_differences"],
                row["status"],
                row["review_notes"] or "",
                row["original_filename"] or "",
                "; ".join(inv_data["names"]),
                "; ".join(inv_data["emails"]),
                row["created_at"].isoformat() if row["created_at"] else "",
                row["updated_at"].isoformat() if row["updated_at"] else "",
            ])

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=disclosures.csv"},
        )


@router.get("/{disclosure_id}", response_model=DisclosureWithInventors)
async def get_disclosure(disclosure_id: UUID):
    """Get a single disclosure with its inventors."""
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, docket_number, title, description, key_differences,
                   status, review_notes, original_filename, pdf_object_key, created_at, updated_at
            FROM disclosures
            WHERE id = $1
            """,
            disclosure_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Disclosure not found")

        disclosure = dict(row)

        inventor_rows = await conn.fetch(
            """
            SELECT id, disclosure_id, name, email, created_at
            FROM inventors
            WHERE disclosure_id = $1
            ORDER BY created_at
            """,
            disclosure_id,
        )
        disclosure["inventors"] = [dict(r) for r in inventor_rows]

        # Fetch status history
        history_rows = await conn.fetch(
            """
            SELECT id, disclosure_id, status, changed_at
            FROM status_history
            WHERE disclosure_id = $1
            ORDER BY changed_at DESC
            """,
            disclosure_id,
        )
        disclosure["status_history"] = [dict(r) for r in history_rows]

        return disclosure


@router.post("/upload", response_model=UploadResponse)
async def upload_disclosure(file: UploadFile = File(...)):
    """Upload a PDF and extract disclosure information."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        content = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    # Extract text from PDF
    try:
        text = extract_text_from_pdf(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text or len(text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Could not extract sufficient text from PDF. The file may be image-based or corrupted.",
        )

    # Extract structured information using AI
    try:
        extracted = await extract_disclosure_info(text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract information from document: {str(e)}",
        )

    # Generate docket number and save to database
    docket_number = await get_next_docket_number()

    async with get_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO disclosures (docket_number, title, description, key_differences, original_filename)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, docket_number, title, description, key_differences,
                          status, review_notes, original_filename, pdf_object_key, created_at, updated_at
                """,
                docket_number,
                extracted["title"],
                extracted["description"],
                extracted["key_differences"],
                file.filename,
            )
            disclosure = dict(row)

            # Upload PDF to MinIO storage
            try:
                pdf_object_key = storage.upload_pdf(
                    str(disclosure["id"]),
                    file.filename,
                    content,
                )
                # Update disclosure with the object key
                await conn.execute(
                    "UPDATE disclosures SET pdf_object_key = $1 WHERE id = $2",
                    pdf_object_key,
                    disclosure["id"],
                )
                disclosure["pdf_object_key"] = pdf_object_key
            except Exception as e:
                logger.warning(f"Failed to upload PDF to storage: {e}")

            inventors = []
            for inv in extracted.get("inventors", []):
                inv_row = await conn.fetchrow(
                    """
                    INSERT INTO inventors (disclosure_id, name, email)
                    VALUES ($1, $2, $3)
                    RETURNING id, disclosure_id, name, email, created_at
                    """,
                    disclosure["id"],
                    inv.get("name", "Unknown"),
                    inv.get("email"),
                )
                inventors.append(dict(inv_row))

            disclosure["inventors"] = inventors

            # Record initial status in history
            history_row = await conn.fetchrow(
                """
                INSERT INTO status_history (disclosure_id, status)
                VALUES ($1, $2)
                RETURNING id, disclosure_id, status, changed_at
                """,
                disclosure["id"],
                disclosure["status"],
            )
            disclosure["status_history"] = [dict(history_row)]

    return UploadResponse(
        disclosure=DisclosureWithInventors(**disclosure),
        message="Disclosure created successfully",
    )


@router.patch("/{disclosure_id}", response_model=Disclosure)
async def update_disclosure(disclosure_id: UUID, update: DisclosureUpdate):
    """Update a disclosure's fields."""
    async with get_connection() as conn:
        # Check if exists and get current status
        existing = await conn.fetchrow(
            "SELECT id, status FROM disclosures WHERE id = $1", disclosure_id
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Disclosure not found")

        current_status = existing["status"]

        # Build update query dynamically
        updates = []
        values = []
        param_idx = 1
        status_changed = False

        if update.title is not None:
            updates.append(f"title = ${param_idx}")
            values.append(update.title)
            param_idx += 1

        if update.description is not None:
            updates.append(f"description = ${param_idx}")
            values.append(update.description)
            param_idx += 1

        if update.key_differences is not None:
            updates.append(f"key_differences = ${param_idx}")
            values.append(update.key_differences)
            param_idx += 1

        if update.status is not None:
            if update.status not in ("pending", "reviewed", "approved", "rejected"):
                raise HTTPException(status_code=400, detail="Invalid status value")
            updates.append(f"status = ${param_idx}")
            values.append(update.status)
            param_idx += 1
            if update.status != current_status:
                status_changed = True

        if update.review_notes is not None:
            updates.append(f"review_notes = ${param_idx}")
            values.append(update.review_notes)
            param_idx += 1

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        values.append(disclosure_id)

        query = f"""
            UPDATE disclosures
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            RETURNING id, docket_number, title, description, key_differences,
                      status, review_notes, original_filename, pdf_object_key, created_at, updated_at
        """

        row = await conn.fetchrow(query, *values)

        # Record status change in history if status was updated
        if status_changed:
            await conn.execute(
                """
                INSERT INTO status_history (disclosure_id, status)
                VALUES ($1, $2)
                """,
                disclosure_id,
                update.status,
            )

        return dict(row)


@router.delete("/{disclosure_id}")
async def delete_disclosure(disclosure_id: UUID):
    """Delete a disclosure and its inventors."""
    async with get_connection() as conn:
        # Get the pdf_object_key before deleting
        row = await conn.fetchrow(
            "SELECT pdf_object_key FROM disclosures WHERE id = $1", disclosure_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Disclosure not found")

        pdf_object_key = row["pdf_object_key"]

        # Delete from database
        await conn.execute("DELETE FROM disclosures WHERE id = $1", disclosure_id)

        # Delete PDF from MinIO if it exists
        if pdf_object_key:
            try:
                storage.delete_pdf(pdf_object_key)
            except Exception as e:
                logger.warning(f"Failed to delete PDF from storage: {e}")

    return {"message": "Disclosure deleted successfully"}


@router.get("/{disclosure_id}/pdf")
async def download_disclosure_pdf(disclosure_id: UUID):
    """Download the original PDF for a disclosure."""
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT original_filename, pdf_object_key FROM disclosures WHERE id = $1",
            disclosure_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Disclosure not found")

        if not row["pdf_object_key"]:
            raise HTTPException(status_code=404, detail="PDF not available for this disclosure")

        try:
            pdf_content = storage.download_pdf(row["pdf_object_key"])
        except Exception as e:
            logger.error(f"Failed to download PDF: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve PDF")

        filename = row["original_filename"] or "disclosure.pdf"

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
