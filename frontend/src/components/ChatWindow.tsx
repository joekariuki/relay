import { useEffect, useRef } from "react";
import type { ChatMessage, Language } from "../types";
import { MessageBubble } from "./MessageBubble";

const FALLBACK_STATUS: Record<string, string> = {
  en: "Processing...",
  fr: "Traitement en cours...",
  sw: "Inashughulikiwa...",
};

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  statusMessage: string;
  language: Language;
}

export function ChatWindow({ messages, isLoading, isStreaming, statusMessage, language }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, isStreaming]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isLoading && (
        <div className="flex justify-start mb-3">
          <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
            <div className="flex items-center gap-2">
              <svg
                className="h-4 w-4 animate-spin text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span className="text-sm text-gray-500">
                {statusMessage || FALLBACK_STATUS[language] || FALLBACK_STATUS.en}
              </span>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
