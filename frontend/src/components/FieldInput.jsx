const inputCls = 'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm'

// One input for a profile / registration-form field. `value` is always a string.
export default function FieldInput({ field, value, onChange, disabled = false, required = false }) {
  const common = { className: `${inputCls} ${disabled ? 'bg-slate-50' : ''}`, value, disabled, required }
  const set = (e) => onChange(e.target.value)

  switch (field.type) {
    case 'textarea':
      return <textarea {...common} rows={3} onChange={set} />
    case 'select':
    case 'yesno': {
      const options = field.type === 'yesno' ? ['Yes', 'No'] : field.options || []
      return (
        <select {...common} onChange={set}>
          <option value="">Select...</option>
          {options.map((o) => (
            <option key={o}>{o}</option>
          ))}
        </select>
      )
    }
    case 'number':
      return <input {...common} type="number" min={field.min} max={field.max} step={field.step || '1'} onChange={set} />
    case 'date':
      return <input {...common} type="date" onChange={set} />
    case 'url':
      return <input {...common} type="url" placeholder="https://" onChange={set} />
    default:
      return <input {...common} type="text" onChange={set} />
  }
}
