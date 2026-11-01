import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'

const inputCls = 'rounded-lg border border-slate-300 px-3 py-2 text-sm'
const errMsg = (err, fallback) => err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || fallback

export default function CompanyDetailPage() {
  const { id } = useParams()
  const [company, setCompany] = useState(null)
  const [yearId, setYearId] = useState(null)
  const [roles, setRoles] = useState([])
  const { user } = useAuth()
  const { push } = useToast()
  const canManage = user?.role === 'PCELL_MEMBER' || user?.role === 'TPO'
  const [yearDraft, setYearDraft] = useState({ visit_year: '', notes: '' })
  const [roleDraft, setRoleDraft] = useState({ title: '', eligibility: '', selection_info: '' })

  const loadCompany = (selectId) =>
    api.get(`/api/companies/${id}/detail`).then((r) => {
      setCompany(r.data)
      setYearId((cur) => selectId ?? cur ?? r.data.years?.[0]?.id ?? null)
    })

  const loadRoles = (yid) => api.get(`/api/company-years/${yid}/roles`).then((r) => setRoles(r.data))

  useEffect(() => {
    loadCompany()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  useEffect(() => {
    if (yearId) loadRoles(yearId)
  }, [yearId])

  const addYear = async (e) => {
    e.preventDefault()
    try {
      const { data } = await api.post(`/api/companies/${id}/years`, {
        visit_year: Number(yearDraft.visit_year),
        notes: yearDraft.notes || null,
      })
      setYearDraft({ visit_year: '', notes: '' })
      push('Visit year added', 'success')
      loadCompany(data.id)
    } catch (err) {
      push(errMsg(err, 'Could not add visit year'), 'error')
    }
  }

  const addRole = async (e) => {
    e.preventDefault()
    try {
      await api.post(`/api/company-years/${yearId}/roles`, {
        title: roleDraft.title,
        eligibility: roleDraft.eligibility || null,
        selection_info: roleDraft.selection_info || null,
        skill_ids: [],
      })
      setRoleDraft({ title: '', eligibility: '', selection_info: '' })
      push('Role added', 'success')
      loadRoles(yearId)
    } catch (err) {
      push(errMsg(err, 'Could not add role'), 'error')
    }
  }

  if (!company) return <p className="text-slate-500">Loading company...</p>

  const selectedYear = company.years?.find((y) => y.id === yearId)

  return (
    <div className="space-y-6">
      <div className="hover-grow-soft bg-white rounded-xl border p-6">
        <h2 className="text-2xl font-semibold">{company.name}</h2>
        <p className="text-slate-500">{company.industry}</p>
        <p className="mt-3 text-slate-700">{company.description}</p>
        {company.website && (
          <a href={company.website} className="text-indigo-600 text-sm mt-2 inline-block" target="_blank" rel="noreferrer">
            Website
          </a>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {company.years?.map((y) => (
          <button
            key={y.id}
            type="button"
            onClick={() => setYearId(y.id)}
            className={`px-4 py-2 rounded-lg text-sm border ${
              yearId === y.id ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white'
            }`}
          >
            {y.visit_year}
          </button>
        ))}
      </div>

      {canManage && (
        <form onSubmit={addYear} className="bg-white rounded-xl border p-5 flex flex-wrap gap-3 items-end">
          <div>
            <p className="text-sm font-medium mb-1">Add visit year</p>
            <input
              type="number"
              min={2000}
              max={2100}
              placeholder="e.g. 2026"
              className={`${inputCls} w-32`}
              value={yearDraft.visit_year}
              onChange={(e) => setYearDraft({ ...yearDraft, visit_year: e.target.value })}
              required
            />
          </div>
          <input
            placeholder="Notes (optional)"
            className={`${inputCls} flex-1 min-w-[12rem]`}
            value={yearDraft.notes}
            onChange={(e) => setYearDraft({ ...yearDraft, notes: e.target.value })}
          />
          <button type="submit" className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm">
            Add year
          </button>
        </form>
      )}

      {company.years?.length === 0 && !canManage && (
        <p className="text-sm text-slate-500">No visit years have been added for this company yet.</p>
      )}

      {selectedYear && (
        <div className="bg-white rounded-xl border p-6">
          <h3 className="font-semibold text-lg">{company.name} → {selectedYear.visit_year}</h3>
          <p className="text-sm text-slate-500 mt-1">Roles / positions offered</p>
          <div className="mt-4 grid md:grid-cols-2 gap-3">
            {roles.map((role) => (
              <Link
                key={role.id}
                to={`/questions?company_id=${company.id}&company_year_id=${yearId}&role_id=${role.id}`}
                className="hover-grow rounded-lg border p-4 hover:border-indigo-300"
              >
                <p className="font-medium">{role.title}</p>
                <p className="text-xs text-slate-500 mt-1">{role.eligibility || 'View interview questions'}</p>
              </Link>
            ))}
            {roles.length === 0 && <p className="text-sm text-slate-500">No roles added for this year yet.</p>}
          </div>
          {canManage && (
            <form onSubmit={addRole} className="mt-5 border-t pt-4 grid md:grid-cols-3 gap-3 items-end">
              <input
                placeholder="Role title (e.g. Software Engineer)"
                className={inputCls}
                value={roleDraft.title}
                onChange={(e) => setRoleDraft({ ...roleDraft, title: e.target.value })}
                required
              />
              <input
                placeholder="Eligibility (optional)"
                className={inputCls}
                value={roleDraft.eligibility}
                onChange={(e) => setRoleDraft({ ...roleDraft, eligibility: e.target.value })}
              />
              <input
                placeholder="Selection process (optional)"
                className={inputCls}
                value={roleDraft.selection_info}
                onChange={(e) => setRoleDraft({ ...roleDraft, selection_info: e.target.value })}
              />
              <button type="submit" className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm md:col-span-3 md:w-fit">
                Add role
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  )
}
