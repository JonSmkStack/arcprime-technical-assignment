import type { Disclosure, DisclosureUpdate, UploadResponse } from "../types/disclosure";

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

export interface SearchParams {
  search?: string;
  status?: Disclosure["status"] | "";
}

export async function getDisclosures(params?: SearchParams): Promise<Disclosure[]> {
  const searchParams = new URLSearchParams();
  if (params?.search) {
    searchParams.set("search", params.search);
  }
  if (params?.status) {
    searchParams.set("status", params.status);
  }

  const queryString = searchParams.toString();
  const url = queryString
    ? `${API_BASE}/disclosures?${queryString}`
    : `${API_BASE}/disclosures`;

  const response = await fetch(url);

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

export async function updateDisclosure(
  id: string,
  update: DisclosureUpdate
): Promise<Disclosure> {
  const response = await fetch(`${API_BASE}/disclosures/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Disclosure not found");
    }
    const error = await response.json().catch(() => ({ detail: "Update failed" }));
    throw new Error(error.detail || "Update failed");
  }

  return response.json();
}
