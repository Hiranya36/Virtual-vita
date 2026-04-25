import React, { useEffect, useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Bot, LineChart, LogOut, Moon, Sun, HeartPulse, Menu, X } from 'lucide-react';

const Layout = () => {
  const [darkMode, setDarkMode] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const isAdmin = location.pathname.includes('/admin');

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const navItems = isAdmin 
    ? [
        { label: 'Analytics', icon: <LineChart size={20} />, path: '/dashboard/admin' },
        { label: 'Patient Chat Demo', icon: <Bot size={20} />, path: '/dashboard/user' }
      ]
    : [
        { label: 'AI Intake Nurse', icon: <Bot size={20} />, path: '/dashboard/user' }
      ];

  return (
    <div className="min-h-screen bg-gray-50 flex dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors duration-300 relative">
      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 glass z-40 border-b border-gray-200/50 dark:border-gray-800/50 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
            <HeartPulse size={24} className="text-brand-500" />
            <span className="font-bold text-lg outfit-font">Virtual Vita</span>
        </div>
        <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="p-2">
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-30 w-64 glass-panel border-r border-gray-200/50 dark:border-gray-800/50 flex flex-col transform transition-transform duration-300 md:translate-x-0 ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'} md:static md:block`}>
        <div className="h-20 flex items-center px-6 gap-3 mb-4 hidden md:flex">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
              <HeartPulse size={18} />
            </div>
            <span className="font-bold text-lg outfit-font tracking-tight">Virtual Vita</span>
        </div>

        <div className="flex-1 px-4 py-4 md:py-0 space-y-2 mt-16 md:mt-0">
          <div className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-4 pl-2">Menu</div>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => { navigate(item.path); setMobileMenuOpen(false); }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${isActive ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-200 border border-transparent'}`}
              >
                {item.icon}
                {item.label}
              </button>
            )
          })}
        </div>

        <div className="p-4 border-t border-gray-200/50 dark:border-gray-800/50 space-y-2">
          <button 
            onClick={() => setDarkMode(!darkMode)}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all border border-transparent"
          >
            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </button>
          <button 
            onClick={() => navigate('/login')}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-all border border-transparent"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden pt-16 md:pt-0">
        <div className="flex-1 overflow-y-auto w-full p-4 md:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto h-full flex flex-col">
            <Outlet />
          </div>
        </div>
      </main>
      
      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 bg-black/20 dark:bg-black/40 z-20 md:hidden backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)}></div>
      )}
    </div>
  );
};

export default Layout;
