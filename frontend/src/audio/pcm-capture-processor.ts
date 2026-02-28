/**
 * AudioWorklet processor that captures microphone audio as 16-bit PCM
 * at 16kHz mono. Runs in a dedicated audio thread for low-latency capture.
 *
 * The processor downsamples from the AudioContext's native sample rate
 * (typically 44100 or 48000 Hz) to 16000 Hz, then converts Float32 samples
 * to Int16 PCM and posts the buffer to the main thread.
 */

const TARGET_SAMPLE_RATE = 16000;
const BUFFER_SIZE = 4096;

class PcmCaptureProcessor extends AudioWorkletProcessor {
  private buffer: Float32Array = new Float32Array(BUFFER_SIZE);
  private bufferOffset = 0;
  private resampleRatio: number;

  constructor() {
    super();
    this.resampleRatio = TARGET_SAMPLE_RATE / sampleRate;
  }

  process(inputs: Float32Array[][]): boolean {
    const channelData = inputs[0];
    if (!channelData) return true;
    const input = channelData[0];
    if (!input || input.length === 0) return true;

    const resampled = this.downsample(input);
    for (let i = 0; i < resampled.length; i++) {
      this.buffer[this.bufferOffset++] = resampled[i] as number;

      if (this.bufferOffset >= BUFFER_SIZE) {
        this.flush();
      }
    }

    return true;
  }

  private downsample(input: Float32Array): Float32Array {
    if (this.resampleRatio >= 1) {
      return input;
    }

    const outputLength = Math.ceil(input.length * this.resampleRatio);
    const output = new Float32Array(outputLength);

    for (let i = 0; i < outputLength; i++) {
      const srcIndex = i / this.resampleRatio;
      const srcFloor = Math.floor(srcIndex);
      const srcCeil = Math.min(srcFloor + 1, input.length - 1);
      const frac = srcIndex - srcFloor;
      output[i] = (input[srcFloor] ?? 0) * (1 - frac) + (input[srcCeil] ?? 0) * frac;
    }

    return output;
  }

  private flush(): void {
    const pcmData = this.buffer.slice(0, this.bufferOffset);
    const int16 = this.float32ToInt16(pcmData);
    this.port.postMessage(int16.buffer, [int16.buffer]);
    this.buffer = new Float32Array(BUFFER_SIZE);
    this.bufferOffset = 0;
  }

  private float32ToInt16(float32: Float32Array): Int16Array {
    const int16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      const s = Math.max(-1, Math.min(1, float32[i] ?? 0));
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return int16;
  }
}

registerProcessor("pcm-capture-processor", PcmCaptureProcessor);
