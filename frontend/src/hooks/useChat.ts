import { useCallback, useState } from "react";
import { sendChatMessage } from "../api";
import type { ChatMessage, Language, ResponseMetadata } from "../types";

let messageCounter = 0;
function nextId(): string {
  messageCounter += 1;
  return `msg_${messageCounter}_${Date.now()}`;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [accountId, setAccountId] = useState("acc_001");
  const [language, setLanguage] = useState<Language>("auto");

  const sendMessage = useCallback(
    async (content: string) => {
      const userMsg: ChatMessage = {
        id: nextId(),
        role: "user",
        content,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const langHint = language === "auto" ? null : language;
        const result = await sendChatMessage(content, accountId, langHint);

        const metadata: ResponseMetadata = {
          language_detected: result.language_detected,
          tools_used: result.tools_used,
          groundedness_score: result.groundedness_score,
          latency_ms: result.latency_ms,
        };

        const assistantMsg: ChatMessage = {
          id: nextId(),
          role: "assistant",
          content: result.response,
          timestamp: new Date(),
          metadata,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        const errorMsg: ChatMessage = {
          id: nextId(),
          role: "system",
          content:
            err instanceof Error
              ? err.message
              : "An unexpected error occurred. Please try again.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [accountId, language],
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    accountId,
    language,
    setAccountId,
    setLanguage,
    sendMessage,
    clearMessages,
  };
}
