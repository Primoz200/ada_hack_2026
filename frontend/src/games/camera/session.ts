// One camera exercise from camera to GameResult, imperatively (a frame loop does not belong in React
// state). Ported from the teammate's recorder: requestVideoFrameCallback loop, detectForVideo with
// performance.now(), the tested hand picked by handedness, every video frame pushed (null when nothing
// was detected), cues on the recorder's timeline. The React component only shows what this reports.
import type { CameraExercise } from '@/client/api'
import type { GameConfig, GameResult } from '../shared/types'
import { Beeper } from './beeps'
import { BEEP_HZ, beepSchedule, cueTimes } from './cues'
import { createLandmarker, type Landmarker } from './detector'
import { FrameCheck, type FrameCheckState } from './frameCheck'
import { drawOverlay, readOverlayPalette, type OverlayPalette } from './overlay'
import { framedWell, pickHand, pickPose } from './pick'
import { buildCameraResult, newSeries, pushFrame, type Frame, type Series } from './series'
import { CameraUnavailable, openCamera, stopStream, type DevVideo, type Unavailable } from './source'

export type SessionPhase = 'starting' | 'framing' | 'countdown' | 'recording' | 'done'

export const COUNTDOWN_MS = 3000

export interface SessionListener {
  phase(p: SessionPhase): void
  videoSize(w: number, h: number): void
  framing(s: FrameCheckState & { seen: boolean }): void
  /** something detected in the latest frame (shown as a hint while recording) */
  seen(seen: boolean): void
  unavailable(reason: Unavailable): void
  complete(result: GameResult): void
}

interface VideoFrameMeta {
  mediaTime: number
}

type FrameCallbackVideo = HTMLVideoElement & {
  requestVideoFrameCallback?: (cb: (now: number, meta: VideoFrameMeta) => void) => number
  cancelVideoFrameCallback?: (id: number) => void
}

export class CameraSession {
  private readonly video: FrameCallbackVideo
  private readonly canvas: HTMLCanvasElement
  private readonly ex: CameraExercise
  private readonly config: GameConfig
  private readonly dev: DevVideo | null
  private readonly on: SessionListener
  private readonly beeper = new Beeper()
  private readonly check = new FrameCheck()
  private palette: OverlayPalette | undefined
  private stream: MediaStream | null = null
  private det: Landmarker | null = null
  private disposed = false
  private phase: SessionPhase = 'starting'
  private lastVideoTime = -1
  private frameHandle: number | undefined
  private rafHandle: number | undefined
  private timers: ReturnType<typeof setTimeout>[] = []
  private series: Series
  private readonly cues: number[]
  private t0 = 0
  private startedAt = new Date()
  private lastT = 0
  private framesSeen = 0
  private lastSeen: boolean | undefined
  private readonly onEnded = () => {
    if (this.phase === 'recording') this.finish(true)
  }

  constructor(opts: {
    video: HTMLVideoElement
    canvas: HTMLCanvasElement
    exercise: CameraExercise
    config: GameConfig
    dev: DevVideo | null
    listener: SessionListener
  }) {
    this.video = opts.video
    this.canvas = opts.canvas
    this.ex = opts.exercise
    this.config = opts.config
    this.dev = opts.dev
    this.on = opts.listener
    this.series = newSeries(this.ex.detector)
    this.cues = cueTimes(this.ex)
  }

  get kind() {
    return this.ex.detector
  }

  /** Call from the click that starts the exercise (audio unlock needs a user gesture). */
  unlockAudio(): void {
    this.beeper.unlock()
  }

  /** ms into the recording, for the progress bar and the prompt word. */
  elapsedMs(): number {
    if (this.phase === 'done') return this.ex.durationS * 1000
    if (this.phase !== 'recording') return 0
    if (this.dev) return this.video.currentTime * 1000
    return performance.now() - this.t0
  }

  countdownLeftMs(): number {
    return this.phase === 'countdown' ? Math.max(0, this.t0 - performance.now()) : 0
  }

