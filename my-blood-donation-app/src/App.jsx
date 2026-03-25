import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import AuthPage from './pages/AuthPage';
import RoleSelectionPage from './pages/RoleSelectionPage';
import DonorRegistrationPage from './pages/DonorRegistrationPage';
import RecipientDashboardPage from './pages/RecipientDashboardPage';
import RequestsListPage from './pages/RequestsListPage';
import { useAuth } from './context/AuthContext';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
};

function App() {
  const { isAuthenticated } = useAuth();
  
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />
      <main className="grow container mx-auto px-4 py-8 max-w-5xl">
        <Routes>
          {/* Public Route */}
          <Route path="/" element={isAuthenticated ? <Navigate to="/role" replace /> : <AuthPage />} />
          
          {/* Protected Routes */}
          <Route path="/role" element={<ProtectedRoute><RoleSelectionPage /></ProtectedRoute>} />
          <Route path="/donor" element={<ProtectedRoute><DonorRegistrationPage /></ProtectedRoute>} />
          <Route path="/recipient" element={<ProtectedRoute><RecipientDashboardPage /></ProtectedRoute>} />
          <Route path="/requests" element={<ProtectedRoute><RequestsListPage /></ProtectedRoute>} />
          
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
