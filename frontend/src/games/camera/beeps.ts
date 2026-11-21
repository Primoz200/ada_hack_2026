// WebAudio beeps, scheduled on the audio clock as the recorder does. Audio is best effort: it never
// gates the recording, and closing the context silences anything still scheduled.

export class Beeper {
  private ctx: AudioContext | undefined

  /** Call from a user gesture where possible (autoplay rules). Never throws, never waits long. */
  unlock(): void {
    try {
      const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
      if (!AC) return
      this.ctx ??= new AC()
      void this.ctx.resume().catch(() => undefined)
    } catch {
      this.ctx = undefined
    }
  }

  /** Beeps at ms offsets from now. */
  schedule(beeps: readonly { atMs: number; hz: number }[]): void {
    const ctx = this.ctx
    if (!ctx || ctx.state === 'closed') return
    const a0 = ctx.currentTime + 0.02
    for (const b of beeps) this.beep(ctx, a0 + b.atMs / 1000, b.hz)
  }

  private beep(ctx: AudioContext, at: number, hz: number, dur = 0.12): void {
    try {
      const o = ctx.createOscillator()
      const g = ctx.createGain()
      o.frequency.value = hz
      o.connect(g)
      g.connect(ctx.destination)
      g.gain.setValueAtTime(0.0001, at)
      g.gain.exponentialRampToValueAtTime(0.3, at + 0.01)
      g.gain.exponentialRampToValueAtTime(0.0001, at + dur)
      o.start(at)
      o.stop(at + dur + 0.02)
    } catch {
      /* audio is best effort */
    }
  }

  close(): void {
    const ctx = this.ctx
    this.ctx = undefined
    if (ctx && ctx.state !== 'closed') void ctx.close().catch(() => undefined)
  }
}
