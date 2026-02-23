interface Props {
  isRecording: boolean;
  isProcessing: boolean;
  onStart: () => void;
  onStop: () => void;
}

export function VoiceRecorder({
  isRecording,
  isProcessing,
  onStart,
  onStop,
}: Props) {
  if (isProcessing) {
    return (
      <button
        disabled
        className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center"
        title="Processing voice..."
      >
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
      </button>
    );
  }

  if (isRecording) {
    return (
      <button
        onClick={onStop}
        className="w-10 h-10 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center animate-pulse transition-colors"
        title="Stop recording"
      >
        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
          <rect x="6" y="6" width="12" height="12" rx="2" />
        </svg>
      </button>
    );
  }

  return (
    <button
      onClick={onStart}
      className="w-10 h-10 rounded-full bg-gray-100 hover:bg-relay-50 flex items-center justify-center transition-colors"
      title="Start voice recording"
    >
      <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
      </svg>
    </button>
  );
}
