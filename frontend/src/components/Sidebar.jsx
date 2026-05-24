import { useState } from 'react';

function Sidebar({ jd, setJd, file, setFile, onAnalyze, isAnalyzing, onFileChange }) {
  const [jdError, setJdError] = useState('');
  const [fileError, setFileError] = useState('');

  const validateAndAnalyze = () => {
    let isValid = true;
    
    if (!jd.trim()) {
      setJdError('Job Description is required.');
      isValid = false;
    } else if (jd.trim().split(/\s+/).length < 10) {
      setJdError('Job Description is too short.');
      isValid = false;
    } else {
      setJdError('');
    }

    if (!file) {
      setFileError('Resume PDF is required.');
      isValid = false;
    } else {
      setFileError('');
    }

    if (isValid) {
      onAnalyze();
    }
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      onFileChange({ target: { files: [droppedFile] } });
      setFileError('');
    } else {
      setFileError('Please upload a valid PDF file.');
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1 className="gradient-text">CodeSage</h1>
        <p>AI Resume Analyzer & Coach</p>
      </div>

      <div className="input-group">
        <label className="input-label">Job Description</label>
        <textarea
          style={{ width: '100%', height: '180px', resize: 'none' }}
          placeholder="Paste the job description here..."
          value={jd}
          onChange={(e) => {
            setJd(e.target.value);
            if (e.target.value.trim()) setJdError('');
          }}
        />
        {jdError && (
          <div className="validation-error">
            <span>⚠</span> {jdError}
          </div>
        )}
      </div>

      <div className="input-group">
        <label className="input-label">Your Resume (.pdf)</label>
        <label 
          className={`file-upload-zone ${file ? 'active' : ''}`}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
        >
          <input type="file" accept="application/pdf" onChange={(e) => {
            onFileChange(e);
            if (e.target.files.length > 0) setFileError('');
          }} />
          <div className="file-upload-text">
            {file ? file.name : 'Click to upload or drag & drop'}
          </div>
          {!file && <div className="file-upload-subtext">PDF files only</div>}
        </label>
        {fileError && (
          <div className="validation-error">
            <span>⚠</span> {fileError}
          </div>
        )}
      </div>

      <button
        className="btn-primary"
        onClick={validateAndAnalyze}
        disabled={isAnalyzing}
        style={{ marginTop: 'auto' }}
      >
        {isAnalyzing ? <span className="loader"></span> : 'Generate ATS Analysis'}
      </button>
    </div>
  );
}

export default Sidebar;
