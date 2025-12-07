import type { Disclosure, UploadResponse } from "../types/disclosure";

const API_BASE = "http://localhost:8000/api";

export async function uploadPDF(file: File): Promise<Disclosure> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/disclosures/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(error.detail || "Upload failed");
  }

  const data: UploadResponse = await response.json();
  return data.disclosure;
}

export async function getDisclosures(): Promise<Disclosure[]> {
  const response = await fetch(`${API_BASE}/disclosures`);

  if (!response.ok) {
    throw new Error("Failed to fetch disclosures");
  }

  return response.json();
}

export async function getDisclosure(id: string): Promise<Disclosure> {
  const response = await fetch(`${API_BASE}/disclosures/${id}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Disclosure not found");
    }
    throw new Error("Failed to fetch disclosure");
  }

  return response.json();
}
