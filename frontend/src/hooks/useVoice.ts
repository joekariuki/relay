import { useCallback, useRef, useState } from "react";
import { sendVoiceMessage } from "../api";
import type { ChatMessage, VoiceMetadata } from "../types";

// ---------------------------------------------------------------------------
// State machine
// ---------------------------------------------------------------------------

export type RecordingState =
  | { status: "idle" }
  | { status: "recording"; elapsed: number }
  | { status: "paused"; elapsed: number }
  | {
      status: "preview";
      blob: Blob;
      duration: number;
      objectUrl: string;
      waveformData: number[];
    }
  | { status: "processing" };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

let voiceMsgCounter = 0;
function nextId(): string {
  voiceMsgCounter += 1;
  return `voice_${voiceMsgCounter}_${Date.now()}`;
}

function downsample(data: number[], count: number): number[] {
  if (data.length === 0) return Array.from({ length: count }, () => 0);
  if (data.length <= count) return data;
  const bucketSize = data.length / count;
  const result: number[] = [];
  for (let i = 0; i < count; i++) {
    const start = Math.floor(i * bucketSize);
    const end = Math.floor((i + 1) * bucketSize);
    let sum = 0;
    for (let j = start; j < end; j++) {
      sum += data[j] ?? 0;
    }
    result.push(sum / (end - start));
  }
  return result;
}

