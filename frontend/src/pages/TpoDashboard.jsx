import { useEffect, useState } from 'react'
import api from '../services/api'
import { useToast } from '../components/Toast'
import StatsCards from '../components/StatsCards'

export default function TpoDashboard() {
  const [members, setMembers] = useState([])
  const { push } = useToast()

  const load = () => api.get('/api/tpo/pcell-members').then((r) => setMembers(r.data.items))

  useEffect(() => {
    load()
  }, [])

  const act = async (id, action) => {
    await api.post(`/api/tpo/pcell-members/${id}/${action}`)
    push(`Member ${action}d`, 'success')
    load()
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">TPO dashboard</h2>
      <StatsCards editable />
      <p className="text-sm text-slate-500">Manage PCELL member accounts and review platform activity.</p>
      <div className="bg-white border rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="p-3">Name</th>
              <th className="p-3">Email</th>
              <th className="p-3">Status</th>
              <th className="p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.id} className="border-t">
                <td className="p-3">{m.full_name}</td>
                <td className="p-3">{m.email}</td>
                <td className="p-3">{m.status}</td>
                <td className="p-3 space-x-2">
                  {m.status === 'PENDING' && (
                    <>
                      <button type="button" className="text-emerald-600" onClick={() => act(m.id, 'approve')}>
                        Approve
                      </button>
                      <button type="button" className="text-red-600" onClick={() => act(m.id, 'reject')}>
                        Reject
                      </button>
                    </>
                  )}
                  {m.status === 'ACTIVE' && (
                    <button type="button" className="text-amber-600" onClick={() => act(m.id, 'suspend')}>
                      Suspend
                    </button>
                  )}
                  {m.status === 'SUSPENDED' && (
                    <button type="button" className="text-indigo-600" onClick={() => act(m.id, 'reactivate')}>
                      Reactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
