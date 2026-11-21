// Every route of the app. Shared hot file: feature agents edit their page files, not this one.
import { createBrowserRouter } from 'react-router'
import { ClinicianPatientPage } from '@/features/clinician/ClinicianPatientPage'
import { TriagePage } from '@/features/clinician/TriagePage'
import { HomePage } from '@/features/patient/HomePage'
import { ProgressPage } from '@/features/patient/ProgressPage'
import { SelfcheckPage } from '@/features/patient/SelfcheckPage'
import { ClinicianShell, PatientShell } from './AppShell'
import { RootRedirect } from './RootRedirect'

export const router = createBrowserRouter([
  { path: '/', element: <RootRedirect /> },
  {
    path: '/pacient/:patientId',
    element: <PatientShell />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'samopregled', element: <SelfcheckPage /> },
      { path: 'napredek', element: <ProgressPage /> },
    ],
  },
  {
    path: '/zdravnik',
    element: <ClinicianShell />,
    children: [
      { index: true, element: <TriagePage /> },
      { path: 'pacient/:patientId', element: <ClinicianPatientPage /> },
    ],
  },
])
