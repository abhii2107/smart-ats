import { useRef, useEffect } from 'react';

function ChatBox({ chatHistory, isChatting, onSendMessage, chatInput, setChatInput }) {
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isChatting]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSendMessage();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  // Filter out system messages
  const displayHistory = chatHistory.filter(m => m.role !== 'system');

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-avatar">S</div>
        <div>SageAI Assistant</div>
      </div>
      
      <div className="chat-messages">
        {displayHistory.length === 0 ? (
          <div className="empty-state" style={{ height: '100%' }}>
            <p>Upload your resume and JD, then ask me anything!</p>
          </div>
        ) : (
          displayHistory.map((msg, idx) => (
            <div key={idx} className={`chat-bubble-wrapper ${msg.role === 'user' ? 'user' : 'ai'}`}>
              {msg.role === 'assistant' && <div className="chat-avatar">S</div>}
              <div className="chat-bubble">
                {msg.content}
              </div>
            </div>
          ))
        )}
        
        {isChatting && (
          <div className="chat-bubble-wrapper ai">
            <div className="chat-avatar">S</div>
            <div className="chat-bubble" style={{ display: 'flex', alignItems: 'center', height: '42px' }}>
              <span className="loader" style={{ width: '1rem', height: '1rem', borderTopColor: 'var(--accent-primary)' }}></span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="chat-input-area">
        <form className="chat-input-container" onSubmit={handleSubmit}>
          <textarea
            className="chat-input"
            placeholder="Ask anything about optimizing your resume..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isChatting}
            rows={1}
          />
          <button 
            type="submit" 
            className="btn-send" 
            disabled={isChatting || !chatInput.trim()}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatBox;
