import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import RecruiterDashboard from './pages/RecruiterDashboard';
import RecruiterDashboardLight from './pages/RecruiterDashboardLight';
import UploadResume from './pages/UploadResume';
import BulkUpload from './pages/BulkUpload';
import LiveAssessment from './pages/LiveAssessment';
import CompareCandidates from './pages/CompareCandidates';
import CandidateOverview from './pages/CandidateOverview';
import CandidateAssessment from './pages/CandidateAssessment';
import AllCandidates from './pages/AllCandidates';
import AssessmentLink from './pages/AssessmentLink';
import LiveMetrics from './pages/LiveMetrics';
import SkillReports from './pages/SkillReports';
import SystemSettings from './pages/SystemSettings';
import Login from './pages/Login';
import Register from './pages/Register';
import './index.css';

/**
 * Protected Route Component
 * Redirects to login if user is not authenticated.
 * Saves current path to redirect back after login.
 */
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading, setRedirectAfterLogin } = useAuth();
  const location = useLocation();

  // Show loading while checking auth state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Save the path user was trying to access
    setRedirectAfterLogin(location.pathname);
    return <Navigate to="/login" replace />;
  }

  return children;
};

/**
 * Public Route Component
 * Redirects to dashboard if already logged in.
 */
const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading while checking auth state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

/**
 * App Routes Component (needs to be inside Router)
 */
function AppRoutes() {
  return (
    <Routes>
      {/* Auth Routes - Public */}
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

      {/* Main Dashboard - Entry Point */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<ProtectedRoute><RecruiterDashboardLight /></ProtectedRoute>} />
      <Route path="/dashboard-dark" element={<ProtectedRoute><RecruiterDashboard /></ProtectedRoute>} />

      {/* Candidate Assessment Route - Standalone fullscreen view (Public for candidates) */}
      <Route path="/assessment/:token" element={<CandidateAssessment />} />

      {/* All other pages - Protected with top nav */}
      <Route path="/upload-resume" element={<ProtectedRoute><UploadResume /></ProtectedRoute>} />
      <Route path="/bulk-upload" element={<ProtectedRoute><BulkUpload /></ProtectedRoute>} />
      <Route path="/live-assessment" element={<ProtectedRoute><LiveAssessment /></ProtectedRoute>} />
      <Route path="/compare-candidates" element={<ProtectedRoute><CompareCandidates /></ProtectedRoute>} />
      <Route path="/candidate/:id" element={<ProtectedRoute><CandidateOverview /></ProtectedRoute>} />
      <Route path="/candidates" element={<ProtectedRoute><AllCandidates /></ProtectedRoute>} />
      <Route path="/assessment-link" element={<ProtectedRoute><AssessmentLink /></ProtectedRoute>} />
      <Route path="/live-metrics" element={<ProtectedRoute><LiveMetrics /></ProtectedRoute>} />
      <Route path="/skill-reports" element={<ProtectedRoute><SkillReports /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><SystemSettings /></ProtectedRoute>} />

      {/* Catch all - redirect to login */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;
