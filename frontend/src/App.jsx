import { useState, useRef, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import AnalysisCard from './components/AnalysisCard';
import ChatBox from './components/ChatBox';
import MockInterview from './components/MockInterview';
import './App.css'; // Optional if anything remains here, mostly index.css handles it.

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

function App() {
  const [jd, setJd] = useState('');
  const [file, setFile] = useState(null);
  const [resumeText, setResumeText] = useState('');
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisRaw, setAnalysisRaw] = useState(null);
  
  const [chatHistory, setChatHistory] = useState([
    { role: 'assistant', content: 'Hi! I am SageAI. Upload your resume and JD, then ask me anything about optimizing your profile.' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatting, setIsChatting] = useState(false);
  
  const [activeTab, setActiveTab] = useState('analysis'); // 'analysis' | 'interview'

  const handleFileChange = async (e) => {
    const selected = e.target.files[0];
    if (!selected) return;
    setFile(selected);
    
    // Auto extract text
    const formData = new FormData();
    formData.append('file', selected);
    
    try {
      const res = await fetch(`${API_BASE}/extract-pdf`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Failed to extract text from PDF.');
      }
      if (data.text) {
        setResumeText(data.text);
      } else {
        alert("Failed to extract text from PDF.");
      }
    } catch (err) {
      console.error(err);
      alert("Error extracting PDF.");
    }
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setAnalysisRaw(null);
    setActiveTab('analysis'); // Switch to analysis tab when generating
    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resumeText, jd_text: jd }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Error generating analysis.');
      }
      setAnalysisRaw(data);
    } catch (err) {
      console.error(err);
      alert(err.message || "Error generating analysis.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMsg = chatInput.trim();
    setChatInput('');
    setChatHistory(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsChatting(true);
    
    try {
      const payload = {
        message: userMsg,
        resume_text: resumeText || null,
        jd_text: jd || null,
        chat_history: chatHistory.filter(m => m.role !== 'system')
      };
      
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      
      const data = await res.json();
      setChatHistory(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      console.error(err);
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="app-container">
      {/* 1. Left Panel: Inputs */}
      <Sidebar 
        jd={jd}
        setJd={setJd}
        file={file}
        setFile={setFile}
        onFileChange={handleFileChange}
        onAnalyze={handleAnalyze}
        isAnalyzing={isAnalyzing}
      />
      
      {/* 2. Middle Panel: Analysis or Mock Interview */}
      <div className="main-content">
        <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'center' }}>
          <div className="tabs-container">
            <button 
              className={`tab-btn ${activeTab === 'analysis' ? 'active' : ''}`}
              onClick={() => setActiveTab('analysis')}
            >
              Analysis Dashboard
            </button>
            <button 
              className={`tab-btn ${activeTab === 'interview' ? 'active' : ''}`}
              onClick={() => setActiveTab('interview')}
            >
              Mock Interview
            </button>
          </div>
        </div>

        {activeTab === 'analysis' ? (
          <AnalysisCard 
            analysisRaw={analysisRaw} 
            jdText={jd} 
            resumeText={resumeText} 
          />
        ) : (
          <MockInterview 
            resumeText={resumeText} 
            jdText={jd} 
          />
        )}
      </div>
      {/* 3. Right Panel: Chat Interface */}
      <ChatBox 
        chatHistory={chatHistory}
        isChatting={isChatting}
        chatInput={chatInput}
        setChatInput={setChatInput}
        onSendMessage={handleSendMessage}
      />
    </div>
  );
}

export default App;
