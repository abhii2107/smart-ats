function ProgressBar({ label, value }) {
  const safeValue = Math.max(0, Math.min(Number(value) || 0, 100));
  const scoreClass = safeValue >= 80 ? 'high' : safeValue >= 60 ? 'medium' : 'low';

  return (
    <div className="metric-row">
      <div className="metric-label">
        <span>{label}</span>
        <strong className={`metric-value ${scoreClass}`}>{safeValue.toFixed(1)}%</strong>
      </div>
      <div className="progress-track">
        <div className={`progress-fill ${scoreClass}`} style={{ width: `${safeValue}%` }} />
      </div>
    </div>
  );
}

function SkillTags({ skills, type }) {
  if (!skills?.length) {
    return <p className="muted-copy">None found.</p>;
  }

  return (
    <div className="keyword-list">
      {skills.map((skill) => (
        <span key={skill} className={`keyword-pill ${type}`}>
          {skill}
        </span>
      ))}
    </div>
  );
}

function AnalysisCard({ analysisRaw }) {
  if (!analysisRaw) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">ATS</div>
        <h2>Awaiting Analysis</h2>
        <p>Upload your resume and JD to see the deterministic score breakdown.</p>
      </div>
    );
  }

  const displayScore = Number(analysisRaw.ats_score) || 0;
  const scoreClass = displayScore >= 80 ? 'high' : displayScore >= 60 ? 'medium' : 'low';
  const componentScores = analysisRaw.component_scores || {};

  return (
    <div className="analysis-dashboard">
      <div className="dashboard-header">
        <h2>Analysis Results</h2>
      </div>

      <div className="score-grid">
        <div className="glass-panel score-card primary-score-card">
          <div className="score-card-header">
            <span className="score-card-title">Overall ATS Score</span>
          </div>
          <div className={`score-value ${scoreClass}`}>
            {displayScore.toFixed(1)}<span className="score-denominator">/100</span>
          </div>
          <div className="score-formula">70% weighted keyword score + 30% semantic similarity</div>
        </div>

        <div className="glass-panel score-card">
          <div className="score-card-header">
            <span className="score-card-title">Keyword Score</span>
          </div>
          <div className={`score-value ${analysisRaw.keyword_score >= 70 ? 'high' : analysisRaw.keyword_score >= 50 ? 'medium' : 'low'}`}>
            {Number(analysisRaw.keyword_score || 0).toFixed(1)}%
          </div>
        </div>

        <div className="glass-panel score-card">
          <div className="score-card-header">
            <span className="score-card-title">Semantic Similarity</span>
          </div>
          <div className={`score-value ${analysisRaw.similarity_score >= 70 ? 'high' : analysisRaw.similarity_score >= 50 ? 'medium' : 'low'}`}>
            {Number(analysisRaw.similarity_score || 0).toFixed(1)}%
          </div>
        </div>
      </div>

      <div className="glass-panel section-card">
        <h3 className="section-title">Weighted ATS Breakdown</h3>
        <ProgressBar label="Skills Match - 40%" value={componentScores.skills} />
        <ProgressBar label="Experience Match - 30%" value={componentScores.experience} />
        <ProgressBar label="Projects Match - 20%" value={componentScores.projects} />
        <ProgressBar label="Education Match - 10%" value={componentScores.education} />
      </div>

      <div className="analysis-two-column">
        <div className="glass-panel section-card">
          <h3 className="section-title">Matched Skills</h3>
          <SkillTags skills={analysisRaw.matched_skills} type="matched" />
        </div>

        <div className="glass-panel section-card">
          <h3 className="section-title">Missing Skills</h3>
          <SkillTags skills={analysisRaw.missing_skills} type="missing" />
        </div>
      </div>

      <div className="glass-panel section-card">
        <h3 className="section-title">Extracted JD Keywords</h3>
        <div className="keyword-groups">
          <div>
            <span className="keyword-group-title">Technical</span>
            <SkillTags skills={analysisRaw.job_keywords?.technical_skills} type="neutral" />
          </div>
          <div>
            <span className="keyword-group-title">Tools</span>
            <SkillTags skills={analysisRaw.job_keywords?.tools} type="neutral" />
          </div>
          <div>
            <span className="keyword-group-title">Frameworks</span>
            <SkillTags skills={analysisRaw.job_keywords?.frameworks} type="neutral" />
          </div>
          <div>
            <span className="keyword-group-title">Soft Skills</span>
            <SkillTags skills={analysisRaw.job_keywords?.soft_skills} type="neutral" />
          </div>
        </div>
      </div>

      <div className="glass-panel section-card">
        <h3 className="section-title">Suggestions</h3>
        <ul className="list-items">
          {(analysisRaw.suggestions || []).map((suggestion) => (
            <li key={suggestion}>{suggestion}</li>
          ))}
        </ul>
      </div>

      {analysisRaw.explanation && (
        <div className="glass-panel section-card analysis-summary">
          <h3 className="section-title">Assistant Notes</h3>
          <p>{analysisRaw.explanation}</p>
        </div>
      )}
    </div>
  );
}

export default AnalysisCard;

