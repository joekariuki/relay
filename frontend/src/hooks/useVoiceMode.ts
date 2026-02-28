import { useCallback, useRef, useState } from "react";
import type {
  VoiceModeState,
  VoiceModeTurnMetadata,
} from "../types";

const WS_URL = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws/voice`;

interface UseVoiceModeReturn {
  voiceModeState: VoiceModeState;
  partialTranscript: string;
  finalTranscript: string;
  agentText: string;
  statusMessage: string;
  turnMetadata: VoiceModeTurnMetadata | null;
  isConnected: boolean;
  startVoiceMode: (accountId: string, language: string, sessionId?: string) => void;
  endVoiceMode: () => void;
}

export function useVoiceMode(): UseVoiceModeReturn {
  const [voiceModeState, setVoiceModeState] = useState<VoiceModeState>("idle");
  const [partialTranscript, setPartialTranscript] = useState("");
  const [finalTranscript, setFinalTranscript] = useState("");
  const [agentText, setAgentText] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [turnMetadata, setTurnMetadata] = useState<VoiceModeTurnMetadata | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const playbackQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const playbackContextRef = useRef<AudioContext | null>(null);

  const cleanupAudio = useCallback(() => {
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    playbackQueueRef.current = [];
    isPlayingRef.current = false;
  }, []);

  const playNextChunk = useCallback(async () => {
    if (isPlayingRef.current || playbackQueueRef.current.length === 0) return;

    isPlayingRef.current = true;

    if (!playbackContextRef.current || playbackContextRef.current.state === "closed") {
      playbackContextRef.current = new AudioContext();
    }

    while (playbackQueueRef.current.length > 0) {
      const chunk = playbackQueueRef.current.shift();
      if (!chunk) break;

      try {
        const audioBuffer = await playbackContextRef.current.decodeAudioData(chunk.slice(0));
        await new Promise<void>((resolve) => {
          const source = playbackContextRef.current!.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(playbackContextRef.current!.destination);
          source.onended = () => resolve();
          source.start();
        });
      } catch {
        // Skip corrupted chunks
      }
    }

    isPlayingRef.current = false;
    setVoiceModeState("listening");
  }, []);

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string);

        switch (data.type) {
          case "session_started":
            setIsConnected(true);
            break;

          case "listening":
            setVoiceModeState("listening");
            setPartialTranscript("");
            setStatusMessage("");
            break;

          case "transcript_partial":
            setPartialTranscript(data.text || "");
            break;

          case "transcript_final":
            setFinalTranscript(data.text || "");
            setPartialTranscript("");
            setVoiceModeState("processing");
            break;

          case "agent_status":
            setStatusMessage(data.message || "");
            break;

          case "agent_text_delta":
            setAgentText((prev) => prev + (data.chunk || ""));
            break;

          case "audio_chunk": {
            setVoiceModeState("speaking");
            const binaryStr = atob(data.data);
            const bytes = new Uint8Array(binaryStr.length);
            for (let i = 0; i < binaryStr.length; i++) {
              bytes[i] = binaryStr.charCodeAt(i);
            }
            playbackQueueRef.current.push(bytes.buffer);
            playNextChunk();
            break;
          }

          case "turn_done":
            setTurnMetadata(data as VoiceModeTurnMetadata);
            if (playbackQueueRef.current.length === 0 && !isPlayingRef.current) {
              setVoiceModeState("listening");
            }
            break;

          case "error":
            setStatusMessage(data.message || "An error occurred");
            break;
        }
      } catch {
        // Ignore parse errors for binary frames
      }
    },
    [playNextChunk],
  );

  const startVoiceMode = useCallback(
    async (accountId: string, language: string, sessionId?: string) => {
      if (voiceModeState !== "idle") return;
      setVoiceModeState("connecting");

      setPartialTranscript("");
      setFinalTranscript("");
      setAgentText("");
      setStatusMessage("");
      setTurnMetadata(null);

      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          const startMsg: Record<string, string> = {
            type: "session_start",
            account_id: accountId,
            language,
          };
          if (sessionId) startMsg.session_id = sessionId;
          ws.send(JSON.stringify(startMsg));
        };

        ws.onmessage = handleMessage;

        ws.onerror = () => {
          setStatusMessage("Connection error");
          setVoiceModeState("idle");
          setIsConnected(false);
          cleanupAudio();
        };

        ws.onclose = () => {
          setVoiceModeState("idle");
          setIsConnected(false);
          cleanupAudio();
        };

        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: 48000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
          },
        });
        streamRef.current = stream;

        const audioCtx = new AudioContext({ sampleRate: 48000 });
        audioContextRef.current = audioCtx;

        const processorUrl = new URL(
          "../audio/pcm-capture-processor.ts",
          import.meta.url,
        ).href;
        await audioCtx.audioWorklet.addModule(processorUrl);

        const source = audioCtx.createMediaStreamSource(stream);
        const workletNode = new AudioWorkletNode(audioCtx, "pcm-capture-processor");
        workletNodeRef.current = workletNode;

        workletNode.port.onmessage = (e: MessageEvent) => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(e.data as ArrayBuffer);
          }
        };

        source.connect(workletNode);
        workletNode.connect(audioCtx.destination);
      } catch (err) {
        console.error("Failed to start voice mode:", err);
        setStatusMessage("Failed to access microphone");
        setVoiceModeState("idle");
        cleanupAudio();
      }
    },
    [voiceModeState, handleMessage, cleanupAudio],
  );

  const endVoiceMode = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "session_end" }));
      wsRef.current.close();
    }
    wsRef.current = null;
    cleanupAudio();
    setVoiceModeState("idle");
    setIsConnected(false);
    setPartialTranscript("");
    setFinalTranscript("");
    setAgentText("");
    setStatusMessage("");
  }, [cleanupAudio]);

  return {
    voiceModeState,
    partialTranscript,
    finalTranscript,
    agentText,
    statusMessage,
    turnMetadata,
    isConnected,
    startVoiceMode,
    endVoiceMode,
  };
}
