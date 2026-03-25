import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
// Placeholders for now
import AuthPage from './pages/AuthPage';
import RoleSelectionPage from './pages/RoleSelectionPage';
import DonorRegistrationPage from './pages/DonorRegistrationPage';
import RecipientDashboardPage from './pages/RecipientDashboardPage';

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />
      <main className="grow container mx-auto px-4 py-8 max-w-5xl">
        <Routes>
          <Route path="/" element={<AuthPage />} />
          <Route path="/role" element={<RoleSelectionPage />} />
          <Route path="/donor" element={<DonorRegistrationPage />} />
          <Route path="/recipient" element={<RecipientDashboardPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
