import { useEffect, useRef } from "react";

const BAR_WIDTH = 3;
const BAR_GAP = 2;
const MIN_BAR_HEIGHT = 2;
const RELAY_600 = "#059669";
const GRAY_300 = "#d1d5db";

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
  const lastBarsRef = useRef<number[]>([]);

  // Live waveform animation loop (recording / paused)
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

      if (isActive && getAnalyserData) {
        const rawData = getAnalyserData();
        if (rawData && rawData.length > 0) {
          const samplesPerBar = Math.max(
            1,
            Math.floor(rawData.length / barCount),
          );
          const bars: number[] = [];
          for (let i = 0; i < barCount; i++) {
            let sum = 0;
            for (let j = 0; j < samplesPerBar; j++) {
              const idx = i * samplesPerBar + j;
              const sample = idx < rawData.length ? (rawData[idx] ?? 128) : 128;
              sum += Math.abs(sample - 128);
            }
            bars.push(sum / samplesPerBar / 128);
          }
          lastBarsRef.current = bars;
        }
      }

      ctx.clearRect(0, 0, width, height);
      const bars = lastBarsRef.current;

      for (let i = 0; i < bars.length; i++) {
        const amplitude = bars[i] ?? 0;
        const barHeight = Math.max(MIN_BAR_HEIGHT, amplitude * height);
        const x = i * (BAR_WIDTH + BAR_GAP);
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

    const barCount = Math.min(
      frozenData.length,
      Math.floor(width / (BAR_WIDTH + BAR_GAP)),
    );
    const centerY = height / 2;
    const progress = playbackProgress ?? 0;
    const playedBars = Math.floor(progress * barCount);

    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < barCount; i++) {
      const amplitude = frozenData[i] ?? 0;
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
