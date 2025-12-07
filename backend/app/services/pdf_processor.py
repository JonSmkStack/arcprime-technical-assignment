import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text content from a PDF file.

    Args:
        pdf_bytes: The PDF file content as bytes.

    Returns:
        The extracted text from all pages.

    Raises:
        ValueError: If the PDF is invalid or cannot be read.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Invalid PDF file: {str(e)}")

    text_parts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            text_parts.append(text)

    doc.close()

    return "\n\n".join(text_parts)
