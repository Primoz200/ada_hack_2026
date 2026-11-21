// Every route of the app. Shared hot file: feature agents edit their page files, not this one.
import { createBrowserRouter } from 'react-router'
import { ClinicianPatientPage } from '@/features/clinician/ClinicianPatientPage'
import { TriagePage } from '@/features/clinician/TriagePage'
import { CheckinPage } from '@/features/patient/CheckinPage'
import { GamePage } from '@/features/patient/GamePage'
import { ProgressPage } from '@/features/patient/ProgressPage'
import { TodayPage } from '@/features/patient/TodayPage'
import { ClinicianLayout } from './ClinicianLayout'
import { PatientLayout } from './PatientLayout'
import { RoleSelectPage } from './RoleSelectPage'

export const router = createBrowserRouter([
  { path: '/', element: <RoleSelectPage /> },
  {
    path: '/pacient/:patientId',
    element: <PatientLayout />,
    children: [
      { index: true, element: <TodayPage /> },
      { path: 'vnos', element: <CheckinPage /> },
      { path: 'igra/:gameType/:level', element: <GamePage /> },
      { path: 'napredek', element: <ProgressPage /> },
    ],
  },
  {
    path: '/zdravnik',
    element: <ClinicianLayout />,
    children: [
      { index: true, element: <TriagePage /> },
      { path: 'pacient/:patientId', element: <ClinicianPatientPage /> },
    ],
  },
])
