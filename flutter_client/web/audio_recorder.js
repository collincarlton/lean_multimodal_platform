(function() {
  class LeanAudioEngine {
    constructor() {
      this.audioContext = null;
      this.mediaStream = null;
      this.scriptNode = null;
      this.recordedSamples = [];
      this.totalSamples = 0;
      this.isRecording = false;
      this.startTime = null;
      this.liveWaveform = new Array(32).fill("0.050");
      this.previewAudio = null;
    }

    async start() {
      if (this.isRecording) return true;
      this.recordedSamples = [];
      this.totalSamples = 0;

      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioCtx();
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      const source = this.audioContext.createMediaStreamSource(this.mediaStream);

      // ScriptProcessorNode: captures raw PCM samples directly from hardware audio thread
      this.scriptNode = this.audioContext.createScriptProcessor(2048, 1, 1);

      this.scriptNode.onaudioprocess = (e) => {
        if (!this.isRecording) return;
        const input = e.inputBuffer.getChannelData(0);

        const copy = new Float32Array(input);
        this.recordedSamples.push(copy);
        this.totalSamples += copy.length;

        let sumSquares = 0;
        for (let i = 0; i < input.length; i++) {
          sumSquares += input[i] * input[i];
        }
        const rms = Math.sqrt(sumSquares / input.length);
        const vocalBoost = Math.min(1.0, rms * 5.5);

        const step = Math.floor(input.length / 32);
        const wave = [];
        for (let i = 0; i < 32; i++) {
          const sampleAmp = Math.abs(input[i * step] || 0);
          const dynamicVal = Math.max(sampleAmp * 2.8, vocalBoost);
          const clamped = Math.min(1.0, Math.max(0.06, dynamicVal));
          wave.push(clamped.toFixed(3));
        }
        this.liveWaveform = wave;

        const output = e.outputBuffer.getChannelData(0);
        output.fill(0);
      };

      source.connect(this.scriptNode);
      this.scriptNode.connect(this.audioContext.destination);

      this.startTime = Date.now();
      this.isRecording = true;
      return true;
    }

    getWaveformString() {
      if (!this.isRecording) {
        return new Array(32).fill("0.050").join(",");
      }
      return this.liveWaveform.join(",");
    }

    getDuration() {
      if (!this.startTime) return 0;
      return Date.now() - this.startTime;
    }

    stop() {
      if (!this.isRecording) return Promise.resolve(null);
      this.isRecording = false;

      const duration = this.startTime ? Date.now() - this.startTime : 0;

      const flat = new Float32Array(this.totalSamples);
      let offset = 0;
      for (let i = 0; i < this.recordedSamples.length; i++) {
        flat.set(this.recordedSamples[i], offset);
        offset += this.recordedSamples[i].length;
      }

      const sourceSampleRate = this.audioContext.sampleRate || 44100;
      const targetSampleRate = 16000;
      const downsampled = this._downsample(flat, sourceSampleRate, targetSampleRate);
      const base64Wav = this._encodeWAV(downsampled, targetSampleRate);

      this._cleanup();

      return Promise.resolve({
        base64: base64Wav,
        mimeType: 'audio/wav',
        durationMs: duration
      });
    }

    cancel() {
      this._cleanup();
      this.isRecording = false;
    }

    playPreview(base64Data, mimeType) {
      try {
        if (!base64Data || base64Data.length < 50) return;
        const binary = atob(base64Data);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i);
        }

        const blob = new Blob([bytes], { type: mimeType || 'audio/wav' });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => URL.revokeObjectURL(url);
        
        const playPromise = audio.play();
        if (playPromise !== undefined) {
          playPromise.catch(() => {
            // WebKit Fallback: Decode directly to AudioContext output
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            const ctx = new AudioCtx();
            ctx.decodeAudioData(bytes.buffer.slice(0), (buf) => {
              const src = ctx.createBufferSource();
              src.buffer = buf;
              src.connect(ctx.destination);
              src.start(0);
            });
          });
        }
      } catch (err) {
        console.error('[PREVIEW FAILED]', err);
      }
    }

    _downsample(buffer, fromRate, toRate) {
      if (fromRate === toRate) return buffer;
      const ratio = fromRate / toRate;
      const newLength = Math.round(buffer.length / ratio);
      const result = new Float32Array(newLength);
      let offset = 0;
      for (let i = 0; i < newLength; i++) {
        const nextOffset = Math.round((i + 1) * ratio);
        let accum = 0;
        let count = 0;
        for (let j = offset; j < nextOffset && j < buffer.length; j++) {
          accum += buffer[j];
          count++;
        }
        result[i] = count > 0 ? accum / count : 0;
        offset = nextOffset;
      }
      return result;
    }

    _encodeWAV(samples, sampleRate) {
      const buffer = new ArrayBuffer(44 + samples.length * 2);
      const view = new DataView(buffer);

      this._writeString(view, 0, 'RIFF');
      view.setUint32(4, 36 + samples.length * 2, true);
      this._writeString(view, 8, 'WAVE');
      this._writeString(view, 12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true); // PCM
      view.setUint16(22, 1, true); // Mono
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * 2, true);
      view.setUint16(32, 2, true);
      view.setUint16(34, 16, true);
      this._writeString(view, 36, 'data');
      view.setUint32(40, samples.length * 2, true);

      let index = 44;
      for (let i = 0; i < samples.length; i++) {
        const s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(index, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        index += 2;
      }

      const bytes = new Uint8Array(buffer);
      let binary = '';
      const chunkSize = 0x8000;
      for (let i = 0; i < bytes.length; i += chunkSize) {
        const chunk = bytes.subarray(i, i + chunkSize);
        binary += String.fromCharCode.apply(null, chunk);
      }
      return btoa(binary);
    }

    _writeString(view, offset, string) {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    }

    _cleanup() {
      if (this.scriptNode) {
        this.scriptNode.disconnect();
        this.scriptNode = null;
      }
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(t => t.stop());
        this.mediaStream = null;
      }
      if (this.audioContext && this.audioContext.state !== 'closed') {
        this.audioContext.close();
        this.audioContext = null;
      }
      this.recordedSamples = [];
      this.totalSamples = 0;
    }
  }

  window.LeanAudioEngine = new LeanAudioEngine();
})();