  async start(): Promise<void> {
    this.setPhase('starting')
    try {
      if (this.dev) await this.openDevVideo(this.dev)
      else await this.openCamera()
      if (this.disposed) return
      this.det = await createLandmarker(this.ex.detector, this.dev?.cpuOnly ? ['CPU'] : undefined).catch((e) => {
        throw new CameraUnavailable('model', e)
      })
      if (this.disposed) {
        this.det.close()
        this.det = null
        return
      }
    } catch (e) {
      if (this.disposed) return
      this.release()
      this.on.unavailable(e instanceof CameraUnavailable ? e.reason : 'no_camera')
      return
    }
    this.canvas.width = this.video.videoWidth || 1280
    this.canvas.height = this.video.videoHeight || 720
    if (this.dev) {
      // warm the detector on the paused first frame, then the clock starts with the video
      try {
        this.det.detect(this.video, performance.now())
      } catch (e) {
        try {
          await this.fallbackToCpu(e)
        } catch {
          if (!this.disposed) {
            this.release()
            this.on.unavailable('model')
          }
          return
        }
        if (this.disposed || !this.det) return
      }
      this.video.playbackRate = this.dev.rate
      this.video.addEventListener('ended', this.onEnded)
      this.startRecording()
      await this.video.play().catch(() => undefined)
    } else {
      this.setPhase('framing')
    }
    this.scheduleFrame()
  }

  /** "Prekini" during the recording: what was recorded so far, completed = false. */
  stop(): void {
    if (this.phase === 'recording') this.finish(false, 'cancelled')
  }

  dispose(): void {
    this.disposed = true
    this.release()
  }

  // ---------------------------------------------------------------- sources

  private async openCamera(): Promise<void> {
    const stream = await openCamera()
    if (this.disposed) {
      stopStream(stream)
      return
    }
    this.stream = stream
    const v = this.video
    v.muted = true
    v.playsInline = true
    v.srcObject = stream
    await v.play().catch(() => undefined)
    await this.waitForSize()
  }

  private async openDevVideo(dev: DevVideo): Promise<void> {
    const v = this.video
    v.muted = true
    v.playsInline = true
    v.loop = false
    v.preload = 'auto'
    v.src = dev.url
    await new Promise<void>((resolve, reject) => {
      if (v.readyState >= 2) return resolve()
      v.addEventListener('loadeddata', () => resolve(), { once: true })
      v.addEventListener('error', () => reject(new CameraUnavailable('no_camera')), { once: true })
    })
    await this.waitForSize()
  }

  private async waitForSize(): Promise<void> {
    const v = this.video
    if (!v.videoWidth) {
      await new Promise<void>((resolve) => {
        v.addEventListener('loadedmetadata', () => resolve(), { once: true })
        this.timers.push(setTimeout(resolve, 3000))
      })
    }
    if (!this.disposed) this.on.videoSize(v.videoWidth || 1280, v.videoHeight || 720)
  }

  private async fallbackToCpu(e: unknown): Promise<void> {
    if (!this.det || this.det.delegate !== 'GPU') throw e
    console.warn('camera: GPU detection failed, switching to CPU', e)
    this.det.close()
    this.det = null
    const cpu = await createLandmarker(this.ex.detector, ['CPU'])
    if (this.disposed) cpu.close()
    else this.det = cpu
  }

  // ---------------------------------------------------------------- frame loop

  private scheduleFrame(): void {
    if (this.disposed || this.phase === 'done') return
    const v = this.video
    if (v.requestVideoFrameCallback) this.frameHandle = v.requestVideoFrameCallback((_now, meta) => this.onFrame(meta))
    else this.rafHandle = requestAnimationFrame(() => this.onFrame(undefined))
  }

  private switching = false

  private onFrame(meta: VideoFrameMeta | undefined): void {
    this.frameHandle = undefined
    this.rafHandle = undefined
    if (this.disposed) return
    const v = this.video
    const det = this.det
    if (det && !this.switching && v.currentTime !== this.lastVideoTime && v.readyState >= 2) {
      this.lastVideoTime = v.currentTime
      const now = performance.now()
      let res: ReturnType<Landmarker['detect']> | null = null
      try {
        res = det.detect(v, now)
      } catch (e) {
        if (this.framesSeen === 0 && det.delegate === 'GPU') {
          this.switching = true
          void this.fallbackToCpu(e)
            .catch(() => {
              if (!this.disposed) {
                this.release()
                this.on.unavailable('model')
              }
            })
            .finally(() => {
              this.switching = false
              this.scheduleFrame()
            })
          return
        }
        res = null
      }
      this.framesSeen++
      const frame: Frame | null = res
        ? this.ex.detector === 'hand'
          ? pickHand(res, this.config.hand)
          : pickPose(res)
        : null
      this.draw(frame)
      this.handleFrame(now, meta, frame)
    }
    this.scheduleFrame()
  }

