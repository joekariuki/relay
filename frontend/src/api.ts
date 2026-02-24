import type {
  ChatApiResponse,
  StreamCallbacks,
  StreamDonePayload,
  VoiceApiResponse,
} from "./types";

const BASE_URL = "/api";

export async function sendChatMessage(
  message: string,
  accountId: string,
  language: string | null,
): Promise<ChatApiResponse> {
  const body: Record<string, unknown> = {
    message,
    account_id: accountId,
  };
  if (language) {
    body.language = language;
  }

  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Chat request failed (${res.status}): ${detail}`);
  }

  return res.json() as Promise<ChatApiResponse>;
}

export function streamChatMessage(
  message: string,
  accountId: string,
  language: string | null,
  callbacks: StreamCallbacks,
): AbortController {
  const controller = new AbortController();

  const body: Record<string, unknown> = {
    message,
    account_id: accountId,
  };
  if (language) {
    body.language = language;
  }

  (async () => {
    try {
      const res = await fetch(`${BASE_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!res.ok) {
        const detail = await res.text();
        callbacks.onError(`Chat request failed (${res.status}): ${detail}`);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        callbacks.onError("Response body is not readable");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events separated by double newlines
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          const trimmed = part.trim();
          if (!trimmed) continue;

          let eventType = "";
          let data = "";

          for (const line of trimmed.split("\n")) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7);
            } else if (line.startsWith("data: ")) {
              data = line.slice(6);
            }
          }

          if (!eventType || !data) continue;

          if (eventType === "text_delta") {
            const parsed = JSON.parse(data) as { chunk: string };
            callbacks.onTextDelta(parsed.chunk);
          } else if (eventType === "done") {
            const parsed = JSON.parse(data) as StreamDonePayload;
            callbacks.onDone(parsed);
          } else if (eventType === "error") {
            const parsed = JSON.parse(data) as { message: string };
            callbacks.onError(parsed.message);
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      callbacks.onError(
        err instanceof Error
          ? err.message
          : "An unexpected error occurred. Please try again.",
      );
    }
  })();

  return controller;
}

export async function sendVoiceMessage(
  audioBlob: Blob,
  accountId: string,
  enableTts: boolean,
): Promise<VoiceApiResponse> {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");
  formData.append("account_id", accountId);
  formData.append("enable_tts", String(enableTts));

  const res = await fetch(`${BASE_URL}/voice`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Voice request failed (${res.status}): ${detail}`);
  }

  return res.json() as Promise<VoiceApiResponse>;
}
