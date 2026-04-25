import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, Users, Plus, Filter, Search, MoreHorizontal, PieChart as PieChartIcon } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const AdminDashboard = () => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [insights, setInsights] = useState(null);

  const sortPatients = (data) => {
    const priority = { 'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Pending': 4 };
    return [...data].sort((a, b) => {
      const triageCmp = (priority[a.triage_level] ?? 4) - (priority[b.triage_level] ?? 4);
      if (triageCmp !== 0) return triageCmp;
      return (b.risk_score ?? 0) - (a.risk_score ?? 0);
    });
  };

  useEffect(() => {
    fetch('http://localhost:8000/api/patients')
      .then(res => res.json())
      .then(data => {
        if(data && data.length > 0) {
          setPatients(sortPatients(data));
        }
      })
      .catch(err => console.log('Using mock data for demo'));

    fetch('http://localhost:8000/api/patients/insights')
      .then(res => res.json())
      .then(data => setInsights(data))
      .catch(() => setInsights(null));
  }, []);

  const updateStatus = async (patientId, status) => {
    try {
      const response = await fetch(`http://localhost:8000/api/patients/${patientId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (!response.ok) return;
      const updatedPatient = await response.json();
      const updatedPatients = patients.map((p) => (p.id === updatedPatient.id ? updatedPatient : p));
      setPatients(sortPatients(updatedPatients));
      setSelectedPatient(updatedPatient);
      setInsights((prev) => {
        if (!prev) return prev;
        const previousStatus = selectedPatient?.status || "Waiting";
        if (previousStatus === status) return prev;
        return {
          ...prev,
          status_distribution: {
            ...prev.status_distribution,
            [previousStatus]: Math.max(0, (prev.status_distribution?.[previousStatus] || 0) - 1),
            [status]: (prev.status_distribution?.[status] || 0) + 1,
          },
        };
      });
    } catch {
      // ignore for now
    }
  };

  return (
    <div className="flex flex-col space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold outfit-font tracking-tight">Admin Insights</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Real-time statistics and patient triaging</p>
        </div>
        <div className="flex gap-3">
           <button className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-medium shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
             <Filter size={16} /> Filters
           </button>
           <button className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-sm font-medium shadow-lg shadow-brand-500/20 transition-colors">
             <Plus size={16} /> Export Report
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Tableau & Stats */}
        <div className="lg:col-span-2 flex flex-col space-y-6 lg:sticky lg:top-4 lg:self-start">
           {/* Top Stats */}
           <div className="grid grid-cols-2 gap-4">
              <StatCard title="Total Intakes" value={insights?.total_patients ?? patients.length} trend={`${insights?.high_risk_ratio_percent ?? 0}% high risk`} icon={<Users size={20} />} color="text-blue-500" />
              <StatCard title="Critical Cases" value={insights?.high_risk_count ?? patients.filter(p=>p.triage_level==='High'||p.triage_level==='Critical').length} trend={`Avg risk ${insights?.average_risk_score ?? 0}/100`} icon={<Activity size={20} />} color="text-red-500" />
           </div>
           
           {/* Dynamic Area: Analytics Chart OR Patient Details */}
           <div className="min-h-[500px] glass-card overflow-hidden flex flex-col relative group pb-4">
              {selectedPatient ? (
                 <div className="flex-1 flex flex-col pt-2 animate-in slide-in-from-right-4 duration-300">
                    <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center bg-brand-50/50 dark:bg-brand-900/10">
                       <div>
                          <p className="text-xs text-brand-600 dark:text-brand-400 font-bold tracking-widest uppercase mb-1">Intake Summary</p>
                          <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                             {selectedPatient.patient_name}
                             <span className="text-sm font-normal text-gray-500">({selectedPatient.age}y, {selectedPatient.weight})</span>
                          </h3>
                       </div>
                       <button onClick={() => setSelectedPatient(null)} className="px-3 py-1.5 bg-white dark:bg-gray-800 text-xs font-semibold rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                          Close Notes
                       </button>
                    </div>
                    <div className="p-6 flex-1 overflow-y-auto space-y-6">
                       <div className="grid grid-cols-2 gap-4 text-sm bg-gray-50 dark:bg-gray-900 p-4 rounded-xl border border-gray-100 dark:border-gray-800/50">
                           <div><span className="text-gray-500 block mb-1">Phone Number</span><span className="font-medium">{selectedPatient.phone}</span></div>
                           <div><span className="text-gray-500 block mb-1">Triage Assigned</span>
                                <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${selectedPatient.triage_level === 'Critical' || selectedPatient.triage_level === 'High' ? 'bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400' : 'bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400'}`}>
                                  {selectedPatient.triage_level}
                                </span>
                           </div>
                           <div><span className="text-gray-500 block mb-1">Risk Score</span><span className="font-semibold">{selectedPatient.risk_score ?? 0}/100</span></div>
                           <div><span className="text-gray-500 block mb-1">Workflow Status</span><span className="font-semibold">{selectedPatient.status || "Waiting"}</span></div>
                       </div>
                       <div className="flex flex-wrap gap-2">
                          <button onClick={() => updateStatus(selectedPatient.id, "In Review")} className="px-3 py-1.5 text-xs rounded-lg border border-blue-200 text-blue-600 hover:bg-blue-50 dark:border-blue-500/30 dark:text-blue-400 dark:hover:bg-blue-500/10">Mark In Review</button>
                          <button onClick={() => updateStatus(selectedPatient.id, "Escalated")} className="px-3 py-1.5 text-xs rounded-lg border border-red-200 text-red-600 hover:bg-red-50 dark:border-red-500/30 dark:text-red-400 dark:hover:bg-red-500/10">Escalate</button>
                          <button onClick={() => updateStatus(selectedPatient.id, "Closed")} className="px-3 py-1.5 text-xs rounded-lg border border-emerald-200 text-emerald-600 hover:bg-emerald-50 dark:border-emerald-500/30 dark:text-emerald-400 dark:hover:bg-emerald-500/10">Close Case</button>
                       </div>
                       
                       <div>
                           <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-2 border-l-4 border-brand-500 pl-2">Chief Complaint</h4>
                           <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap bg-white/50 dark:bg-gray-950/50 p-4 rounded-xl border border-gray-100 dark:border-gray-800 shadow-sm">
                             {selectedPatient.chief_complaint || "Not recorded."}
                           </p>
                       </div>
                       
                       <div>
                           <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-2 border-l-4 border-emerald-500 pl-2">History of Present Illness / Notes</h4>
                           <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap bg-white/50 dark:bg-gray-950/50 p-4 rounded-xl border border-gray-100 dark:border-gray-800 shadow-sm">
                             {selectedPatient.history_of_present_illness || "Not recorded or conversation pending."}
                           </p>
                       </div>
                       <div>
                           <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-2 border-l-4 border-red-500 pl-2">Risk Factors</h4>
                           <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap bg-white/50 dark:bg-gray-950/50 p-4 rounded-xl border border-gray-100 dark:border-gray-800 shadow-sm">
                             {Array.isArray(selectedPatient.risk_reasons) && selectedPatient.risk_reasons.length > 0
                              ? selectedPatient.risk_reasons.join(" ")
                              : "No explicit risk factors recorded."}
                           </p>
                       </div>
                    </div>
                 </div>
              ) : (
                 <>
                    <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center bg-white/50 dark:bg-gray-900/50">
                       <h3 className="font-semibold text-sm flex items-center gap-2">
                          <PieChartIcon size={16} className="text-brand-500" />
                          Patient Triage Distribution
                       </h3>
                       <div className="px-2 py-1 bg-brand-100 dark:bg-brand-500/20 text-brand-700 dark:text-brand-400 text-[10px] font-bold rounded uppercase">Real-time Data</div>
                    </div>
                    <div className="flex-1 relative w-full h-full p-2 flex items-center justify-center">
                        {patients.length > 0 ? (
                          <ResponsiveContainer width="100%" height={400}>
                            <PieChart>
                               <Pie
                                 data={[
                                   { name: 'Critical', value: patients.filter(p => p.triage_level === 'Critical').length, color: '#ef4444' },
                                   { name: 'High', value: patients.filter(p => p.triage_level === 'High').length, color: '#f97316' },
                                   { name: 'Medium', value: patients.filter(p => p.triage_level === 'Medium').length, color: '#eab308' },
                                   { name: 'Low', value: patients.filter(p => p.triage_level === 'Low').length, color: '#22c55e' }
                                 ].filter(d => d.value > 0)}
                                 cx="50%"
                                 cy="50%"
                                 innerRadius={70}
                                 outerRadius={100}
                                 paddingAngle={5}
                                 dataKey="value"
                               >
                                 {[
                                   { name: 'Critical', value: patients.filter(p => p.triage_level === 'Critical').length, color: '#ef4444' },
                                   { name: 'High', value: patients.filter(p => p.triage_level === 'High').length, color: '#f97316' },
                                   { name: 'Medium', value: patients.filter(p => p.triage_level === 'Medium').length, color: '#eab308' },
                                   { name: 'Low', value: patients.filter(p => p.triage_level === 'Low').length, color: '#22c55e' }
                                 ].filter(d => d.value > 0).map((entry, index) => (
                                   <Cell key={`cell-${index}`} fill={entry.color} />
                                 ))}
                               </Pie>
                               <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', background: '#fff', color: '#000' }} />
                               <Legend verticalAlign="bottom" height={36}/>
                            </PieChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="text-gray-400 text-sm">No patient data available.</div>
                        )}
                    </div>
                 </>
              )}
           </div>
        </div>

        {/* Right Column: High Risk Patients List */}
        <div className="glass-card flex flex-col overflow-hidden h-[600px] lg:h-auto">
           <div className="p-5 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center bg-white/50 dark:bg-gray-900/50">
              <h3 className="font-semibold text-gray-900 dark:text-white">Recent Intakes</h3>
              <Search size={16} className="text-gray-400" />
           </div>
           <div className="flex-1 overflow-y-auto p-2 space-y-2">
              {patients.length === 0 ? <div className="p-4 text-center text-sm text-gray-500">No recent intakes.</div> : patients.map(p => (
                <div key={p.id} onClick={() => setSelectedPatient(p)} className={`p-4 rounded-xl transition-colors border cursor-pointer flex flex-col gap-2 ${selectedPatient?.id === p.id ? 'bg-brand-50/50 dark:bg-brand-900/10 border-brand-200 dark:border-brand-500/30' : 'hover:bg-gray-50 dark:hover:bg-gray-800 border-transparent hover:border-gray-200 dark:hover:border-gray-700'}`}>
                   <div className="flex justify-between items-start">
                      <div className="font-medium text-sm">{p.patient_name} <span className="text-gray-400 font-normal">({p.age}y)</span></div>
                      <div className={`text-[10px] uppercase tracking-wider font-bold px-2 py-1 rounded ${
                         p.triage_level === 'High' || p.triage_level === 'Critical' ? 'bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400' :
                         p.triage_level === 'Medium' ? 'bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400' :
                         'bg-green-100 text-green-600 dark:bg-green-500/20 dark:text-green-400'
                      }`}>
                        {p.triage_level || 'Pending'}
                      </div>
                   </div>
                   <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{p.chief_complaint || 'No complaint listed'}</p>
                   <div className="flex items-center justify-between mt-1">
                    <div className="text-[10px] text-gray-400">{p.id}</div>
                    <div className="text-[10px] text-gray-500">Risk {(p.risk_score ?? 0)}/100 • {p.status || "Waiting"}</div>
                   </div>
                </div>
              ))}
           </div>
           <div className="p-3 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50 text-center">
             <button className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:text-brand-500 transition-colors">View All Patients</button>
           </div>
        </div>

      </div>
    </div>
  );
};

const StatCard = ({ title, value, trend, icon, color }) => (
  <div className="glass-card p-5 flex flex-col justify-between">
    <div className="flex justify-between items-start mb-4">
      <div className={`p-2 rounded-lg bg-gray-100 dark:bg-gray-800 ${color}`}>
        {icon}
      </div>
      <MoreHorizontal size={16} className="text-gray-400" />
    </div>
    <div>
      <h4 className="text-gray-500 dark:text-gray-400 text-sm mb-1">{title}</h4>
      <div className="flex items-end gap-3">
         <span className="text-3xl font-bold outfit-font text-gray-900 dark:text-white leading-none">{value}</span>
         <span className="text-xs font-medium text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10 px-1.5 py-0.5 rounded mb-1">{trend}</span>
      </div>
    </div>
  </div>
);

export default AdminDashboard;
