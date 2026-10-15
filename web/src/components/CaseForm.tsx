import { FAULTS, PRESETS } from '../presets'
import type { CaseForm as Form } from '../types'

export function CaseFormPanel({
  form,
  preset,
  running,
  onPreset,
  onChange,
  onSubmit,
  onReset,
}: {
  form: Form
  preset: string
  running: boolean
  onPreset: (k: string) => void
  onChange: (patch: Partial<Form>) => void
  onSubmit: () => void
  onReset: () => void
}) {
  return (
    <div className="pane">
      <div className="pane-h">
        <h3>Prior authorization request</h3>
        <span className="label">FHIR ServiceRequest</span>
      </div>
      <div className="pane-b">
        <div className="label" style={{ marginBottom: 6 }}>
          Scenario
        </div>
        <div className="presets">
          {Object.entries(PRESETS).map(([k, p]) => (
            <button
              key={k}
              type="button"
              className={preset === k ? 'on' : ''}
              disabled={running}
              onClick={() => onPreset(k)}
            >
              {p.label}
            </button>
          ))}
        </div>
        <div className="row2">
          <div className="field">
            <label className="label" htmlFor="f-name">
              Patient
            </label>
            <input
              id="f-name"
              value={form.patient}
              disabled={running}
              onChange={(e) => onChange({ patient: e.target.value })}
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="f-dob">
              DOB
            </label>
            <input
              id="f-dob"
              value={form.dob}
              disabled={running}
              onChange={(e) => onChange({ dob: e.target.value })}
            />
          </div>
        </div>
        <div className="row2">
          <div className="field">
            <label className="label" htmlFor="f-member">
              Member ID
            </label>
            <input
              id="f-member"
              value={form.member}
              disabled={running}
              onChange={(e) => onChange({ member: e.target.value })}
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="f-payer">
              Payer
            </label>
            <input
              id="f-payer"
              value={form.payer}
              disabled={running}
              onChange={(e) => onChange({ payer: e.target.value })}
            />
          </div>
        </div>
        <div className="row2">
          <div className="field">
            <label className="label" htmlFor="f-cpt">
              Service (CPT)
            </label>
            <select id="f-cpt" value={form.cpt} disabled={running} onChange={(e) => onChange({ cpt: e.target.value })}>
              <option value="72148">72148 · MRI lumbar spine w/o contrast</option>
            </select>
          </div>
          <div className="field">
            <label className="label" htmlFor="f-icd">
              Diagnosis (ICD-10)
            </label>
            <select id="f-icd" value={form.icd} disabled={running} onChange={(e) => onChange({ icd: e.target.value })}>
              <option value="M54.16">M54.16 · Radiculopathy, lumbar</option>
              <option value="M54.50">M54.50 · Low back pain, unspecified</option>
            </select>
          </div>
        </div>
        <div className="field">
          <label className="label" htmlFor="f-note">
            Clinical note
          </label>
          <textarea
            id="f-note"
            value={form.note}
            disabled={running}
            onChange={(e) => onChange({ note: e.target.value })}
          />
        </div>
        <div className="field">
          <label className="label" htmlFor="f-fault">
            Fault injection
          </label>
          <select
            id="f-fault"
            value={form.fault}
            disabled={running}
            onChange={(e) => onChange({ fault: e.target.value })}
          >
            {FAULTS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        </div>
        <div className="ctrl">
          <button type="button" className="btn primary" disabled={running} onClick={onSubmit}>
            {running ? 'Running…' : 'Submit request'}
          </button>
          <button type="button" className="btn" disabled={running} onClick={onReset}>
            Reset
          </button>
        </div>
      </div>
    </div>
  )
}
