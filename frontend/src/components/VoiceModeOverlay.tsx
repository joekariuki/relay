import { PhoneOff } from "lucide-react";
import { useState } from "react";
import type { VoiceModeState, VoiceModeTurnMetadata } from "../types";

interface Props {
  voiceModeState: VoiceModeState;
  partialTranscript: string;
  finalTranscript: string;
  agentText: string;
  statusMessage: string;
  turnMetadata: VoiceModeTurnMetadata | null;
  onEnd: () => void;
}

const STATE_LABELS: Record<VoiceModeState, string> = {
  idle: "",
  connecting: "Connecting...",
  listening: "Listening...",
  processing: "Thinking...",
  speaking: "Speaking...",
};

export function VoiceModeOverlay({
  voiceModeState,
  partialTranscript,
  finalTranscript,
  agentText,
  statusMessage,
  turnMetadata,
  onEnd,
}: Props) {
  const [showLatency, setShowLatency] = useState(false);

  const isListening = voiceModeState === "listening";
  const isProcessing = voiceModeState === "processing";
  const isSpeaking = voiceModeState === "speaking";

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center">
      <div className="bg-gray-900 rounded-3xl w-full max-w-md mx-4 p-8 flex flex-col items-center gap-6 text-white">
        {/* Animated orb */}
        <div className="relative flex items-center justify-center w-32 h-32">
          <div
            className={`absolute inset-0 rounded-full transition-all duration-500 ${
              isListening
                ? "bg-relay-500/30 animate-pulse scale-110"
                : isSpeaking
                  ? "bg-green-500/30 animate-ping"
                  : isProcessing
                    ? "bg-amber-500/20 animate-spin-slow"
                    : "bg-gray-700/30"
            }`}
          />
          <div
            className={`relative w-20 h-20 rounded-full transition-all duration-300 ${
              isListening
                ? "bg-relay-500 shadow-lg shadow-relay-500/40"
                : isSpeaking
                  ? "bg-green-500 shadow-lg shadow-green-500/40"
                  : isProcessing
                    ? "bg-amber-500 shadow-lg shadow-amber-500/40"
                    : "bg-gray-600"
            }`}
          />
        </div>

        {/* State label */}
        <p className="text-sm font-medium text-gray-400 uppercase tracking-wider">
          {STATE_LABELS[voiceModeState]}
        </p>

        {/* Transcript area */}
        <div className="w-full min-h-[120px] flex flex-col gap-3">
          {/* Partial transcript (live) */}
          {partialTranscript && (
            <p className="text-gray-400 text-sm italic text-center animate-pulse">
              {partialTranscript}
            </p>
          )}

          {/* Final transcript */}
          {finalTranscript && (
            <div className="bg-gray-800 rounded-xl px-4 py-3">
              <p className="text-xs text-gray-500 mb-1">You said:</p>
              <p className="text-white text-sm">{finalTranscript}</p>
            </div>
          )}

          {/* Status message (tool execution) */}
          {statusMessage && voiceModeState === "processing" && (
            <div className="flex items-center gap-2 justify-center">
              <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
              <p className="text-amber-400 text-xs">{statusMessage}</p>
            </div>
          )}

          {/* Agent response */}
          {agentText && (
            <div className="bg-relay-900/50 border border-relay-700/30 rounded-xl px-4 py-3">
              <p className="text-xs text-relay-400 mb-1">Agent:</p>
              <p className="text-white text-sm leading-relaxed">{agentText}</p>
            </div>
          )}
        </div>

        {/* Latency breakdown */}
        {turnMetadata && (
          <div className="w-full">
            <button
              onClick={() => setShowLatency(!showLatency)}
              className="text-xs text-gray-500 hover:text-gray-400 flex items-center gap-1 mx-auto"
            >
              <span className={`transform transition-transform ${showLatency ? "rotate-90" : ""}`}>
                &#9654;
              </span>
              Latency details
            </button>
            {showLatency && (
              <div className="mt-2 bg-gray-800/50 rounded-lg p-3 text-xs text-gray-400 grid grid-cols-2 gap-2">
                {Object.entries(turnMetadata.latency_ms).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-2">
                    <span className="text-gray-500">{key.replace(/_ms$/, "").replace(/_/g, " ")}:</span>
                    <span className="text-gray-300 font-mono">{Math.round(value)}ms</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* End button */}
        <button
          onClick={onEnd}
          className="mt-2 flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-full transition-colors font-medium"
        >
          <PhoneOff size={18} />
          End Voice Mode
        </button>
      </div>
    </div>
  );
}
