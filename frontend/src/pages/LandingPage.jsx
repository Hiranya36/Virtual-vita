import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Bot, HeartPulse, Activity, ShieldCheck, ArrowRight, ActivitySquare, CheckCircle2 } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-50 overflow-hidden relative">
      {/* Background Gradients (Vercel/Stripe inspired) */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-brand-500/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-500/20 blur-[120px] pointer-events-none" />
      
      {/* Navbar */}
      <nav className="fixed w-full z-50 glass border-b-0 border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-brand-500/30">
              <HeartPulse size={24} />
            </div>
            <span className="font-bold text-xl outfit-font tracking-tight">Virtual Vita</span>
          </div>
          <div className="hidden md:flex items-center gap-8 font-medium">
            <a href="#features" className="text-sm text-gray-600 dark:text-gray-300 hover:text-brand-500 transition-colors">Features</a>
            <a href="#solutions" className="text-sm text-gray-600 dark:text-gray-300 hover:text-brand-500 transition-colors">Solutions</a>
            <a href="#analytics" className="text-sm text-gray-600 dark:text-gray-300 hover:text-brand-500 transition-colors">Analytics</a>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => navigate('/login')}
              className="px-5 py-2.5 text-sm font-medium rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all shadow-sm"
            >
              Admin Login
            </button>
            <button 
              onClick={() => navigate('/dashboard/user')}
              className="px-5 py-2.5 text-sm font-medium rounded-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:bg-gray-800 dark:hover:bg-gray-100 transition-all shadow-lg flex items-center gap-2"
            >
              Get Started <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="pt-32 pb-20 px-6 max-w-7xl mx-auto relative z-10">
        <div className="text-center max-w-4xl mx-auto mt-16 md:mt-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
             <span className="px-4 py-1.5 rounded-full border border-brand-500/30 bg-brand-500/10 text-brand-600 dark:text-brand-400 text-xs font-semibold uppercase tracking-wider mb-6 inline-block">
               Announcing AI Analytics 2.0
             </span>
             <h1 className="text-5xl md:text-7xl font-extrabold outfit-font tracking-tight leading-[1.1] mb-6">
                The Healthcare OS for <br />
                <span className="text-gradient">Next-Gen Intake.</span>
             </h1>
             <p className="text-lg md:text-xl text-gray-600 dark:text-gray-400 mb-10 max-w-2xl mx-auto font-light leading-relaxed">
               Virtual Vita is an empathetic AI receptionist and advanced analytics platform designed to dramatically reduce clinical overhead while scaling patient care.
             </p>
          </motion.div>
          
          <motion.div 
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <button 
              onClick={() => navigate('/dashboard/user')}
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold rounded-full bg-brand-600 hover:bg-brand-500 text-white transition-all shadow-xl shadow-brand-500/25 flex items-center justify-center gap-2"
            >
              Try the AI Demo <ArrowRight size={18} />
            </button>
            <button className="w-full sm:w-auto px-8 py-4 text-base font-medium rounded-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all shadow-sm">
              Contact Sales
            </button>
          </motion.div>
        </div>

        {/* Dashboard Mockup Video/Image Frame */}
        <motion.div 
          className="mt-20 mx-auto max-w-5xl relative rounded-2xl md:rounded-[2rem] p-2 bg-gradient-to-b from-gray-200 to-gray-100 dark:from-gray-800 dark:to-gray-900 shadow-2xl glass"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          <div className="absolute top-3 left-4 flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-400/80"></div>
            <div className="w-3 h-3 rounded-full bg-amber-400/80"></div>
            <div className="w-3 h-3 rounded-full bg-green-400/80"></div>
          </div>
          <div className="bg-white dark:bg-[#0B0F19] w-full h-[300px] md:h-[500px] rounded-xl md:rounded-[1.5rem] overflow-hidden border border-gray-200/50 dark:border-white/5 flex flex-col pt-10">
            <div className="flex-1 border-t border-gray-100 dark:border-gray-800 flex bg-gray-50/50 dark:bg-[#060913]">
              {/* Fake Sidebar */}
              <div className="w-48 border-r border-gray-100 dark:border-gray-800 hidden md:block p-4 space-y-4">
                 <div className="h-6 w-24 bg-gray-200 dark:bg-gray-800 rounded mb-8 animate-pulse"></div>
                 <div className="h-4 w-full bg-gray-200 dark:bg-gray-800 rounded opacity-50"></div>
                 <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-800 rounded opacity-50"></div>
                 <div className="h-4 w-5/6 bg-gray-200 dark:bg-gray-800 rounded opacity-50"></div>
              </div>
              {/* Fake Content area */}
              <div className="flex-1 p-6 md:p-10">
                 <div className="h-8 w-48 bg-gray-200 dark:bg-gray-800 rounded mb-8"></div>
                 <div className="grid grid-cols-3 gap-6 mb-8">
                    <div className="h-24 bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse"></div>
                    <div className="h-24 bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse delay-75"></div>
                    <div className="h-24 bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse delay-150"></div>
                 </div>
                 <div className="h-48 bg-brand-500/10 dark:bg-brand-500/5 rounded-xl border border-brand-500/20"></div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Feature Grid */}
        <div className="mt-32 max-w-6xl mx-auto py-10" id="features">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<Bot size={28} className="text-brand-500" />}
              title="Conversational AI"
              desc="Natural language patient intake mimicking a real nurse interaction. Translates multiple languages."
            />
            <FeatureCard 
              icon={<ActivitySquare size={28} className="text-indigo-500" />}
              title="Tableau Analytics"
              desc="Embedded high-performance interactive visual dashboards for admins and patients."
            />
            <FeatureCard 
              icon={<ShieldCheck size={28} className="text-emerald-500" />}
              title="Enterprise Grade"
              desc="Secure patient tracking, triage categorization, and role-based access controls."
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950/50 mt-20 py-12">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-500 text-sm">
          <p>© 2026 Virtual Vita Healthcare Inc. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

const FeatureCard = ({ icon, title, desc }) => (
  <div className="p-8 rounded-3xl glass-card transition-transform hover:-translate-y-1 duration-300">
    <div className="w-14 h-14 rounded-2xl bg-gray-50 dark:bg-gray-800 flex items-center justify-center mb-6 shadow-sm border border-gray-100 dark:border-gray-700">
      {icon}
    </div>
    <h3 className="text-xl font-bold outfit-font mb-3">{title}</h3>
    <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">{desc}</p>
  </div>
);

export default LandingPage;
