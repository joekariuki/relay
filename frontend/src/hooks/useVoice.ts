import { useCallback, useRef, useState } from "react";
import { sendVoiceMessage } from "../api";
import type { ChatMessage, VoiceMetadata } from "../types";

let voiceMsgCounter = 0;
function nextId(): string {
  voiceMsgCounter += 1;
  return `voice_${voiceMsgCounter}_${Date.now()}`;
}

export function useVoice(
  accountId: string,
  onMessages: (userMsg: ChatMessage, assistantMsg: ChatMessage) => void,
  onError: (errorMsg: ChatMessage) => void,
) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Prefer opus codec for compression
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        // Stop all tracks to release microphone
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(chunksRef.current, { type: mimeType });
        if (audioBlob.size === 0) return;

        setIsProcessing(true);
        try {
          const result = await sendVoiceMessage(audioBlob, accountId, true);

          const userMsg: ChatMessage = {
            id: nextId(),
            role: "user",
            content: result.transcript || "(no speech detected)",
            timestamp: new Date(),
          };

          const metadata: VoiceMetadata = {
            transcript: result.transcript,
            language_detected: result.language_detected,
            tools_used: result.tools_used,
            groundedness_score: null,
            latency_ms: result.latency_ms,
            audio_base64: result.audio_base64,
          };

          const assistantMsg: ChatMessage = {
            id: nextId(),
            role: "assistant",
            content: result.response,
            timestamp: new Date(),
            metadata,
          };

          onMessages(userMsg, assistantMsg);

          // Play TTS audio if available
          if (result.audio_base64) {
            playAudio(result.audio_base64);
          }
        } catch (err) {
          onError({
            id: nextId(),
            role: "system",
            content:
              err instanceof Error
                ? err.message
                : "Voice processing failed. Please try again.",
            timestamp: new Date(),
          });
        } finally {
          setIsProcessing(false);
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
    } catch {
      onError({
        id: nextId(),
        role: "system",
        content:
          "Microphone access denied. Please allow microphone access to use voice mode.",
        timestamp: new Date(),
      });
    }
  }, [accountId, onMessages, onError]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  return {
    isRecording,
    isProcessing,
    startRecording,
    stopRecording,
  };
}

function playAudio(base64: string): void {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  const blob = new Blob([bytes], { type: "audio/mp3" });
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play().catch(() => {
    // Browser may block autoplay — silently ignore
  });
  audio.onended = () => URL.revokeObjectURL(url);
}
