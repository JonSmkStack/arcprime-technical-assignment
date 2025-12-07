import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { getDisclosures, exportDisclosuresCSV, type SearchParams } from "../api/disclosures";
import type { Disclosure } from "../types/disclosure";

type LoadingState =
  | { status: "loading" }
  | { status: "success"; disclosures: Disclosure[] }
  | { status: "error"; message: string };

const STATUS_OPTIONS: Array<{ value: Disclosure["status"] | ""; label: string }> = [
  { value: "", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "reviewed", label: "Reviewed" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
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
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<Disclosure["status"] | "">("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [isExporting, setIsExporting] = useState(false);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const fetchDisclosures = useCallback(async () => {
    setState({ status: "loading" });

    try {
      const params: SearchParams = {};
      if (debouncedSearch) {
        params.search = debouncedSearch;
      }
      if (statusFilter) {
        params.status = statusFilter;
      }

      const disclosures = await getDisclosures(params);
      setState({ status: "success", disclosures });
    } catch (error) {
      setState({
        status: "error",
        message:
          error instanceof Error ? error.message : "Failed to load disclosures",
      });
    }
  }, [debouncedSearch, statusFilter]);

  useEffect(() => {
    fetchDisclosures();
  }, [fetchDisclosures]);

  const handleClearFilters = () => {
    setSearch("");
    setStatusFilter("");
  };

  const handleExportCSV = async () => {
    setIsExporting(true);
    try {
      const params: SearchParams = {};
      if (debouncedSearch) {
        params.search = debouncedSearch;
      }
      if (statusFilter) {
        params.status = statusFilter;
      }
      await exportDisclosuresCSV(params);
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setIsExporting(false);
    }
  };

  const hasFilters = search || statusFilter;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Disclosures</h1>
        <div className="flex items-center gap-4">
          {state.status === "success" && state.disclosures.length > 0 && (
            <button
              onClick={handleExportCSV}
              disabled={isExporting}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 flex items-center gap-2"
            >
              {isExporting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-500 border-t-transparent"></div>
                  Exporting...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export CSV
                </>
              )}
            </button>
          )}
          {state.status === "success" && (
            <span className="text-sm text-gray-500">
              {state.disclosures.length} {state.disclosures.length === 1 ? "result" : "results"}
            </span>
          )}
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title, description, or docket number..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>
        <div className="flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as Disclosure["status"] | "")}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {hasFilters && (
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {state.status === "loading" && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
        </div>
      )}

      {state.status === "error" && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-700">{state.message}</p>
          <button
            onClick={fetchDisclosures}
            className="mt-4 text-sm text-red-600 hover:text-red-700 underline"
          >
            Try again
          </button>
        </div>
      )}

      {state.status === "success" && state.disclosures.length === 0 && (
        <div className="text-center py-12">
          {hasFilters ? (
            <>
              <div className="text-gray-400 text-5xl mb-4">&#128269;</div>
              <h2 className="text-xl font-semibold text-gray-700 mb-2">
                No Results Found
              </h2>
              <p className="text-gray-500 mb-6">
                Try adjusting your search or filter to find what you're looking for.
              </p>
              <button
                onClick={handleClearFilters}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Clear Filters
              </button>
            </>
          ) : (
            <>
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
            </>
          )}
        </div>
      )}

      {state.status === "success" && state.disclosures.length > 0 && (
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
      )}
    </div>
  );
}
