// Where the frames come from: the webcam, or (dev builds only) a recorded video given as
// ?cameraVideo=<url>, which runs the identical pipeline without a camera.

export type Unavailable = 'unsupported' | 'no_camera' | 'denied' | 'busy' | 'model'

export class CameraUnavailable extends Error {
  readonly reason: Unavailable
  constructor(reason: Unavailable, cause?: unknown) {
    super(reason)
    this.reason = reason
    this.cause = cause
  }
}

/** getUserMedia errors -> what we tell the patient. */
export function classifyMediaError(e: unknown): Unavailable {
  const name = (e as { name?: string } | null)?.name ?? ''
  if (name === 'NotAllowedError' || name === 'SecurityError' || name === 'PermissionDeniedError') return 'denied'
  if (name === 'NotFoundError' || name === 'OverconstrainedError' || name === 'DevicesNotFoundError') return 'no_camera'
  if (name === 'NotReadableError' || name === 'AbortError' || name === 'TrackStartError') return 'busy'
  return 'no_camera'
}

export interface DevVideo {
  url: string
  /** playback rate, so a slow CPU detector still sees most frames (t follows the video's own clock) */
  rate: number
  /** ?cameraDelegate=CPU skips the GPU delegate (to check the fallback) */
  cpuOnly: boolean
}

/** ?cameraVideo=<url>[&cameraVideoRate=0.5][&cameraDelegate=CPU], only in dev builds. */
export function devVideo(search: string = typeof window === 'undefined' ? '' : window.location.search): DevVideo | null {
  if (!import.meta.env.DEV) return null
  const q = new URLSearchParams(search)
  const url = q.get('cameraVideo')
  if (!url) return null
  const rate = Number(q.get('cameraVideoRate') ?? '1')
  return { url, rate: Number.isFinite(rate) && rate > 0 ? rate : 1, cpuOnly: q.get('cameraDelegate') === 'CPU' }
}

export async function openCamera(): Promise<MediaStream> {
  if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
    throw new CameraUnavailable('unsupported')
  }
  try {
    return await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, frameRate: { ideal: 30 }, facingMode: 'user' },
      audio: false,
    })
  } catch (e) {
    throw new CameraUnavailable(classifyMediaError(e), e)
  }
}

export function stopStream(stream: MediaStream | null | undefined): void {
  stream?.getTracks().forEach((t) => t.stop())
}
