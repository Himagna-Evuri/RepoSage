
import { useState } from 'react'
import ResultsPanel from './ResultsPanel'
import './App.css'

function App() {
  const [analysisMode, setAnalysisMode] = useState('single')
  const [repoPath, setRepoPath] = useState('')
  const [commitSha, setCommitSha] = useState('')
  const [commitLimit, setCommitLimit] = useState(10)
  const [message, setMessage] = useState('')
  const [analysisResult, setAnalysisResult] = useState(null)
  const [resultMode, setResultMode] = useState('single')
  const [loading, setLoading] = useState(false)

  // Send the analysis request to the Spring Boot backend
  async function handleSubmit(event) {
    event.preventDefault()

    if (!repoPath.trim()) {
      setMessage('Please enter a Git repository path.')
      setAnalysisResult(null)
      return
    }

    if (analysisMode === 'single' && !commitSha.trim()) {
      setMessage('Please enter a commit SHA.')
      setAnalysisResult(null)
      return
    }

    if (
        analysisMode === 'multiple' &&
        (!commitLimit || Number(commitLimit) < 1)
    ) {
      setMessage('Please enter a valid commit limit.')
      setAnalysisResult(null)
      return
    }

    setLoading(true)
    setMessage('')
    setAnalysisResult(null)

    try {
      let response

      if (analysisMode === 'single') {
        // Single-commit API request
        response = await fetch('http://localhost:8080/api/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            repoPath: repoPath.trim(),
            commitSha: commitSha.trim()
          })
        })
      } else {
        // Multiple-commit API request
        const params = new URLSearchParams({
          repoPath: repoPath.trim(),
          limit: String(commitLimit)
        })

        response = await fetch(
            `http://localhost:8080/api/analyze/recent?${params.toString()}`,
            {
              method: 'GET'
            }
        )
      }

      const responseText = await response.text()

      let data

      try {
        data = JSON.parse(responseText)
      } catch {
        throw new Error('The backend returned an invalid response.')
      }

      if (!response.ok) {
        throw new Error(
            data.error || `Backend request failed (${response.status}).`
        )
      }

      if (data.error) {
        throw new Error(data.error)
      }

      // Store the actual backend response
      setAnalysisResult(data)
      setResultMode(analysisMode)
      setMessage('Repository analysis completed successfully!')
    } catch (error) {
      console.error('RepoSage API error:', error)

      setAnalysisResult(null)
      setMessage(
          error.message ||
          'Unable to connect to the RepoSage backend.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
      <div className="app-container">

        {/* Sidebar */}
        <aside className="sidebar">
          <div className="brand">
            <div className="brand-icon">R</div>
            <div>
              <h2>RepoSage</h2>
              <span>Code Intelligence</span>
            </div>
          </div>

          <nav className="sidebar-nav">
            <p className="nav-heading">WORKSPACE</p>

            <a href="#dashboard" className="nav-link active">
              <span>▦</span> Dashboard
            </a>

            <a href="#analysis" className="nav-link">
              <span>⌕</span> Commit Analysis
            </a>

            <a href="#about" className="nav-link">
              <span>ⓘ</span> About RepoSage
            </a>
          </nav>

          <div className="sidebar-bottom">
            <div className="system-status">
              <span className="status-dot"></span>
              Analysis engine
              <strong>Ready</strong>
            </div>
            <p>RepoSage v1.0</p>
          </div>
        </aside>

        {/* Main content */}
        <main className="main-content" id="dashboard">

          {/* Header */}
          <header className="topbar">
            <div>
              <p className="breadcrumb">Workspace / Dashboard</p>
              <h1>Repository Overview</h1>
            </div>

            <div className="topbar-right">
            <span className="live-indicator">
              <span className="status-dot"></span>
              Local environment
            </span>
              <div className="avatar">U</div>
            </div>
          </header>

          {/* Welcome section */}
          <section className="welcome-section">
            <div>
              <p className="eyebrow">INTELLIGENT CODE ANALYSIS</p>
              <h2>Understand your code before it breaks.</h2>
              <p>
                Analyze Git commits, identify potentially impacted files,
                and estimate defect risk using machine learning.
              </p>
            </div>

            <div className="welcome-graphic">⌘</div>
          </section>

          {/* Statistics */}
          <section className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon purple">⌘</div>
              <p>Analysis engine</p>
              <h3>Random Forest</h3>
              <span>Machine learning model</span>
            </div>

            <div className="stat-card">
              <div className="stat-icon blue">⌁</div>
              <p>Model explainability</p>
              <h3>SHAP</h3>
              <span>Feature contributions</span>
            </div>

            <div className="stat-card">
              <div className="stat-icon green">⑂</div>
              <p>Change detection</p>
              <h3>Git Analysis</h3>
              <span>Commit and file dependencies</span>
            </div>

            <div className="stat-card">
              <div className="stat-icon orange">⇄</div>
              <p>Backend</p>
              <h3>Spring Boot</h3>
              <span>REST API integration</span>
            </div>
          </section>

          {/* Analysis form */}
          <section className="analysis-section" id="analysis">
            <div className="section-heading">
              <div>
                <p className="eyebrow">GET STARTED</p>
                <h2>Analyze a repository</h2>
                <p>
                  Choose how you want RepoSage to analyze your commits.
                </p>
              </div>

              <span className="section-tag">Git analysis</span>
            </div>

            <div className="analysis-card">

              {/* Analysis mode selection */}
              <div className="mode-selector">
                <button
                    type="button"
                    className={
                      analysisMode === 'single'
                          ? 'mode-btn selected'
                          : 'mode-btn'
                    }
                    onClick={() => {
                      setAnalysisMode('single')
                      setMessage('')
                      setAnalysisResult(null)
                    }}
                >
                  Single Commit
                </button>

                <button
                    type="button"
                    className={
                      analysisMode === 'multiple'
                          ? 'mode-btn selected'
                          : 'mode-btn'
                    }
                    onClick={() => {
                      setAnalysisMode('multiple')
                      setMessage('')
                      setAnalysisResult(null)
                    }}
                >
                  Multiple Commits
                </button>
              </div>

              <form onSubmit={handleSubmit}>

                {/* Repository path */}
                <div className="form-group">
                  <label htmlFor="repoPath">
                    Git repository path
                  </label>

                  <input
                      id="repoPath"
                      type="text"
                      placeholder="C:/Users/username/Documents/MyRepository"
                      value={repoPath}
                      onChange={(event) => setRepoPath(event.target.value)}
                      disabled={loading}
                  />

                  <small>
                    Enter the local path of your Git repository.
                  </small>
                </div>

                {/* Single or multiple commit input */}
                {analysisMode === 'single' ? (
                    <div className="form-group">
                      <label htmlFor="commitSha">Commit SHA</label>

                      <input
                          id="commitSha"
                          type="text"
                          placeholder="Enter the commit SHA"
                          value={commitSha}
                          onChange={(event) => setCommitSha(event.target.value)}
                          disabled={loading}
                      />

                      <small>
                        Provide the commit you want to analyze.
                      </small>
                    </div>
                ) : (
                    <div className="form-group">
                      <label htmlFor="commitLimit">
                        Number of recent commits
                      </label>

                      <input
                          id="commitLimit"
                          type="number"
                          min="1"
                          max="100"
                          value={commitLimit}
                          onChange={(event) => setCommitLimit(event.target.value)}
                          disabled={loading}
                      />

                      <small>
                        Choose how many recent commits to analyze.
                      </small>
                    </div>
                )}

                <button
                    type="submit"
                    className="analyze-btn"
                    disabled={loading}
                >
                  {loading ? 'Analyzing...' : 'Analyze Repository'}
                  {!loading && <span> →</span>}
                </button>

                {message && (
                    <p className="form-message" role="status">
                      {message}
                    </p>
                )}
              </form>
            </div>
          </section>

          {/* Analysis results */}
          {analysisResult && (
              <ResultsPanel
                  mode={resultMode}
                  result={analysisResult}
              />
          )}

          {/* Features */}
          <section className="features-section" id="about">
            <div className="section-heading">
              <div>
                <p className="eyebrow">WHAT REPOSAGE DOES</p>
                <h2>Intelligent analysis capabilities</h2>
              </div>
            </div>

            <div className="features-grid">
              <div className="feature-card">
                <span className="feature-icon">◈</span>
                <h3>Defect Risk Prediction</h3>
                <p>
                  Random Forest estimates the likelihood that a commit
                  may be defect-inducing.
                </p>
              </div>

              <div className="feature-card">
                <span className="feature-icon">⑂</span>
                <h3>Change Impact Analysis</h3>
                <p>
                  Dependency analysis identifies files that may be
                  affected by code changes.
                </p>
              </div>

              <div className="feature-card">
                <span className="feature-icon">✳</span>
                <h3>Model Explainability</h3>
                <p>
                  SHAP explanations show which commit features
                  influenced the prediction.
                </p>
              </div>
            </div>
          </section>

          {/* Footer */}
          <footer className="footer">
          <span>
            RepoSage — Pull Request Change-Impact & Defect-Risk Analyzer
          </span>
            <span>Built with React, Spring Boot and Python</span>
          </footer>

        </main>
      </div>
  )
}

export default App
