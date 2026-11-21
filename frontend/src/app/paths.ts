// All route paths in one place. Shared hot file.
import type { GameType } from '@/games/shared/types'

export const paths = {
  home: '/',
  patientToday: (id: string) => `/pacient/${id}`,
  patientCheckin: (id: string) => `/pacient/${id}/vnos`,
  patientGame: (id: string, gameType: GameType, level: number) => `/pacient/${id}/igra/${gameType}/${level}`,
  patientProgress: (id: string) => `/pacient/${id}/napredek`,
  clinician: '/zdravnik',
  clinicianPatient: (id: string) => `/zdravnik/pacient/${id}`,
}
