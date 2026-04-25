import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Mic, ShieldAlert, Loader2, RefreshCw, Languages } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const UserDashboard = () => {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! I am Virtual Vita, your AI Intake Nurse. Please let me know your Name, Age, Weight, and Phone number before we begin discussing your symptoms.', id: 1 }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [lang, setLang] = useState('en-US'); // 'en-US' or 'te-IN'
  const [sessionId] = useState(`session_${Math.random().toString(36).substring(7)}`);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim()) return;

    if (isListening && recognitionRef.current) {
       recognitionRef.current.stop();
       setIsListening(false);
    }

    const userText = input;
    const newMsg = { sender: 'user', text: userText, id: Date.now() };
    setMessages(prev => [...prev, newMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText, session_id: sessionId }) 
      });
      
      const data = await response.json();
      
      if (data.response) {
         setMessages(prev => [...prev, { sender: 'bot', text: data.response, id: Date.now() }]);
      } else {
         setMessages(prev => [...prev, { sender: 'bot', text: "I'm sorry, my servers seem to be offline right now. Please notify the administrator.", id: Date.now() }]);
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { sender: 'bot', text: "Error connecting to AI Backend. Is the Flask server running?", id: Date.now() }]);
    }
    
    setIsLoading(false);
  };

  const toggleRecording = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = lang;
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onresult = (e) => {
      let finalTranscript = '';
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        if (e.results[i].isFinal) {
          finalTranscript += e.results[i][0].transcript;
        } else {
          finalTranscript += e.results[i][0].transcript; 
        }
      }
      // Assuming user wants to replace/append input. Just overriding for simplicity
      setInput(finalTranscript);
    };

    recognition.onerror = (e) => {
      console.error("Speech reco error: ", e.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  };

  return (
    <div className="h-full flex justify-center pb-4">
      
      {/* Patient Chat Area */}
      <div className="w-full lg:max-w-4xl flex flex-col glass-card overflow-hidden relative shadow-2xl">
         {/* Header */}
         <div className="p-4 md:p-6 border-b border-gray-100 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 flex justify-between items-center backdrop-blur-xl z-10 sticky top-0">
            <div className="flex items-center gap-3">
               <div className="relative">
                  <div className="w-10 h-10 rounded-full bg-brand-100 dark:bg-brand-900 flex items-center justify-center text-brand-600 dark:text-brand-400">
                    <Bot size={22} />
                  </div>
                  <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white dark:border-gray-900 rounded-full"></div>
               </div>
               <div>
                  <h2 className="font-bold text-gray-900 dark:text-white">Virtual Vita Nurse</h2>
                  <p className="text-xs text-green-600 dark:text-green-400 font-medium">Online • Connected</p>
               </div>
            </div>
            <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors" title="Restart Session" onClick={() => window.location.reload()}>
               <RefreshCw size={18} />
            </button>
         </div>

         {/* Messages */}
         <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 bg-gradient-to-b from-transparent to-gray-50/30 dark:to-gray-900/30">
            <AnimatePresence initial={false}>
               {messages.map((msg) => (
                 <motion.div 
                    key={msg.id}
                    initial={{ opacity: 0, y: 10, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    className={`flex gap-3 max-w-[85%] ${msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
                 >
                    <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${msg.sender === 'user' ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-400' : 'bg-brand-100 text-brand-600 dark:bg-brand-900/50 dark:text-brand-400'}`}>
                       {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                    </div>
                    <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                       msg.sender === 'user' 
                         ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900 rounded-tr-sm shadow-md' 
                         : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-tl-sm border border-gray-100 dark:border-gray-700 shadow-sm'
                    }`}>
                       {msg.text}
                    </div>
                 </motion.div>
               ))}
               {isLoading && (
                 <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3 max-w-[85%]">
                    <div className="w-8 h-8 rounded-full flex-shrink-0 bg-brand-100 text-brand-600 dark:bg-brand-900/50 dark:text-brand-400 flex items-center justify-center">
                       <Loader2 size={16} className="animate-spin" />
                    </div>
                    <div className="p-4 rounded-2xl bg-white dark:bg-gray-800 rounded-tl-sm border border-gray-100 dark:border-gray-700 flex items-center gap-1 shadow-sm">
                       <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></span>
                       <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                       <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                    </div>
                 </motion.div>
               )}
               <div ref={messagesEndRef} />
            </AnimatePresence>
         </div>

         {/* Input Area */}
         <div className="p-4 md:p-6 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-t border-gray-100 dark:border-gray-800">
            <form onSubmit={handleSend} className="relative flex items-end gap-2">
               <div className="flex-1 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-2xl flex items-center pl-4 pr-1 py-1 focus-within:ring-2 focus-within:ring-brand-500/50 focus-within:border-brand-500 transition-all shadow-sm">
                  <input 
                     type="text" 
                     value={input}
                     onChange={(e) => setInput(e.target.value)}
                     placeholder="Message Virtual Vita..." 
                     className="w-full bg-transparent border-none outline-none text-sm py-3 text-gray-900 dark:text-white"
                  />
                  <div className="flex items-center gap-1 pr-1">
                     <button
                        type="button"
                        onClick={() => setLang(lang === 'en-US' ? 'te-IN' : 'en-US')}
                        className="p-1.5 px-3 uppercase text-xs font-bold text-gray-500 hover:text-brand-500 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 transition-colors shadow-sm"
                     >
                        {lang.split('-')[0]}
                     </button>
                     <button 
                        type="button" 
                        onClick={toggleRecording}
                        className={`p-2 transition-colors relative ${isListening ? 'text-red-500 animate-pulse' : 'text-gray-400 hover:text-brand-500'}`}
                     >
                        {isListening && <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 animate-ping rounded-full block"></span>}
                        <Mic size={20} />
                     </button>
                     <button 
                       type="submit" 
                       disabled={!input.trim() || isLoading}
                       className="p-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl transition-colors disabled:opacity-50 disabled:hover:bg-brand-600 shadow-md"
                     >
                        <Send size={18} />
                     </button>
                  </div>
               </div>
            </form>
            <p className="text-[10px] text-center mt-3 text-gray-400 flex items-center justify-center gap-1">
               <ShieldAlert size={12} /> Virtual Vita is an AI. It can make mistakes. Always consult a doctor.
            </p>
         </div>
      </div>
    </div>
  );
};

export default UserDashboard;
