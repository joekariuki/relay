import { useEffect, useRef } from "react";

const BAR_WIDTH = 3;
const BAR_GAP = 2;
const MIN_BAR_HEIGHT = 2;
const RELAY_600 = "#059669";
const GRAY_300 = "#d1d5db";
const SAMPLE_INTERVAL_MS = 50;
const AMPLITUDE_SCALE = 5;

/** Compute RMS amplitude (0–1) from time-domain data centered at 128. */
function computeAmplitude(rawData: Uint8Array): number {
  let sum = 0;
  for (let i = 0; i < rawData.length; i++) {
    const sample = (rawData[i] ?? 128) - 128;
    sum += sample * sample;
  }
  const rms = Math.sqrt(sum / rawData.length) / 128;
  return Math.min(1, rms * AMPLITUDE_SCALE);
}

interface Props {
  /** Called each animation frame in live mode to read time-domain data. */
  getAnalyserData?: () => Uint8Array | null;
  /** Whether the waveform should animate (true = recording, false = paused). */
  isActive: boolean;
  /** Static amplitude data (0–1 per bar) for preview mode. */
  frozenData?: number[];
  /** 0–1 playback progress for coloring played vs unplayed bars. */
  playbackProgress?: number;
  /** Canvas height in CSS pixels. */
  height?: number;
}

export function WaveformCanvas({
  getAnalyserData,
  isActive,
  frozenData,
  playbackProgress,
  height = 40,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef(0);

  // Rolling buffer: each entry is one amplitude sample over time
  const rollingBufferRef = useRef<number[]>([]);
  const lastSampleTimeRef = useRef(0);

  // Live rolling waveform (recording / paused)
  useEffect(() => {
    if (frozenData) return;

    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const dpr = window.devicePixelRatio || 1;

    const draw = () => {
      const width = container.clientWidth;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.scale(dpr, dpr);

      const barCount = Math.floor(width / (BAR_WIDTH + BAR_GAP));
      const centerY = height / 2;
      const now = performance.now();

      // Sample new amplitude if active and enough time has elapsed
      if (isActive && getAnalyserData) {
        if (now - lastSampleTimeRef.current >= SAMPLE_INTERVAL_MS) {
          const rawData = getAnalyserData();
          if (rawData && rawData.length > 0) {
            rollingBufferRef.current.push(computeAmplitude(rawData));
          }
          lastSampleTimeRef.current = now;
        }
      }

      // Trim buffer to fit canvas
      const buffer = rollingBufferRef.current;
      if (buffer.length > barCount) {
        buffer.splice(0, buffer.length - barCount);
      }

      // Draw bars right-aligned (newest on right)
      ctx.clearRect(0, 0, width, height);
      const offset = barCount - buffer.length;

      for (let i = 0; i < buffer.length; i++) {
        const amplitude = buffer[i] ?? 0;
        const barHeight = Math.max(MIN_BAR_HEIGHT, amplitude * height);
        const x = (offset + i) * (BAR_WIDTH + BAR_GAP);
        ctx.fillStyle = RELAY_600;
        ctx.fillRect(x, centerY - barHeight / 2, BAR_WIDTH, barHeight);
      }

      if (isActive) {
        rafRef.current = requestAnimationFrame(draw);
      }
    };

    draw();

    return () => cancelAnimationFrame(rafRef.current);
  }, [isActive, getAnalyserData, frozenData, height]);

  // Static / preview waveform rendering
  useEffect(() => {
    if (!frozenData) return;

    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const dpr = window.devicePixelRatio || 1;
    const width = container.clientWidth;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);

    const barCount = Math.floor(width / (BAR_WIDTH + BAR_GAP));
    const centerY = height / 2;
    const progress = playbackProgress ?? 0;
    const playedBars = Math.floor(progress * barCount);
    const dataLen = frozenData.length;

    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < barCount; i++) {
      // Map bar index to frozenData index (stretch data across full width)
      const dataIndex = dataLen > 0 ? (i / barCount) * dataLen : 0;
      const lo = Math.floor(dataIndex);
      const hi = Math.min(lo + 1, dataLen - 1);
      const t = dataIndex - lo;
      const amplitude = ((frozenData[lo] ?? 0) * (1 - t)) + ((frozenData[hi] ?? 0) * t);
      const barHeight = Math.max(MIN_BAR_HEIGHT, amplitude * height);
      const x = i * (BAR_WIDTH + BAR_GAP);
      ctx.fillStyle = i < playedBars ? RELAY_600 : GRAY_300;
      ctx.fillRect(x, centerY - barHeight / 2, BAR_WIDTH, barHeight);
    }
  }, [frozenData, playbackProgress, height]);

  return (
    <div ref={containerRef} className="flex-1 min-w-0">
      <canvas
        ref={canvasRef}
        className="w-full rounded"
        style={{ height: `${height}px` }}
      />
    </div>
  );
}
