import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { getDisclosure, updateDisclosure, deleteDisclosure, downloadDisclosurePDF } from "../api/disclosures";
import type { Disclosure, DisclosureUpdate } from "../types/disclosure";

type LoadingState =
  | { status: "loading" }
  | { status: "success"; disclosure: Disclosure }
  | { status: "error"; message: string };

const STATUS_OPTIONS: Disclosure["status"][] = [
  "pending",
  "reviewed",
  "approved",
  "rejected",
];

function StatusBadge({ status }: { status: Disclosure["status"] }) {
  const styles = {
    pending: "bg-yellow-100 text-yellow-800",
    reviewed: "bg-blue-100 text-blue-800",
    approved: "bg-green-100 text-green-800",
    rejected: "bg-red-100 text-red-800",
  };

  return (
    <span
      className={`px-3 py-1 text-sm font-medium rounded-full ${styles[status]}`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-6">
      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">
        {title}
      </h3>
      <div className="text-gray-900">{children}</div>
    </div>
  );
}

interface EditFormData {
  title: string;
  description: string;
  key_differences: string;
  status: Disclosure["status"];
  review_notes: string;
}

export function DisclosureDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [state, setState] = useState<LoadingState>({ status: "loading" });
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [formData, setFormData] = useState<EditFormData>({
    title: "",
    description: "",
    key_differences: "",
    status: "pending",
    review_notes: "",
  });

  useEffect(() => {
    if (!id) return;

    let cancelled = false;

    async function fetchDisclosure() {
      try {
        const disclosure = await getDisclosure(id!);
        if (!cancelled) {
          setState({ status: "success", disclosure });
          setFormData({
            title: disclosure.title,
            description: disclosure.description,
            key_differences: disclosure.key_differences,
            status: disclosure.status,
            review_notes: disclosure.review_notes || "",
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            status: "error",
            message:
              error instanceof Error ? error.message : "Failed to load disclosure",
          });
        }
      }
    }

    fetchDisclosure();

    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleSave = async () => {
    if (!id || state.status !== "success") return;

    setIsSaving(true);
    setSaveError(null);

    try {
      const update: DisclosureUpdate = {};

      // Only include changed fields
      if (formData.title !== state.disclosure.title) {
        update.title = formData.title;
      }
      if (formData.description !== state.disclosure.description) {
        update.description = formData.description;
      }
      if (formData.key_differences !== state.disclosure.key_differences) {
        update.key_differences = formData.key_differences;
      }
      if (formData.status !== state.disclosure.status) {
        update.status = formData.status;
      }
      if (formData.review_notes !== (state.disclosure.review_notes || "")) {
        update.review_notes = formData.review_notes;
      }

      // If nothing changed, just exit edit mode
      if (Object.keys(update).length === 0) {
        setIsEditing(false);
        return;
      }

      await updateDisclosure(id, update);
      // Refetch to get updated status_history
      const refreshed = await getDisclosure(id);
      setState({ status: "success", disclosure: refreshed });
      setIsEditing(false);
    } catch (error) {
      setSaveError(
        error instanceof Error ? error.message : "Failed to save changes"
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    if (state.status !== "success") return;

    // Reset form to current disclosure values
    setFormData({
      title: state.disclosure.title,
      description: state.disclosure.description,
      key_differences: state.disclosure.key_differences,
      status: state.disclosure.status,
      review_notes: state.disclosure.review_notes || "",
    });
    setIsEditing(false);
    setSaveError(null);
  };

  const handleDelete = async () => {
    if (!id || state.status !== "success") return;

    const confirmed = window.confirm(
      `Are you sure you want to delete "${state.disclosure.docket_number}"? This action cannot be undone.`
    );
    if (!confirmed) return;

    setDeleteError(null);

    try {
      await deleteDisclosure(id);
      navigate("/disclosures");
    } catch (error) {
      setDeleteError(
        error instanceof Error ? error.message : "Failed to delete disclosure"
      );
    }
  };

  if (state.status === "loading") {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-700 mb-4">{state.message}</p>
          <Link
            to="/disclosures"
            className="text-red-600 hover:text-red-700 underline"
          >
            Back to disclosures
          </Link>
        </div>
      </div>
    );
  }

  const { disclosure } = state;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <Link
          to="/disclosures"
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          &larr; Back to disclosures
        </Link>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-mono text-sm text-gray-500">
                {disclosure.docket_number}
              </span>
              {isEditing ? (
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) =>
                    setFormData({ ...formData, title: e.target.value })
                  }
                  className="block w-full text-xl font-semibold text-gray-900 mt-1 px-2 py-1 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                />
              ) : (
                <h1 className="text-xl font-semibold text-gray-900 mt-1">
                  {disclosure.title}
                </h1>
              )}
            </div>
            {isEditing ? (
              <select
                value={formData.status}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    status: e.target.value as Disclosure["status"],
                  })
                }
                className="px-3 py-1 text-sm font-medium rounded-md border border-gray-300 focus:ring-blue-500 focus:border-blue-500"
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </option>
                ))}
              </select>
            ) : (
              <StatusBadge status={disclosure.status} />
            )}
          </div>
        </div>

        <div className="px-6 py-6">
          {saveError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {saveError}
            </div>
          )}

          <Section title="Description">
            {isEditing ? (
              <textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            ) : (
              <p className="whitespace-pre-wrap">{disclosure.description}</p>
            )}
          </Section>

          <Section title="Key Differences">
            {isEditing ? (
              <textarea
                value={formData.key_differences}
                onChange={(e) =>
                  setFormData({ ...formData, key_differences: e.target.value })
                }
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            ) : (
              <p className="whitespace-pre-wrap">{disclosure.key_differences}</p>
            )}
          </Section>

          <Section title="Inventors">
            {disclosure.inventors.length === 0 ? (
              <p className="text-gray-500 italic">No inventors listed</p>
            ) : (
              <ul className="space-y-2">
                {disclosure.inventors.map((inventor) => (
                  <li
                    key={inventor.id}
                    className="flex items-center gap-2 text-gray-900"
                  >
                    <span className="font-medium">{inventor.name}</span>
                    {inventor.email && (
                      <a
                        href={`mailto:${inventor.email}`}
                        className="text-blue-600 hover:text-blue-700 text-sm"
                      >
                        {inventor.email}
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Review Notes">
            {isEditing ? (
              <textarea
                value={formData.review_notes}
                onChange={(e) =>
                  setFormData({ ...formData, review_notes: e.target.value })
                }
                rows={4}
                placeholder="Add notes about this disclosure for other reviewers..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            ) : disclosure.review_notes ? (
              <p className="whitespace-pre-wrap">{disclosure.review_notes}</p>
            ) : (
              <p className="text-gray-500 italic">No review notes</p>
            )}
          </Section>

          <Section title="Status History">
            {disclosure.status_history && disclosure.status_history.length > 0 ? (
              <ul className="space-y-2">
                {disclosure.status_history.map((entry) => (
                  <li
                    key={entry.id}
                    className="flex items-center gap-3 text-sm"
                  >
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        {
                          pending: "bg-yellow-100 text-yellow-800",
                          reviewed: "bg-blue-100 text-blue-800",
                          approved: "bg-green-100 text-green-800",
                          rejected: "bg-red-100 text-red-800",
                        }[entry.status]
                      }`}
                    >
                      {entry.status.charAt(0).toUpperCase() + entry.status.slice(1)}
                    </span>
                    <span className="text-gray-500">
                      {formatDateTime(entry.changed_at)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">No status history</p>
            )}
          </Section>

          <div className="grid grid-cols-2 gap-6 pt-4 border-t border-gray-200">
            {disclosure.original_filename && (
              <Section title="Original File">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm">
                    {disclosure.original_filename}
                  </span>
                  {disclosure.pdf_object_key ? (
                    <button
                      onClick={() => downloadDisclosurePDF(disclosure.id, disclosure.original_filename || undefined)}
                      className="text-sm text-blue-600 hover:text-blue-700 underline"
                    >
                      Download
                    </button>
                  ) : (
                    <span className="text-sm text-gray-400 italic">
                      PDF not available
                    </span>
                  )}
                </div>
              </Section>
            )}
            <Section title="Submitted">
              <span className="text-sm">
                {formatDateTime(disclosure.created_at)}
              </span>
            </Section>
          </div>

          {deleteError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {deleteError}
            </div>
          )}

          {/* Edit/Save/Delete buttons */}
          <div className="mt-6 pt-4 border-t border-gray-200 flex justify-between">
            {!isEditing && (
              <button
                onClick={handleDelete}
                className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-300 rounded-md hover:bg-red-50"
              >
                Delete
              </button>
            )}
            <div className="flex gap-3 ml-auto">
              {isEditing ? (
                <>
                  <button
                    onClick={handleCancel}
                    disabled={isSaving}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    {isSaving && (
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                    )}
                    Save Changes
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  Edit Disclosure
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
