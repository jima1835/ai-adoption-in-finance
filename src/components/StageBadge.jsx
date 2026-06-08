import { STAGE_LABELS } from '../data.js'

// Stage as a small uppercase mono pill. Color is driven entirely by the
// `data-stage` attribute → CSS amber ramp (dim → bright = cold → hot).
export default function StageBadge({ stage, size = 'sm' }) {
  return (
    <span className="badge" data-stage={stage} data-size={size}>
      {STAGE_LABELS[stage] || stage}
    </span>
  )
}