function playTtsAudio(base64: string): void {
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

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useVoice(
  accountId: string,
  onMessages: (userMsg: ChatMessage, assistantMsg: ChatMessage) => void,
  onError: (errorMsg: ChatMessage) => void,
) {
  const [recordingState, setRecordingState] = useState<RecordingState>({
    status: "idle",
  });
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackProgress, setPlaybackProgress] = useState(0);

  // Recording infrastructure
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const mimeTypeRef = useRef("audio/webm");

  // Web Audio API for waveform analysis
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  // Timer
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const elapsedRef = useRef(0);
  const timerStartRef = useRef(0);

  // Waveform history: one amplitude sample per ~100ms tick
  const waveformHistoryRef = useRef<number[]>([]);

  // Playback
  const previewAudioRef = useRef<HTMLAudioElement | null>(null);

  // ---- internal helpers ----

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const releaseResources = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;

    if (audioContextRef.current?.state !== "closed") {
      audioContextRef.current?.close().catch(() => {});
    }
    audioContextRef.current = null;
    analyserRef.current = null;

    mediaRecorderRef.current = null;
    chunksRef.current = [];
  }, []);

  const sampleWaveform = useCallback(() => {
    if (!analyserRef.current) return;
    const buf = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteTimeDomainData(buf);
    let sum = 0;
    for (let i = 0; i < buf.length; i++) {
      sum += Math.abs((buf[i] ?? 128) - 128);
    }
    waveformHistoryRef.current.push(sum / buf.length / 128);
  }, []);

  const startTimerInterval = useCallback(() => {
    timerRef.current = setInterval(() => {
      const elapsed = (Date.now() - timerStartRef.current) / 1000;
      elapsedRef.current = elapsed;
      setRecordingState({ status: "recording", elapsed });
      sampleWaveform();
    }, 100);
  }, [sampleWaveform]);

  // ---- public API ----

  const getAnalyserData = useCallback((): Uint8Array | null => {
    const analyser = analyserRef.current;
    if (!analyser) return null;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteTimeDomainData(data);
    return data;
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Set up Web Audio analyser for waveform
      const audioCtx = new AudioContext();
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);
      // Do NOT connect to destination — no feedback loop

      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;

      // Set up MediaRecorder
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      mimeTypeRef.current = mimeType;

      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];
      waveformHistoryRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start(250);

      // Start elapsed timer
      elapsedRef.current = 0;
      timerStartRef.current = Date.now();
      startTimerInterval();

      setRecordingState({ status: "recording", elapsed: 0 });
    } catch {
      onError({
        id: nextId(),
        role: "system",
        content:
          "Microphone access denied. Please allow microphone access to use voice mode.",
        timestamp: new Date(),
      });
    }
  }, [onError, startTimerInterval]);

  const pauseRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== "recording") return;

    if (typeof recorder.pause === "function") {
      recorder.pause();
    }

    clearTimer();
    const elapsed = elapsedRef.current;
    setRecordingState({ status: "paused", elapsed });
  }, [clearTimer]);

  const resumeRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== "paused") return;

    recorder.resume();

    // Restart timer from where we left off
    timerStartRef.current = Date.now() - elapsedRef.current * 1000;
    startTimerInterval();

    setRecordingState({ status: "recording", elapsed: elapsedRef.current });
  }, [startTimerInterval]);

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") return;

    clearTimer();
    const duration = elapsedRef.current;
    const waveformData = downsample(waveformHistoryRef.current, 50);

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeTypeRef.current });
      releaseResources();

      if (blob.size === 0) {
        setRecordingState({ status: "idle" });
        return;
      }

      const objectUrl = URL.createObjectURL(blob);
      setRecordingState({
        status: "preview",
        blob,
        duration,
        objectUrl,
        waveformData,
      });
    };

    recorder.stop();
  }, [clearTimer, releaseResources]);

  const deleteRecording = useCallback(() => {
    if (previewAudioRef.current) {
      previewAudioRef.current.pause();
      previewAudioRef.current = null;
    }
    setIsPlaying(false);
    setPlaybackProgress(0);

    if (recordingState.status === "preview") {
      URL.revokeObjectURL(recordingState.objectUrl);
    }

    clearTimer();
    releaseResources();
    setRecordingState({ status: "idle" });
  }, [recordingState, clearTimer, releaseResources]);

  const playPreview = useCallback(() => {
    if (recordingState.status !== "preview") return;

    const audio = new Audio(recordingState.objectUrl);
    previewAudioRef.current = audio;

    audio.ontimeupdate = () => {
      if (audio.duration && isFinite(audio.duration)) {
        setPlaybackProgress(audio.currentTime / audio.duration);
      }
    };

    audio.onended = () => {
      setIsPlaying(false);
      setPlaybackProgress(0);
      previewAudioRef.current = null;
    };

    audio.play().catch(() => {});
    setIsPlaying(true);
  }, [recordingState]);

  const stopPreview = useCallback(() => {
    if (previewAudioRef.current) {
      previewAudioRef.current.pause();
      previewAudioRef.current.currentTime = 0;
      previewAudioRef.current = null;
    }
    setIsPlaying(false);
    setPlaybackProgress(0);
  }, []);

  const sendRecording = useCallback(async () => {
    if (recordingState.status !== "preview") return;

    const { blob, objectUrl } = recordingState;

    if (previewAudioRef.current) {
      previewAudioRef.current.pause();
      previewAudioRef.current = null;
    }
    setIsPlaying(false);
    setPlaybackProgress(0);

    URL.revokeObjectURL(objectUrl);
    setRecordingState({ status: "processing" });

    try {
      const result = await sendVoiceMessage(blob, accountId, true);

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

      if (result.audio_base64) {
        playTtsAudio(result.audio_base64);
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
      setRecordingState({ status: "idle" });
    }
  }, [recordingState, accountId, onMessages, onError]);

  // ---- backward-compatible derived state ----
  const isRecording =
    recordingState.status === "recording" ||
    recordingState.status === "paused";
  const isProcessing = recordingState.status === "processing";

  return {
    // Legacy API (used by current App.tsx and VoiceRecorder.tsx)
    isRecording,
    isProcessing,
    startRecording,
    stopRecording,

    // New API
    recordingState,
    isPlaying,
    playbackProgress,
    getAnalyserData,
    pauseRecording,
    resumeRecording,
    deleteRecording,
    playPreview,
    stopPreview,
    sendRecording,
  };
}
