import type { ChatApiResponse, VoiceApiResponse } from "./types";

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
