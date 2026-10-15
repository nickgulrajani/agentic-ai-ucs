import type { CaseForm } from './types'

export const PRESETS: Record<string, { label: string; form: CaseForm }> = {
  meets: {
    label: 'Meets criteria',
    form: {
      patient: 'Jordan Rivera (fictional)',
      dob: '1968-03-14',
      member: 'AHP-0042-7781',
      payer: 'Acme Health Plan (fictional)',
      cpt: '72148',
      icd: 'M54.16',
      fault: 'none',
      note:
        '58-year-old with low back pain radiating down the left leg for 9 weeks. Completed 6 weeks of physical therapy (12 visits) without meaningful improvement. Trialed naproxen 500 mg twice daily and cyclobenzaprine 10 mg at bedtime. Exam: positive straight-leg raise on the left, diminished left ankle reflex, numbness in the L5-S1 distribution. No bowel or bladder changes. No history of cancer. No prior lumbar imaging. Candidate for epidural steroid injection pending imaging.',
    },
  },
  gap: {
    label: 'Missing documentation',
    form: {
      patient: 'Casey Morgan (fictional)',
      dob: '1979-11-02',
      member: 'AHP-0042-3310',
      payer: 'Acme Health Plan (fictional)',
      cpt: '72148',
      icd: 'M54.50',
      fault: 'none',
      note:
        'Patient reports low back pain for about 3 weeks after lifting boxes. Taking naproxen 500 mg as needed. Exam notes tenderness over the lumbar paraspinals, full strength in both legs. Requesting MRI to rule out disc herniation.',
    },
  },
  redflag: {
    label: 'Red flag · urgent',
    form: {
      patient: 'Avery Chen (fictional)',
      dob: '1961-06-27',
      member: 'AHP-0042-9054',
      payer: 'Acme Health Plan (fictional)',
      cpt: '72148',
      icd: 'M54.16',
      fault: 'none',
      note:
        'Acute worsening low back pain over 48 hours with new saddle numbness and urinary retention. Bilateral leg weakness on exam. Gabapentin 300 mg started last week for radicular pain. Requesting urgent lumbar MRI.',
    },
  },
}

export const FAULTS = [
  { value: 'none', label: 'None · happy path' },
  { value: 'mcp_timeout', label: 'MCP timeout · policy slow' },
  { value: 'mcp_down', label: 'MCP outage · eligibility down' },
  { value: 'policy_missing', label: 'Missing policy document' },
  { value: 'grounding_fail', label: 'Grounding check fails first draft' },
]
