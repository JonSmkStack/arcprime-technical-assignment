import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDisclosures } from "../api/disclosures";
import type { Disclosure } from "../types/disclosure";

type LoadingState =
  | { status: "loading" }
  | { status: "success"; disclosures: Disclosure[] }
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
      className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status]}`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function DisclosuresPage() {
  const [state, setState] = useState<LoadingState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function fetchDisclosures() {
      try {
        const disclosures = await getDisclosures();
        if (!cancelled) {
          setState({ status: "success", disclosures });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            status: "error",
            message:
              error instanceof Error ? error.message : "Failed to load disclosures",
          });
        }
      }
    }

    fetchDisclosures();

    return () => {
      cancelled = true;
    };
  }, []);

  if (state.status === "loading") {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-700">{state.message}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 text-sm text-red-600 hover:text-red-700 underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (state.disclosures.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-5xl mb-4">&#128450;</div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">
          No Disclosures Yet
        </h2>
        <p className="text-gray-500 mb-6">
          Invention disclosures submitted by inventors will appear here.
        </p>
        <Link
          to="/"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Submit First Disclosure
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Disclosures</h1>
        <span className="text-sm text-gray-500">
          {state.disclosures.length} total
        </span>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Docket #
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Title
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {state.disclosures.map((disclosure) => (
              <tr key={disclosure.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="font-mono text-sm text-gray-900">
                    {disclosure.docket_number}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 line-clamp-1">
                    {disclosure.title}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge status={disclosure.status} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(disclosure.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <Link
                    to={`/disclosures/${disclosure.id}`}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
