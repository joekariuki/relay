import { useCallback, useRef, useState } from "react";
import { deleteSession, streamChatMessage } from "../api";
import type { ChatMessage, Language, ResponseMetadata } from "../types";

let messageCounter = 0;
function nextId(): string {
  messageCounter += 1;
  return `msg_${messageCounter}_${Date.now()}`;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [accountId, setAccountId] = useState("acc_001");
  const [language, setLanguage] = useState<Language>("auto");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    (content: string) => {
      const userMsg: ChatMessage = {
        id: nextId(),
        role: "user",
        content,
        timestamp: new Date(),
      };

      const assistantId = nextId();
      let assistantAdded = false;

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      const langHint = language === "auto" ? null : language;

      abortRef.current = streamChatMessage(
        content,
        accountId,
        langHint,
        {
          onStatus(message) {
            setStatusMessage(message);
          },
          onTextDelta(chunk) {
            if (!assistantAdded) {
              assistantAdded = true;
              setIsLoading(false);
              setIsStreaming(true);
              setStatusMessage("");
              setMessages((prev) => [
                ...prev,
                {
                  id: assistantId,
                  role: "assistant" as const,
                  content: chunk,
                  timestamp: new Date(),
                },
              ]);
            } else {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantId
                    ? { ...msg, content: msg.content + chunk }
                    : msg,
                ),
              );
            }
          },
          onDone(payload) {
            setIsStreaming(false);
            setStatusMessage("");
            if (payload.session_id) {
              setSessionId(payload.session_id);
            }
            const metadata: ResponseMetadata = {
              language_detected: payload.language_detected,
              tools_used: payload.tools_used,
              groundedness_score: payload.groundedness_score,
              latency_ms: payload.latency_ms,
              session_id: payload.session_id,
            };
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantId ? { ...msg, metadata } : msg,
              ),
            );
          },
          onError(message) {
            setIsLoading(false);
            setIsStreaming(false);
            setStatusMessage("");
            setMessages((prev) => {
              const filtered = prev.filter((msg) => msg.id !== assistantId);
              return [
                ...filtered,
                {
                  id: nextId(),
                  role: "system" as const,
                  content: message,
                  timestamp: new Date(),
                },
              ];
            });
          },
        },
        sessionId,
      );
    },
    [accountId, language, sessionId],
  );

  const clearMessages = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    if (sessionId) {
      void deleteSession(sessionId);
    }
    setMessages([]);
    setSessionId(null);
    setIsLoading(false);
    setIsStreaming(false);
    setStatusMessage("");
  }, [sessionId]);

  return {
    messages,
    isLoading,
    isStreaming,
    statusMessage,
    accountId,
    language,
    sessionId,
    setAccountId,
    setLanguage,
    sendMessage,
    clearMessages,
  };
}
