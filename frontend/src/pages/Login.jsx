import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { HeartPulse, ShieldAlert, ArrowRight, Lock, Mail } from 'lucide-react';

const Login = () => {
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (isRegistering) {
       if (!email || !password) {
          setError('Please enter both email and password.');
          return;
       }
       localStorage.setItem('admin_email', email);
       localStorage.setItem('admin_password', password);
       // Auto-login after registration
       navigate('/dashboard/admin');
    } else {
       const savedEmail = localStorage.getItem('admin_email');
       const savedPassword = localStorage.getItem('admin_password');
       
       if (!savedEmail) {
          setError('No admin account found. Please register first.');
          return;
       }
       
       if (email === savedEmail && password === savedPassword) {
          navigate('/dashboard/admin');
       } else {
          setError('Invalid email or password.');
       }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-6 relative overflow-hidden text-gray-900 dark:text-gray-100">
       {/* Background */}
       <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-[0.03] dark:opacity-[0.05] pointer-events-none"></div>
       <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-500/20 blur-[150px] rounded-full pointer-events-none"></div>

       <motion.div 
         initial={{ opacity: 0, scale: 0.95 }}
         animate={{ opacity: 1, scale: 1 }}
         transition={{ duration: 0.4 }}
         className="w-full max-w-md"
       >
         <div className="flex flex-col items-center mb-8">
           <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-brand-500/30 mb-4 cursor-pointer" onClick={() => navigate('/')}>
             <HeartPulse size={28} />
           </div>
           <h2 className="text-3xl font-extrabold outfit-font text-gray-900 dark:text-white">Admin Portal</h2>
           <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">{isRegistering ? 'Create an admin account' : 'Sign in to your admin account'}</p>
         </div>

         <div className="glass-panel rounded-3xl p-8 relative z-10">
           <div className="flex items-center justify-center gap-2 mb-8 text-brand-600 dark:text-brand-400 font-medium">
             <ShieldAlert size={20} />
             <span>Administrator Access</span>
           </div>

           <form onSubmit={handleSubmit} className="space-y-6">
              <AnimatePresence mode="wait">
                <motion.div
                  key="admin-fields"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-4"
                >
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Email Address</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                        <Mail size={18} />
                      </div>
                      <input 
                        type="email" 
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full bg-white/50 dark:bg-gray-950/50 border border-gray-300 dark:border-gray-700/50 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 rounded-xl pl-10 pr-4 py-3 text-gray-900 dark:text-white text-sm outline-none transition-all shadow-sm"
                        placeholder="admin@virtualvita.com"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Password</label>
                    <div className="relative mt-1">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                        <Lock size={18} />
                      </div>
                      <input 
                        type="password" 
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full bg-white/50 dark:bg-gray-950/50 border border-gray-300 dark:border-gray-700/50 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 rounded-xl pl-10 pr-4 py-3 text-gray-900 dark:text-white text-sm outline-none transition-all shadow-sm"
                        placeholder="••••••••"
                      />
                    </div>
                    {error && <p className="text-red-500 text-xs mt-2 font-medium">{error}</p>}
                  </div>

                  <div className="flex justify-end">
                     <button type="button" onClick={() => { setIsRegistering(!isRegistering); setError(''); }} className="text-xs text-brand-600 dark:text-brand-400 hover:text-brand-500 font-medium transition-colors">
                        {isRegistering ? 'Already have an account? Log in' : 'No account? Register here'}
                     </button>
                  </div>
                </motion.div>
              </AnimatePresence>

              <button 
                type="submit"
                className="w-full py-3.5 px-4 bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-sm font-bold rounded-xl hover:bg-gray-800 dark:hover:bg-gray-100 transition-all flex items-center justify-center gap-2 group shadow-xl"
              >
                {isRegistering ? 'Create Admin Account' : 'Login'}
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </button>
           </form>
         </div>
       </motion.div>
    </div>
  );
};

export default Login;
