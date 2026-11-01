import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import api from '../services/api'

export default function AnalyticsPage() {
  const [placements, setPlacements] = useState(null)
  const [companies, setCompanies] = useState(null)

  useEffect(() => {
    api.get('/api/analytics/placements').then((r) => setPlacements(r.data))
    api.get('/api/analytics/companies').then((r) => setCompanies(r.data))
  }, [])

  if (!placements || !companies) return <p className="text-slate-500">Loading analytics...</p>

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Placement analytics</h2>
      <div className="grid sm:grid-cols-3 gap-4">
        <div className="hover-grow bg-white border rounded-xl p-4">
          <p className="text-sm text-slate-500">Total placed</p>
          <p className="text-2xl font-semibold">{placements.total_placed}</p>
        </div>
        <div className="hover-grow bg-white border rounded-xl p-4">
          <p className="text-sm text-slate-500">Average package (LPA)</p>
          <p className="text-2xl font-semibold">{placements.average_package_lpa.toFixed(2)}</p>
        </div>
        <div className="hover-grow bg-white border rounded-xl p-4">
          <p className="text-sm text-slate-500">Active companies</p>
          <p className="text-2xl font-semibold">{companies.total_companies}</p>
        </div>
      </div>
      <div className="bg-white border rounded-xl p-4 h-80">
        <p className="font-medium mb-2">Companies by visit year</p>
        <ResponsiveContainer width="100%" height="90%">
          <BarChart data={companies.companies_by_year}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" fill="#4f46e5" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
