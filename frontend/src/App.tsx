import { Phone } from "lucide-react";
import { useCallback, useState } from "react";
import { AccountSelector } from "./components/AccountSelector";
import { ChatWindow } from "./components/ChatWindow";
import { LanguageSelector } from "./components/LanguageSelector";
import { RecordingPanel } from "./components/RecordingPanel";
import { SampleQueries } from "./components/SampleQueries";
import { VoiceModeOverlay } from "./components/VoiceModeOverlay";
import { VoiceRecorder } from "./components/VoiceRecorder";
import { useChat } from "./hooks/useChat";
import { useVoice } from "./hooks/useVoice";
import { useVoiceMode } from "./hooks/useVoiceMode";
import type { ChatMessage } from "./types";

function App() {
  const {
    messages,
    isLoading,
    isStreaming,
    statusMessage,
    accountId,
    language,
    sessionId,
    setAccountId,
    setLanguage,
    sendMessage,
    clearMessages,
  } = useChat();

  const [input, setInput] = useState("");

  const handleAccountChange = useCallback(
    (newAccountId: string) => {
      if (newAccountId !== accountId) {
        clearMessages();
        setVoiceMessages([]);
      }
      setAccountId(newAccountId);
    },
    [accountId, clearMessages, setAccountId],
  );

  const handleVoiceMessages = useCallback(
    (userMsg: ChatMessage, assistantMsg: ChatMessage) => {
      setVoiceMessages((prev) => [...prev, userMsg, assistantMsg]);
    },
    [],
  );

  const handleVoiceError = useCallback((errorMsg: ChatMessage) => {
    setVoiceMessages((prev) => [...prev, errorMsg]);
  }, []);

  const [voiceMessages, setVoiceMessages] = useState<ChatMessage[]>([]);

  const {
    recordingState,
    isPlaying,
    playbackProgress,
    getAnalyserData,
    startRecording,
    pauseRecording,
    resumeRecording,
    stopRecording,
    deleteRecording,
    playPreview,
    stopPreview,
    sendRecording,
    stopAndSend,
  } = useVoice(accountId, handleVoiceMessages, handleVoiceError);

  const {
    voiceModeState,
    partialTranscript,
    finalTranscript,
    agentText,
    statusMessage: voiceModeStatus,
    turnMetadata,
    startVoiceMode,
    endVoiceMode,
  } = useVoiceMode();

  const isVoiceModeActive = voiceModeState !== "idle";

  const isActive = recordingState.status !== "idle";
  const isProcessing = recordingState.status === "processing";

  const allMessages = [...messages, ...voiceMessages].sort(
    (a, b) => a.timestamp.getTime() - b.timestamp.getTime(),
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading || isStreaming) return;
    setInput("");
    void sendMessage(trimmed);
  };

  const handleSampleQuery = (query: string) => {
    void sendMessage(query);
  };

  const handleClear = () => {
    clearMessages();
    setVoiceMessages([]);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-relay-700 text-white px-4 py-3 shadow-lg">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold tracking-wide">RELAY</h1>
            <p className="text-relay-200 text-xs">
              Mobile Money Support Agent
            </p>
          </div>
          <div className="flex items-center gap-3">
            <LanguageSelector language={language} onChange={setLanguage} />
            <AccountSelector accountId={accountId} onChange={handleAccountChange} />
            {allMessages.length > 0 && (
              <button
                onClick={handleClear}
                className="text-xs text-relay-200 hover:text-white transition-colors"
                title="Clear chat"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Chat area */}
      <main className="flex-1 overflow-hidden max-w-3xl mx-auto w-full flex flex-col">
        {allMessages.length === 0 && !isLoading ? (
          <SampleQueries onSelect={handleSampleQuery} />
        ) : (
          <ChatWindow
            messages={allMessages}
            isLoading={isLoading || isProcessing}
            isStreaming={isStreaming}
            statusMessage={statusMessage}
            language={language}
          />
        )}
      </main>

      {/* Input bar */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        <div className="max-w-3xl mx-auto">
          {isActive ? (
            <RecordingPanel
              recordingState={recordingState}
              isPlaying={isPlaying}
              playbackProgress={playbackProgress}
              getAnalyserData={getAnalyserData}
              onPause={pauseRecording}
              onResume={resumeRecording}
              onStop={stopRecording}
              onStopAndSend={stopAndSend}
              onPlay={playPreview}
              onStopPlay={stopPreview}
              onDelete={deleteRecording}
              onSend={sendRecording}
            />
          ) : (
            <form
              onSubmit={handleSubmit}
              className="flex items-center gap-2"
            >
              <button
                onClick={() => startVoiceMode(accountId, language === "auto" ? "auto" : language, sessionId ?? undefined)}
                disabled={isLoading || isStreaming}
                className="w-10 h-10 rounded-full bg-relay-600 hover:bg-relay-700 disabled:bg-gray-200 flex items-center justify-center transition-colors"
                title="Start voice mode"
              >
                <Phone className="w-4 h-4 text-white" />
              </button>
              <VoiceRecorder onStart={startRecording} />
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a message..."
                disabled={isLoading || isStreaming}
                className="flex-1 bg-gray-50 border border-gray-200 rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-relay-500 focus:border-transparent disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading || isStreaming}
                className="w-10 h-10 rounded-full bg-relay-600 hover:bg-relay-700 disabled:bg-gray-200 flex items-center justify-center transition-colors"
              >
                <svg
                  className="w-5 h-5 text-white"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              </button>
            </form>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="text-center py-2 text-xs text-gray-400">
        Relay Demo &mdash; DuniaWallet Support Agent
      </footer>

      {/* Voice Mode Overlay */}
      {isVoiceModeActive && (
        <VoiceModeOverlay
          voiceModeState={voiceModeState}
          partialTranscript={partialTranscript}
          finalTranscript={finalTranscript}
          agentText={agentText}
          statusMessage={voiceModeStatus}
          turnMetadata={turnMetadata}
          onEnd={endVoiceMode}
        />
      )}
    </div>
  );
}

export default App;
