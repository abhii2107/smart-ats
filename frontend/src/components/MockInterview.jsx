import { useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

function MockInterview({ resumeText, jdText }) {
  const [isStarted, setIsStarted] = useState(false);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isGeneratingQuestion, setIsGeneratingQuestion] = useState(false);

  const generateQuestion = async () => {
    setIsGeneratingQuestion(true);
    try {
      const res = await fetch(`${API_BASE}/mock-question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_text: resumeText,
          jd_text: jdText,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Unable to generate interview question.');
      }
      setQuestion(data.question);
    } catch (err) {
      console.error(err);
      setQuestion(err.message || "Could you describe a challenging project from your past experience and how you handled it?");
    } finally {
      setIsGeneratingQuestion(false);
    }
  };

  const startInterview = () => {
    setIsStarted(true);
    setAnswer('');
    setFeedback('');
    generateQuestion();
  };

  const nextQuestion = () => {
    setAnswer('');
    setFeedback('');
    generateQuestion();
  };

  const submitAnswer = async () => {
    if (!answer.trim()) return;
    setIsEvaluating(true);
    
    try {
      const res = await fetch(`${API_BASE}/mock-feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          answer,
          resume_text: resumeText || '',
          jd_text: jdText || '',
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Unable to evaluate this answer.');
      }
      setFeedback(data.feedback);
    } catch (err) {
      console.error(err);
      setFeedback(err.message || "Error evaluating the answer. Please try again.");
    } finally {
      setIsEvaluating(false);
    }
  };

  if (!isStarted) {
    return (
      <div className="mock-interview-container">
        <div className="dashboard-header">
          <h2>Mock Interview</h2>
        </div>
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', marginTop: '2rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎤</div>
          <h3 style={{ marginBottom: '1rem' }}>Practice for your next interview</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
            We'll dynamically generate questions based on your resume and the job description, and give you immediate feedback.
          </p>
          <button 
            className="btn-primary" 
            onClick={startInterview}
            disabled={!resumeText || !jdText}
            style={{ margin: '0 auto' }}
          >
            Start Mock Interview
          </button>
          {(!resumeText || !jdText) && (
            <p className="validation-error" style={{ justifyContent: 'center', marginTop: '1rem' }}>
              Please upload a resume and job description first.
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="mock-interview-container">
      <div className="dashboard-header">
        <h2>Mock Interview</h2>
        <button className="btn-secondary" onClick={() => setIsStarted(false)}>
          End Interview
        </button>
      </div>

      <div className="glass-panel mi-question-card">
        <div style={{ color: 'var(--text-secondary)', textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.05em', marginBottom: '1rem' }}>
          Question
        </div>
        <div className="mi-question-text">
          {isGeneratingQuestion ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '1rem' }}>
              <span className="loader" style={{ borderTopColor: 'var(--accent-primary)' }}></span>
            </div>
          ) : (
            `"${question}"`
          )}
        </div>
      </div>

      <div className="input-group">
        <label className="input-label">Your Answer</label>
        <textarea
          style={{ width: '100%', height: '150px', resize: 'vertical' }}
          placeholder="Type your answer here..."
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          disabled={!!feedback || isEvaluating || isGeneratingQuestion}
        />
      </div>

      {!feedback ? (
        <button 
          className="btn-primary" 
          onClick={submitAnswer}
          disabled={!answer.trim() || isEvaluating || isGeneratingQuestion}
          style={{ alignSelf: 'flex-start' }}
        >
          {isEvaluating ? <span className="loader"></span> : 'Submit Answer'}
        </button>
      ) : (
        <div className="mi-feedback glass-panel">
          <strong>Feedback:</strong> {feedback}
          <div style={{ marginTop: '1rem' }}>
            <button className="btn-secondary" onClick={nextQuestion}>
              Next Question
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default MockInterview;
