import { useCallback, useRef, useState } from "react";
import { streamChatMessage } from "../api";
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
  const [accountId, setAccountId] = useState("acc_001");
  const [language, setLanguage] = useState<Language>("auto");
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

      abortRef.current = streamChatMessage(content, accountId, langHint, {
        onTextDelta(chunk) {
          if (!assistantAdded) {
            assistantAdded = true;
            setIsLoading(false);
            setIsStreaming(true);
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
          const metadata: ResponseMetadata = {
            language_detected: payload.language_detected,
            tools_used: payload.tools_used,
            groundedness_score: payload.groundedness_score,
            latency_ms: payload.latency_ms,
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
          // Remove the empty assistant placeholder and add error message
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
      });
    },
    [accountId, language],
  );

  const clearMessages = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setMessages([]);
    setIsLoading(false);
    setIsStreaming(false);
  }, []);

  return {
    messages,
    isLoading,
    isStreaming,
    accountId,
    language,
    setAccountId,
    setLanguage,
    sendMessage,
    clearMessages,
  };
}
