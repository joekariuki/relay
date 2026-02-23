import type { RecordingState } from "../types";
import { WaveformCanvas } from "./WaveformCanvas";

interface Props {
  recordingState: RecordingState;
  isPlaying: boolean;
  playbackProgress: number;
  getAnalyserData: () => Uint8Array | null;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onStopAndSend: () => void;
  onPlay: () => void;
  onStopPlay: () => void;
  onDelete: () => void;
  onSend: () => void;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function RecordingPanel({
  recordingState,
  isPlaying,
  playbackProgress,
  getAnalyserData,
  onPause,
  onResume,
  onStop,
  onStopAndSend,
  onPlay,
  onStopPlay,
  onDelete,
  onSend,
}: Props) {
  if (recordingState.status === "processing") {
    return (
      <div className="flex items-center justify-center gap-3 py-1">
        <svg
          className="w-5 h-5 text-gray-400 animate-spin"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
        <span className="text-sm text-gray-500">Processing voice...</span>
      </div>
    );
  }

  if (recordingState.status === "recording") {
    return (
      <div className="flex items-center gap-3 bg-red-50 rounded-xl px-3 py-1">
        {/* Pause button */}
        <button
          type="button"
          onClick={onPause}
          className="w-10 h-10 rounded-full bg-relay-600 hover:bg-relay-700 flex items-center justify-center transition-colors flex-shrink-0"
          title="Pause recording"
        >
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="4" width="4" height="16" rx="1" />
            <rect x="14" y="4" width="4" height="16" rx="1" />
          </svg>
        </button>

        {/* Stop button */}
        <button
          type="button"
          onClick={onStop}
          className="w-10 h-10 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center transition-colors flex-shrink-0"
          title="Stop recording"
        >
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
        </button>

        {/* Live waveform + timer */}
        <WaveformCanvas getAnalyserData={getAnalyserData} isActive={true} />
        <span className="text-sm font-mono text-gray-600 flex-shrink-0">
          {formatTime(recordingState.elapsed)}
        </span>

        {/* Quick send button */}
        <button
          type="button"
          onClick={onStopAndSend}
          className="w-10 h-10 rounded-full bg-relay-600 hover:bg-relay-700 flex items-center justify-center transition-colors flex-shrink-0"
          title="Send voice message"
        >
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
    );
  }

  if (recordingState.status === "paused") {
    return (
      <div className="flex items-center gap-3 rounded-xl px-3 py-1">
        {/* Resume button */}
        <button
          type="button"
          onClick={onResume}
          className="w-10 h-10 rounded-full bg-relay-600 hover:bg-relay-700 flex items-center justify-center transition-colors flex-shrink-0"
          title="Resume recording"
        >
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        </button>

        {/* Stop button */}
        <button
          type="button"
          onClick={onStop}
          className="w-10 h-10 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center transition-colors flex-shrink-0"
          title="Stop recording"
        >
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
        </button>

        {/* Frozen waveform + blinking timer */}
        <div className="flex-1 min-w-0 flex items-center gap-2 opacity-60">
          <WaveformCanvas getAnalyserData={getAnalyserData} isActive={false} />
          <span className="text-sm font-mono text-gray-600 animate-pulse flex-shrink-0">
            {formatTime(recordingState.elapsed)}
          </span>
        </div>

        {/* Quick send button */}
        <button
          type="button"
          onClick={onStopAndSend}
          className="w-10 h-10 rounded-full bg-relay-600 hover:bg-relay-700 flex items-center justify-center transition-colors flex-shrink-0"
          title="Send voice message"
        >
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
    );
  }

  if (recordingState.status === "preview") {
    return (
      <div className="flex items-center gap-3 rounded-xl px-3 py-1">
        {/* Delete button */}
        <button
          type="button"
          onClick={onDelete}
          className="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors flex-shrink-0"
          title="Delete recording"
        >
          <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>

        {/* Play / Stop button */}
        <button
          type="button"
          onClick={isPlaying ? onStopPlay : onPlay}
          className="w-10 h-10 rounded-full bg-relay-100 hover:bg-relay-200 flex items-center justify-center transition-colors flex-shrink-0"
          title={isPlaying ? "Stop playback" : "Play recording"}
        >
          {isPlaying ? (
            <svg className="w-4 h-4 text-relay-700" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="4" width="4" height="16" rx="1" />
              <rect x="14" y="4" width="4" height="16" rx="1" />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-relay-700" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>

        {/* Static waveform with playback progress */}
        <WaveformCanvas
          isActive={false}
          frozenData={recordingState.waveformData}
          playbackProgress={playbackProgress}
        />

        {/* Duration */}
        <span className="text-sm font-mono text-gray-600 flex-shrink-0">
          {formatTime(recordingState.duration)}
        </span>

        {/* Send button */}
        <button
          type="button"
          onClick={onSend}
          className="w-10 h-10 rounded-full bg-relay-600 hover:bg-relay-700 flex items-center justify-center transition-colors flex-shrink-0"
          title="Send voice message"
        >
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
    );
  }

  return null;
}