  private handleFrame(now: number, meta: VideoFrameMeta | undefined, frame: Frame | null): void {
    const seen = frame !== null
    if (seen !== this.lastSeen) {
      this.lastSeen = seen
      this.on.seen(seen)
    }
    if (this.phase === 'framing') {
      const state = this.check.push(now, framedWell(this.ex.detector, frame))
      this.on.framing({ ...state, seen })
      if (state.ready) this.startCountdown()
      return
    }
    if (this.phase !== 'recording') return
    // dev video: the video's own clock, so a slowed-down playback still yields real-time t
    const t = this.dev ? (meta?.mediaTime ?? this.video.currentTime) * 1000 : now - this.t0
    const durationMs = this.ex.durationS * 1000
    if (t >= durationMs) {
      if (this.dev) this.finish(true)
      return
    }
    pushFrame(this.series, this.ex.detector, t, frame)
    this.lastT = t
  }

  private draw(frame: Frame | null): void {
    const ctx = this.canvas.getContext('2d')
    if (!ctx || !this.det) return
    this.palette ??= readOverlayPalette()
    drawOverlay(ctx, this.canvas.width, this.canvas.height, this.ex.detector, frame?.lm ?? null, this.det.connections, this.palette)
  }

  // ---------------------------------------------------------------- countdown, recording, finish

  private startCountdown(): void {
    this.t0 = performance.now() + COUNTDOWN_MS
    this.setPhase('countdown')
    this.beeper.schedule([0, 1000, 2000].map((atMs) => ({ atMs, hz: BEEP_HZ.countdown })))
    this.timers.push(setTimeout(() => this.startRecording(), COUNTDOWN_MS))
  }

  private startRecording(): void {
    if (this.disposed) return
    this.t0 = performance.now()
    this.startedAt = new Date()
    this.series = newSeries(this.ex.detector)
    this.setPhase('recording')
    this.beeper.schedule(beepSchedule(this.ex))
    if (!this.dev) this.timers.push(setTimeout(() => this.finish(true), this.ex.durationS * 1000))
  }

  private finish(completed: boolean, abortReason?: string): void {
    if (this.phase !== 'recording') return
    const durationMs = this.dev
      ? Math.min(this.ex.durationS * 1000, Math.max(this.lastT, this.video.currentTime * 1000))
      : performance.now() - this.t0
    const v = this.video
    const result = buildCameraResult({
      config: this.config,
      kind: this.ex.detector,
      series: this.series,
      cueT: this.cues,
      startedAt: this.startedAt,
      durationMs,
      completed,
      abortReason,
      videoW: v.videoWidth,
      videoH: v.videoHeight,
      delegate: this.det?.delegate ?? 'CPU',
      devicePixelRatio: window.devicePixelRatio || 1,
      userAgent: navigator.userAgent,
    })
    this.setPhase('done')
    // the camera goes off as soon as the exercise ends
    this.release()
    this.on.complete(result)
  }

  private setPhase(p: SessionPhase): void {
    this.phase = p
    if (!this.disposed) this.on.phase(p)
  }

  /** Stop everything: tracks, the loop, timers, beeps, the detector. Safe to call twice. */
  private release(): void {
    const v = this.video
    if (this.frameHandle !== undefined) v.cancelVideoFrameCallback?.(this.frameHandle)
    if (this.rafHandle !== undefined) cancelAnimationFrame(this.rafHandle)
    this.frameHandle = undefined
    this.rafHandle = undefined
    this.timers.forEach(clearTimeout)
    this.timers = []
    v.removeEventListener('ended', this.onEnded)
    stopStream(this.stream)
    this.stream = null
    try {
      v.pause()
      v.srcObject = null
      if (this.dev) v.removeAttribute('src')
    } catch {
      /* element may be gone */
    }
    this.beeper.close()
    this.det?.close()
    this.det = null
  }
}
