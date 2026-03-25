import { Droplet, LogOut, User, LayoutDashboard, ListFilter, Home } from 'lucide-react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-primary text-white shadow-md sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-2 text-xl font-bold tracking-tight hover:opacity-90 transition-opacity">
          <Droplet className="w-6 h-6 fill-white" />
          <span>LifeBlood</span>
        </Link>

        {/* Navigation Links */}
        {isAuthenticated && (
          <div className="hidden lg:flex items-center gap-1 bg-white/10 p-1 rounded-xl border border-white/10">
            <Link 
              to="/role" 
              className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${isActive('/role') ? 'bg-white text-primary' : 'hover:bg-white/10'}`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </Link>
            <Link 
              to="/requests" 
              className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${isActive('/requests') ? 'bg-white text-primary' : 'hover:bg-white/10'}`}
            >
              <ListFilter className="w-4 h-4" />
              Blood Feed
            </Link>
          </div>
        )}

        {/* User Menu */}
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-1.5 bg-white/10 px-3 py-1.5 rounded-full text-xs font-semibold border border-white/20">
                <User className="w-3.5 h-3.5" />
                <span>{user.user_name || user.email}</span>
              </div>
              <button 
                onClick={handleLogout}
                className="flex items-center gap-1.5 text-sm hover:text-red-200 transition-colors bg-red-600 px-3 py-1.5 rounded-lg border border-red-500 shadow-sm"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Sign Out</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-4">
               <Link to="/" className="text-sm font-medium flex items-center gap-1 hover:underline">
                 <Home className="w-4 h-4" />
                 Home
               </Link>
            </div>
          )}
        </div>
      </div>
      
      {/* Mobile Nav */}
      {isAuthenticated && (
        <div className="lg:hidden bg-primary-dark border-t border-white/5 px-4 py-2 flex justify-around">
           <Link to="/role" className={`flex flex-col items-center gap-1 text-[10px] ${isActive('/role') ? 'text-white' : 'text-white/60'}`}>
             <LayoutDashboard className="w-5 h-5" />
             Dashboard
           </Link>
           <Link to="/requests" className={`flex flex-col items-center gap-1 text-[10px] ${isActive('/requests') ? 'text-white' : 'text-white/60'}`}>
             <ListFilter className="w-5 h-5" />
             Feed
           </Link>
        </div>
      )}
    </nav>
  );
}
