export interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
  duration_ms: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  metadata?: ResponseMetadata;
}

export interface ResponseMetadata {
  language_detected: string;
  tools_used: ToolCall[];
  groundedness_score: number | null;
  latency_ms: Record<string, number>;
  session_id?: string;
}

export interface VoiceMetadata extends ResponseMetadata {
  transcript: string;
  audio_base64: string | null;
}

export interface Account {
  id: string;
  name: string;
  country: string;
}

export type Language = "auto" | "en" | "fr" | "sw";

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

export interface ChatApiResponse {
  response: string;
  language_detected: string;
  tools_used: ToolCall[];
  groundedness_score: number | null;
  latency_ms: Record<string, number>;
  metadata: Record<string, unknown>;
}

export interface VoiceApiResponse {
  response: string;
  transcript: string;
  language_detected: string;
  tools_used: ToolCall[];
  latency_ms: Record<string, number>;
  audio_base64: string | null;
}

export interface StreamDonePayload {
  language_detected: string;
  tools_used: ToolCall[];
  groundedness_score: number | null;
  latency_ms: Record<string, number>;
  session_id?: string;
}

export interface StreamCallbacks {
  onTextDelta: (chunk: string) => void;
  onDone: (payload: StreamDonePayload) => void;
  onError: (message: string) => void;
  onStatus?: (message: string) => void;
}

// --- Voice Mode Types ---

export type VoiceModeState =
  | "idle"
  | "connecting"
  | "listening"
  | "processing"
  | "speaking";

export interface VoiceModeMessage {
  type: string;
  [key: string]: unknown;
}

export interface VoiceModeTurnMetadata {
  session_id: string;
  language_detected: string;
  tools_used: ToolCall[];
  groundedness_score: number | null;
  latency_ms: Record<string, number>;
}

export interface VoiceModeTurn {
  userTranscript: string;
  agentResponse: string;
  metadata: VoiceModeTurnMetadata;
}
