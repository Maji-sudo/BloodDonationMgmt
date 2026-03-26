import { Droplet, LogOut, User, LayoutDashboard, ListFilter, Home, Bell } from 'lucide-react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState, useEffect } from 'react';
import { notificationApi } from '../services/api';

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [notifications, setNotifications] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    if (isAuthenticated && user?.email) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 10000); // Check every 10s
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, user]);

  const fetchNotifications = async () => {
    try {
      const data = await notificationApi.getAll(user.email);
      setNotifications(data);
    } catch(err) {
      console.error(err);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const markAsRead = async (id) => {
    try {
      await notificationApi.markAsRead(id);
      fetchNotifications();
    } catch(err) {}
  };

  const markAllAsRead = async () => {
    try {
      await notificationApi.markAllAsRead(user.email);
      fetchNotifications();
    } catch(err) {}
  };

  const isActive = (path) => location.pathname === path;

  const unreadCount = notifications.filter(n => !n.is_read).length;

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
              
              {/* Notifications Dropdown */}
              <div className="relative">
                <button 
                  onClick={() => setShowDropdown(!showDropdown)}
                  className="relative p-2 rounded-full hover:bg-white/10 transition-colors"
                >
                  <Bell className="w-5 h-5" />
                  {unreadCount > 0 && (
                    <span className="absolute top-1 right-1.5 w-2 h-2 bg-red-500 rounded-full animate-pulse border border-white"></span>
                  )}
                </button>

                {showDropdown && (
                  <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden text-gray-800 z-50">
                    <div className="flex justify-between items-center p-3 border-b border-gray-50 bg-gray-50/50">
                      <h3 className="font-bold text-sm">Notifications</h3>
                      {unreadCount > 0 && (
                        <button onClick={markAllAsRead} className="text-xs text-primary hover:underline">
                          Mark all read
                        </button>
                      )}
                    </div>
                    <div className="max-h-80 overflow-y-auto">
                      {notifications.length === 0 ? (
                        <div className="p-4 text-center text-sm text-gray-500">No notifications</div>
                      ) : (
                        notifications.map((n) => (
                          <div 
                            key={n.id} 
                            onClick={() => markAsRead(n.id)}
                            className={`p-3 border-b border-gray-50 text-sm cursor-pointer hover:bg-gray-50 transition-colors ${!n.is_read ? 'bg-blue-50/30' : ''}`}
                          >
                            <div className="flex justify-between items-start gap-2 mb-1">
                              <span className={`font-semibold ${n.type === 'warning' ? 'text-orange-600' : 'text-gray-900'}`}>{n.title}</span>
                              {!n.is_read && <span className="w-2 h-2 bg-primary rounded-full mt-1.5 shrink-0"></span>}
                            </div>
                            <p className="text-gray-600 text-xs">{n.message}</p>
                            <span className="text-[10px] text-gray-400 mt-2 block">
                              {new Date(n.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>

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
