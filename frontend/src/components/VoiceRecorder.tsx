interface Props {
  onStart: () => void;
}

export function VoiceRecorder({ onStart }: Props) {
  return (
    <button
      type="button"
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
