// Thin typed API client. Types come from the generated schema.d.ts (do not edit that file by hand;
// run scripts/gen_contract.sh after a contract change).
import createClient from 'openapi-fetch'
import type { components, paths } from './schema'

export const api = createClient<paths>({ baseUrl: '/' })

type S = components['schemas']
export type Pathway = S['PathwayOut']
export type Question = S['Question']
export type PatientList = S['PatientListOut']
export type PatientListItem = S['PatientListItem']
export type PatientDetail = S['PatientDetail']
export type Timeline = S['TimelineOut']
export type SessionSummary = S['SessionSummary']
export type Checkin = S['CheckinOut']
export type CheckinIn = S['CheckinIn']
export type TrendPoint = S['TrendPoint']
export type Alert = S['AlertOut']
export type AlertAckIn = S['AlertAckIn']
export type PatientHome = S['PatientHomeOut']
export type SelfcheckStep = S['SelfcheckStep']
export type SelfcheckSummary = S['SelfcheckSummary']
export type Progress = S['ProgressOut']
export type ProgressPoint = S['ProgressPoint']
export type RatingPoint = S['RatingPoint']
export type GameProgress = S['GameProgress']
export type CameraExercise = S['CameraExercise']
export type SessionIn = S['SessionIn']
export type SessionResult = S['SessionResult']
export type SessionRaw = S['SessionRawOut']
export type Meta = S['MetaOut']
export type Outcome = NonNullable<S['AlertAckIn']['outcome']>

/** Unwrap an openapi-fetch result or throw with the server's message. */
export async function unwrap<T>(p: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const { data, error, response } = await p
  if (error !== undefined || data === undefined) {
    const detail = (error as { detail?: unknown } | undefined)?.detail
    throw new Error(typeof detail === 'string' ? detail : `Napaka strežnika (${response.status})`)
  }
  return data
}
