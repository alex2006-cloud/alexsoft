/** Procedural chiptune — original loop, not a Konami rip. */

type Voice = {
  osc: OscillatorNode;
  gain: GainNode;
};

export class Chiptune {
  private ctx: AudioContext | null = null;
  private master: GainNode | null = null;
  private timer: number | null = null;
  private step = 0;
  muted = false;

  async resume() {
    if (!this.ctx) {
      this.ctx = new AudioContext();
      this.master = this.ctx.createGain();
      this.master.gain.value = this.muted ? 0 : 0.09;
      this.master.connect(this.ctx.destination);
    }
    if (this.ctx.state === "suspended") await this.ctx.resume();
  }

  setMuted(muted: boolean) {
    this.muted = muted;
    if (this.master) this.master.gain.value = muted ? 0 : 0.09;
  }

  start() {
    if (this.timer != null || !this.ctx || !this.master) return;
    const bpm = 148;
    const stepMs = (60_000 / bpm) / 2;
    this.step = 0;

    const tick = () => {
      if (!this.ctx || !this.master) return;
      const t = this.ctx.currentTime;
      const s = this.step % 32;

      // Kick / noise hat
      if (s % 4 === 0) this.kick(t);
      if (s % 2 === 1) this.hat(t);

      // Bass arpeggio (Am / F / C / G feel in A minor-ish)
      const bass = [110, 110, 130.81, 146.83, 164.81, 146.83, 130.81, 110];
      this.tone(bass[s % 8], t, 0.14, "square", 0.07);

      // Lead — original run-and-gun motif
      const lead = [
        440, 0, 523.25, 0, 659.25, 523.25, 440, 0, 392, 0, 440, 493.88, 523.25, 0, 659.25, 0, 784,
        0, 659.25, 523.25, 587.33, 523.25, 440, 0, 392, 349.23, 392, 440, 493.88, 0, 523.25, 0,
      ];
      if (lead[s]) this.tone(lead[s], t, 0.11, "triangle", 0.055);

      this.step += 1;
    };

    tick();
    this.timer = window.setInterval(tick, stepMs);
  }

  stop() {
    if (this.timer != null) {
      window.clearInterval(this.timer);
      this.timer = null;
    }
  }

  dispose() {
    this.stop();
    void this.ctx?.close();
    this.ctx = null;
    this.master = null;
  }

  /** Short one-shot SFX */
  sfx(kind: "shoot" | "hit" | "jump" | "die" | "win") {
    if (!this.ctx || !this.master || this.muted) return;
    const t = this.ctx.currentTime;
    if (kind === "shoot") this.tone(880, t, 0.06, "square", 0.04);
    if (kind === "jump") this.sweep(220, 440, t, 0.08, 0.04);
    if (kind === "hit") this.tone(180, t, 0.1, "sawtooth", 0.05);
    if (kind === "die") this.sweep(320, 80, t, 0.35, 0.08);
    if (kind === "win") {
      this.tone(523.25, t, 0.12, "triangle", 0.06);
      this.tone(659.25, t + 0.12, 0.12, "triangle", 0.06);
      this.tone(783.99, t + 0.24, 0.2, "triangle", 0.07);
    }
  }

  private voice(type: OscillatorType): Voice | null {
    if (!this.ctx || !this.master) return null;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = type;
    gain.connect(this.master);
    osc.connect(gain);
    return { osc, gain };
  }

  private tone(
    freq: number,
    when: number,
    dur: number,
    type: OscillatorType,
    vol: number,
  ) {
    const v = this.voice(type);
    if (!v) return;
    v.osc.frequency.setValueAtTime(freq, when);
    v.gain.gain.setValueAtTime(0.0001, when);
    v.gain.gain.exponentialRampToValueAtTime(vol, when + 0.01);
    v.gain.gain.exponentialRampToValueAtTime(0.0001, when + dur);
    v.osc.start(when);
    v.osc.stop(when + dur + 0.02);
  }

  private sweep(from: number, to: number, when: number, dur: number, vol: number) {
    const v = this.voice("square");
    if (!v) return;
    v.osc.frequency.setValueAtTime(from, when);
    v.osc.frequency.exponentialRampToValueAtTime(Math.max(to, 40), when + dur);
    v.gain.gain.setValueAtTime(0.0001, when);
    v.gain.gain.exponentialRampToValueAtTime(vol, when + 0.01);
    v.gain.gain.exponentialRampToValueAtTime(0.0001, when + dur);
    v.osc.start(when);
    v.osc.stop(when + dur + 0.02);
  }

  private kick(when: number) {
    this.sweep(140, 45, when, 0.12, 0.09);
  }

  private hat(when: number) {
    if (!this.ctx || !this.master) return;
    const bufferSize = 2 * this.ctx.sampleRate * 0.03;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize);
    const src = this.ctx.createBufferSource();
    const gain = this.ctx.createGain();
    src.buffer = buffer;
    gain.gain.setValueAtTime(0.03, when);
    gain.gain.exponentialRampToValueAtTime(0.0001, when + 0.03);
    src.connect(gain);
    gain.connect(this.master);
    src.start(when);
  }
}
