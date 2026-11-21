// All route paths in one place. Shared hot file.
export const paths = {
  home: '/',
  patientHome: (id: string) => `/pacient/${id}`,
  selfcheck: (id: string) => `/pacient/${id}/samopregled`,
  progress: (id: string) => `/pacient/${id}/napredek`,
  clinician: '/zdravnik',
  clinicianPatient: (id: string) => `/zdravnik/pacient/${id}`,
}

const LAST_PATIENT_KEY = 'okrevanje.lastPatient'

/** The patient view remembers who was selected, so switching back from the clinician view returns there. */
export function rememberPatient(id: string) {
  try {
    localStorage.setItem(LAST_PATIENT_KEY, id)
  } catch {
    // storage may be unavailable; the default patient is used instead
  }
}

export function lastPatient(): string | null {
  try {
    return localStorage.getItem(LAST_PATIENT_KEY)
  } catch {
    return null
  }
}
