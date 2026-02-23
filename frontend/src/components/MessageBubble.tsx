import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../types";
import { DebugPanel } from "./DebugPanel";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  if (message.role === "system") {
    return (
      <div className="flex justify-center my-2">
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg max-w-md">
          {message.content}
        </div>
      </div>
    );
  }

  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div className={`max-w-[80%] ${isUser ? "order-2" : "order-1"}`}>
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? "bg-relay-600 text-white rounded-br-md"
              : "bg-white text-gray-800 border border-gray-200 rounded-bl-md shadow-sm"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {message.content}
            </p>
          ) : (
            <div className="prose prose-chat max-w-none overflow-x-auto">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        <div
          className={`flex items-center gap-2 mt-1 ${isUser ? "justify-end" : "justify-start"}`}
        >
          <span className="text-xs text-gray-400">
            {message.timestamp.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          {message.metadata && (
            <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
              {message.metadata.language_detected.toUpperCase()}
            </span>
          )}
          {message.metadata &&
            message.metadata.latency_ms["total_ms"] !== undefined && (
              <span className="text-xs text-gray-400">
                {Math.round(message.metadata.latency_ms["total_ms"])}ms
              </span>
            )}
        </div>

        {message.metadata &&
          message.metadata.tools_used.length > 0 && (
            <DebugPanel metadata={message.metadata} />
          )}
      </div>
    </div>
  );
}
