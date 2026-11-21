// MediaPipe landmarkers with the recorder's options. Loaded lazily (its own chunk) from our own origin:
// wasm and models live in public/vendor/mediapipe (scripts/setup_mediapipe.sh). GPU first, CPU fallback.
import type { Detector } from './exercises'
import type { HandResultLike, PoseResultLike } from './pick'

export type Delegate = 'GPU' | 'CPU'

export interface Landmarker {
  kind: Detector
  delegate: Delegate
  detect(video: HTMLVideoElement, timestampMs: number): HandResultLike & PoseResultLike
  close(): void
  /** pairs of landmark indices to draw */
  connections: readonly { start: number; end: number }[]
}

const BASE = `${import.meta.env.BASE_URL}vendor/mediapipe`

type Vision = typeof import('@mediapipe/tasks-vision')
let vision: Promise<Vision> | undefined
let fileset: Promise<Awaited<ReturnType<Vision['FilesetResolver']['forVisionTasks']>>> | undefined

function loadFileset() {
  vision ??= import('@mediapipe/tasks-vision')
  fileset ??= vision.then((v) => v.FilesetResolver.forVisionTasks(`${BASE}/wasm`))
  // a failed load must not be cached: the next exercise tries again
  fileset.catch(() => {
    vision = undefined
    fileset = undefined
  })
  return Promise.all([vision, fileset] as const)
}

export async function createLandmarker(kind: Detector, delegates: readonly Delegate[] = ['GPU', 'CPU']): Promise<Landmarker> {
  const [v, fs] = await loadFileset()
  let lastError: unknown
  for (const delegate of delegates) {
    try {
      if (kind === 'hand') {
        const det = await v.HandLandmarker.createFromOptions(fs, {
          baseOptions: { modelAssetPath: `${BASE}/models/hand_landmarker.task`, delegate },
          runningMode: 'VIDEO',
          numHands: 2,
          minHandDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5,
        })
        return {
          kind,
          delegate,
          detect: (video, ts) => det.detectForVideo(video, ts),
          close: () => det.close(),
          connections: v.HandLandmarker.HAND_CONNECTIONS,
        }
      }
      const det = await v.PoseLandmarker.createFromOptions(fs, {
        baseOptions: { modelAssetPath: `${BASE}/models/pose_landmarker_full.task`, delegate },
        runningMode: 'VIDEO',
        numPoses: 1,
        minPoseDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      })
      return {
        kind,
        delegate,
        detect: (video, ts) => det.detectForVideo(video, ts),
        close: () => det.close(),
        connections: v.PoseLandmarker.POSE_CONNECTIONS,
      }
    } catch (e) {
      lastError = e
      console.warn(`camera: ${kind} landmarker with ${delegate} failed`, e)
    }
  }
  throw lastError ?? new Error('landmarker unavailable')
}
