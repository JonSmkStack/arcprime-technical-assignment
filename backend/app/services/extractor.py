import json

from openai import AsyncOpenAI

from app.config import settings

EXTRACTION_PROMPT = """Analyze this document and extract patent disclosure information.
Return ONLY a valid JSON object with these fields:
- title: A concise title for the invention (string)
- description: What the invention is, explained in plain terms (string, 2-4 paragraphs)
- key_differences: What makes it different or novel compared to existing approaches (string, bullet points or paragraphs)
- inventors: Array of objects with "name" and "email" fields for each inventor/author mentioned

If you cannot find inventors/authors, return an empty array for inventors.
If you cannot determine a field, make your best inference from the document content.

Document text:
{document_text}

Return ONLY the JSON object, no other text or markdown formatting."""


async def extract_disclosure_info(document_text: str) -> dict:
    """Extract structured disclosure information from document text using AI.

    Args:
        document_text: The text content extracted from the PDF.

    Returns:
        A dictionary with title, description, key_differences, and inventors.

    Raises:
        ValueError: If extraction fails or returns invalid data.
    """
    if not settings.openai_api_key:
        raise ValueError(
            "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
        )

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Truncate very long documents to avoid token limits
    max_chars = 50000
    if len(document_text) > max_chars:
        document_text = document_text[:max_chars] + "\n\n[Document truncated...]"

    prompt = EXTRACTION_PROMPT.format(document_text=document_text)

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at analyzing technical documents and extracting structured information for patent disclosures. Always respond with valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=4000,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from AI model")

    # Clean up potential markdown formatting
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from AI: {str(e)}")

    # Validate required fields
    required = ["title", "description", "key_differences"]
    for field in required:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")

    # Ensure string fields are strings (AI sometimes returns lists)
    for field in ["title", "description", "key_differences"]:
        if isinstance(data[field], list):
            data[field] = "\n".join(f"• {item}" for item in data[field])

    # Ensure inventors is a list
    if "inventors" not in data:
        data["inventors"] = []
    elif not isinstance(data["inventors"], list):
        data["inventors"] = []

    return data
