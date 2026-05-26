import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import DashboardPage from './pages/DashboardPage'
import UploadGRPage from './pages/UploadGRPage'
import DraftDetailPage from './pages/DraftDetailPage'
import ExceptionsPage from './pages/ExceptionsPage'
import PostedDocumentsPage from './pages/PostedDocumentsPage'
import ReportsPage from './pages/ReportsPage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadGRPage />} />
          <Route path="/drafts/:requestId" element={<DraftDetailPage />} />
          <Route path="/exceptions" element={<ExceptionsPage />} />
          <Route path="/posted" element={<PostedDocumentsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
