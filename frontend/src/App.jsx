import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './components/Toast'
import AppLayout from './layouts/AppLayout'
import { ProtectedRoute } from './routes/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import StudentDashboard from './pages/StudentDashboard'
import CompaniesPage from './pages/CompaniesPage'
import CompanyDetailPage from './pages/CompanyDetailPage'
import QuestionsPage from './pages/QuestionsPage'
import ExperiencesPage from './pages/ExperiencesPage'
import EventsPage from './pages/EventsPage'
import ResumePage from './pages/ResumePage'
import AdminDashboard from './pages/AdminDashboard'
import AdminQuestionReview from './pages/AdminQuestionReview'
import AnalyticsPage from './pages/AnalyticsPage'
import TpoDashboard from './pages/TpoDashboard'
import SearchPage from './pages/SearchPage'
import SimpleListPage from './pages/SimpleListPage'
import NotificationsPage from './pages/NotificationsPage'
import ProfilePage from './pages/ProfilePage'
import StudentsPage from './pages/StudentsPage'
import AuditLogsPage from './pages/AuditLogsPage'
import AdminEventsPage from './pages/AdminEventsPage'
import PlacementsPage from './pages/PlacementsPage'
import CampusGate from './components/CampusGate'
import StudentRequestsPage from './pages/StudentRequestsPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'

export default function App() {
  return (
    <CampusGate>
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route index element={<StudentDashboard />} />
                <Route path="companies" element={<CompaniesPage />} />
                <Route path="companies/:id" element={<CompanyDetailPage />} />
                <Route path="questions" element={<QuestionsPage />} />
                <Route path="experiences" element={<ExperiencesPage />} />
                <Route path="events" element={<EventsPage />} />
                <Route path="resume" element={<ResumePage />} />
                <Route path="topics" element={<SimpleListPage title="Topics" endpoint="/api/topics" />} />
                <Route path="skills" element={<SimpleListPage title="Skills" endpoint="/api/skills" />} />
                <Route path="notifications" element={<NotificationsPage />} />
                <Route path="profile" element={<ProfilePage />} />
                <Route path="search" element={<SearchPage />} />

                <Route element={<ProtectedRoute roles={['PCELL_MEMBER', 'TPO']} />}>
                  <Route path="admin" element={<AdminDashboard />} />
                  <Route path="admin/students" element={<StudentsPage />} />
                  <Route path="admin/requests" element={<StudentRequestsPage />} />
                  <Route path="admin/companies" element={<CompaniesPage />} />
                  <Route path="admin/questions" element={<AdminQuestionReview />} />
                  <Route path="admin/experiences" element={<ExperiencesPage />} />
                  <Route path="admin/registrations" element={<AdminEventsPage section="registrations" />} />
                  <Route path="admin/events" element={<AdminEventsPage section="events" />} />
                  <Route path="admin/placements" element={<PlacementsPage />} />
                  <Route path="admin/analytics" element={<AnalyticsPage />} />
                </Route>

                <Route element={<ProtectedRoute roles={['TPO']} />}>
                  <Route path="tpo" element={<TpoDashboard />} />
                  <Route path="tpo/pcell" element={<TpoDashboard />} />
                  <Route path="tpo/audit" element={<AuditLogsPage />} />
                </Route>
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
    </CampusGate>
  )
}
