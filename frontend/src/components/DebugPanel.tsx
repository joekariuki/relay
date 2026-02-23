import { useState } from "react";
import type { ResponseMetadata } from "../types";

interface Props {
  metadata: ResponseMetadata;
}

export function DebugPanel({ metadata }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="mt-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-xs text-relay-600 hover:text-relay-700 flex items-center gap-1"
      >
        <span className={`transform transition-transform ${isOpen ? "rotate-90" : ""}`}>
          &#9654;
        </span>
        {metadata.tools_used.length} tool call{metadata.tools_used.length !== 1 ? "s" : ""}
      </button>

      {isOpen && (
        <div className="mt-2 bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs space-y-3">
          {/* Tool calls */}
          <div>
            <h4 className="font-semibold text-gray-700 mb-1">Tool Calls</h4>
            {metadata.tools_used.map((tool, i) => (
              <div key={i} className="bg-white border border-gray-100 rounded p-2 mb-1.5">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono font-medium text-relay-700">
                    {tool.tool_name}
                  </span>
                  <span className="text-gray-400">
                    {Math.round(tool.duration_ms)}ms
                  </span>
                </div>
                <div className="text-gray-500">
                  <span className="text-gray-400">args: </span>
                  {JSON.stringify(tool.arguments)}
                </div>
                <div className="text-gray-500 mt-0.5">
                  <span className="text-gray-400">result: </span>
                  <span className="break-all">
                    {JSON.stringify(tool.result).slice(0, 200)}
                    {JSON.stringify(tool.result).length > 200 ? "..." : ""}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Latency breakdown */}
          <div>
            <h4 className="font-semibold text-gray-700 mb-1">Latency</h4>
            <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
              {Object.entries(metadata.latency_ms).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-500">{key}:</span>
                  <span className="font-mono text-gray-700">
                    {Math.round(value)}ms
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Groundedness */}
          {metadata.groundedness_score !== null && (
            <div>
              <h4 className="font-semibold text-gray-700 mb-1">Groundedness</h4>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-relay-500 rounded-full h-2 transition-all"
                    style={{ width: `${metadata.groundedness_score * 100}%` }}
                  />
                </div>
                <span className="font-mono text-gray-700">
                  {(metadata.groundedness_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
