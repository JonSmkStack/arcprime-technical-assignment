export interface Inventor {
  id: string;
  name: string;
  email: string | null;
}

export interface StatusHistoryEntry {
  id: string;
  disclosure_id: string;
  status: "pending" | "reviewed" | "approved" | "rejected";
  changed_at: string;
}

export interface Disclosure {
  id: string;
  docket_number: string;
  title: string;
  description: string;
  key_differences: string;
  status: "pending" | "reviewed" | "approved" | "rejected";
  review_notes: string | null;
  original_filename: string | null;
  pdf_object_key: string | null;
  inventors: Inventor[];
  status_history: StatusHistoryEntry[];
  created_at: string;
  updated_at: string;
}

export interface DisclosureUpdate {
  title?: string;
  description?: string;
  key_differences?: string;
  status?: Disclosure["status"];
  review_notes?: string;
}

export interface UploadResponse {
  disclosure: Disclosure;
}

export interface ApiError {
  detail: string;
}
