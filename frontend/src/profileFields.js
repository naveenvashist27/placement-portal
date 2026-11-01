// Student profile fields, shared by the profile page and the registration form builder/filler.
// type: text | number | url | date | select | yesno | textarea
export const PROFILE_FIELDS = [
  { key: 'full_name', label: 'Full name', type: 'text', required: true },
  { key: 'email', label: 'College email', type: 'text', readOnly: true },
  { key: 'roll_number', label: 'Roll number', type: 'text' },
  { key: 'phone', label: 'Phone', type: 'text' },
  { key: 'personal_email', label: 'Personal email', type: 'text' },
  { key: 'gender', label: 'Gender', type: 'select', options: ['Male', 'Female', 'Other'] },
  { key: 'date_of_birth', label: 'Date of birth', type: 'date' },
  { key: 'city', label: 'City', type: 'text' },
  { key: 'course', label: 'Course (e.g. MBA Tech, B.Tech)', type: 'text' },
  { key: 'branch', label: 'Branch / specialisation', type: 'text' },
  { key: 'batch', label: 'Batch (e.g. 2022-2026)', type: 'text' },
  { key: 'graduation_year', label: 'Passing year', type: 'number', min: 2000, max: 2100 },
  { key: 'current_semester', label: 'Current semester', type: 'number', min: 1, max: 12 },
  { key: 'cgpa', label: 'CGPA (out of 10)', type: 'number', min: 0, max: 10, step: '0.01' },
  { key: 'tenth_percentage', label: '10th class %', type: 'number', min: 0, max: 100, step: '0.01' },
  { key: 'twelfth_percentage', label: '12th class %', type: 'number', min: 0, max: 100, step: '0.01' },
  { key: 'has_atkt', label: 'Currently have an ATKT / backlog?', type: 'yesno' },
  { key: 'atkt_count', label: 'Number of current ATKTs', type: 'number', min: 0, max: 50 },
  { key: 'linkedin_url', label: 'LinkedIn URL', type: 'url' },
  { key: 'github_url', label: 'GitHub URL', type: 'url' },
]

export const FIELD_TYPES = [
  ['text', 'Short text'],
  ['textarea', 'Long text'],
  ['number', 'Number'],
  ['select', 'Dropdown'],
  ['yesno', 'Yes / No'],
  ['url', 'Link'],
  ['date', 'Date'],
]

export const profileField = (key) => PROFILE_FIELDS.find((f) => f.key === key)

// Profile value -> value shown in a form input (booleans become Yes/No).
export function toInputValue(type, value) {
  if (value === null || value === undefined) return ''
  if (type === 'yesno') return value === true || value === 'Yes' ? 'Yes' : 'No'
  return String(value)
}

// Fields counted when showing "profile X% complete" (everything a student can fill, minus the read-only email).
export const COMPLETENESS_KEYS = PROFILE_FIELDS.filter((f) => !f.readOnly && f.key !== 'atkt_count').map((f) => f.key)

export function profileCompleteness(profile) {
  const filled = COMPLETENESS_KEYS.filter((k) => profile[k] !== null && profile[k] !== undefined && profile[k] !== '')
  return Math.round((filled.length / COMPLETENESS_KEYS.length) * 100)
}
