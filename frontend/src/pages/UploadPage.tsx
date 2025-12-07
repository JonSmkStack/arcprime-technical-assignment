import { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { uploadPDF } from "../api/disclosures";
import type { Disclosure } from "../types/disclosure";

type UploadState =
  | { status: "idle" }
  | { status: "uploading" }
  | { status: "success"; disclosure: Disclosure }
  | { status: "error"; message: string };

export function UploadPage() {
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const [dragActive, setDragActive] = useState(false);

  const handleFile = useCallback(async (file: File) => {
    if (file.type !== "application/pdf") {
      setState({ status: "error", message: "Please upload a PDF file" });
      return;
    }

    setState({ status: "uploading" });

    try {
      const disclosure = await uploadPDF(file);
      setState({ status: "success", disclosure });
    } catch (error) {
      setState({
        status: "error",
        message: error instanceof Error ? error.message : "Upload failed",
      });
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const resetUpload = useCallback(() => {
    setState({ status: "idle" });
  }, []);

  if (state.status === "success") {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <div className="text-green-600 text-5xl mb-4">&#10003;</div>
          <h2 className="text-xl font-semibold text-green-800 mb-2">
            Disclosure Created Successfully
          </h2>
          <p className="text-green-700 mb-4">
            Docket Number:{" "}
            <span className="font-mono font-semibold">
              {state.disclosure.docket_number}
            </span>
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              to={`/disclosures/${state.disclosure.id}`}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              View Disclosure
            </Link>
            <button
              onClick={resetUpload}
              className="px-4 py-2 bg-white text-green-700 border border-green-300 rounded-md hover:bg-green-50 transition-colors"
            >
              Upload Another
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Submit Invention Disclosure
        </h1>
        <p className="text-gray-600">
          Upload a PDF document containing your invention details. We'll
          automatically extract the title, description, key differences, and
          inventor information.
        </p>
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          dragActive
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        } ${state.status === "uploading" ? "pointer-events-none opacity-60" : ""}`}
      >
        {state.status === "uploading" ? (
          <div>
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
            <p className="text-gray-600">Processing your document...</p>
            <p className="text-sm text-gray-500 mt-1">
              This may take a moment while we extract the information.
            </p>
          </div>
        ) : (
          <>
            <div className="text-gray-400 text-5xl mb-4">&#128196;</div>
            <p className="text-gray-700 mb-2">
              Drag and drop your PDF here, or{" "}
              <label className="text-blue-600 hover:text-blue-700 cursor-pointer underline">
                browse
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleInputChange}
                  className="hidden"
                />
              </label>
            </p>
            <p className="text-sm text-gray-500">PDF files only</p>
          </>
        )}
      </div>

      {state.status === "error" && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{state.message}</p>
          <button
            onClick={resetUpload}
            className="mt-2 text-sm text-red-600 hover:text-red-700 underline"
          >
            Try again
          </button>
        </div>
      )}
    </div>
  );
}
