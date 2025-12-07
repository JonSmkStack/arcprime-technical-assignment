import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getDisclosure } from "../api/disclosures";
import type { Disclosure } from "../types/disclosure";

type LoadingState =
  | { status: "loading" }
  | { status: "success"; disclosure: Disclosure }
  | { status: "error"; message: string };

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

export function DisclosureDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [state, setState] = useState<LoadingState>({ status: "loading" });

  useEffect(() => {
    if (!id) return;

    let cancelled = false;

    async function fetchDisclosure() {
      try {
        const disclosure = await getDisclosure(id!);
        if (!cancelled) {
          setState({ status: "success", disclosure });
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
              <h1 className="text-xl font-semibold text-gray-900 mt-1">
                {disclosure.title}
              </h1>
            </div>
            <StatusBadge status={disclosure.status} />
          </div>
        </div>

        <div className="px-6 py-6">
          <Section title="Description">
            <p className="whitespace-pre-wrap">{disclosure.description}</p>
          </Section>

          <Section title="Key Differences">
            <p className="whitespace-pre-wrap">{disclosure.key_differences}</p>
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

          <div className="grid grid-cols-2 gap-6 pt-4 border-t border-gray-200">
            {disclosure.original_filename && (
              <Section title="Original File">
                <span className="font-mono text-sm">
                  {disclosure.original_filename}
                </span>
              </Section>
            )}
            <Section title="Submitted">
              <span className="text-sm">
                {formatDateTime(disclosure.created_at)}
              </span>
            </Section>
          </div>
        </div>
      </div>
    </div>
  );
}
