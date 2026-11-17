
function ResultsPanel({ mode, result }) {
    if (!result) return null

    const isMultiple = mode === 'multiple'

    function formatPercentage(value) {
        if (typeof value !== 'number' || !Number.isFinite(value)) {
            return 'N/A'
        }

        return `${(value * 100).toFixed(2)}%`
    }

    // Validate the response structure before rendering
    const isValidMultipleResult =
        Array.isArray(result.commits) &&
        typeof result.totalCommitsAnalyzed === 'number'

    const isValidSingleResult =
        typeof result.probability === 'number' &&
        typeof result.riskCategory === 'string' &&
        Array.isArray(result.changedFiles) &&
        Array.isArray(result.impactedFiles) &&
        Array.isArray(result.explanations)

    if (
        (isMultiple && !isValidMultipleResult) ||
        (!isMultiple && !isValidSingleResult)
    ) {
        return (
            <section className="results-section" id="results">
                <div className="results-card">
                    <h3>Unable to display analysis results</h3>
                    <p className="results-subtitle">
                        The backend returned incomplete or unexpected data.
                        Please try the analysis again.
                    </p>
                </div>
            </section>
        )
    }

    return (
        <section className="results-section" id="results">

            <div className="section-heading">
                <div>
                    <p className="eyebrow">ANALYSIS REPORT</p>
                    <h2>Repository analysis results</h2>
                    <p>Your commit analysis is complete.</p>
                </div>
                <span className="section-tag">Analysis complete</span>
            </div>

            {isMultiple ? (
                <div className="results-card">
                    <h3>Commit risk ranking</h3>

                    <p className="results-subtitle">
                        Total commits analyzed: {result.totalCommitsAnalyzed}
                    </p>

                    {result.commits.length > 0 ? (
                        <div className="table-wrapper">
                            <table className="results-table">
                                <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Commit SHA</th>
                                    <th>Defect probability</th>
                                    <th>Risk category</th>
                                    <th>Prediction</th>
                                </tr>
                                </thead>

                                <tbody>
                                {result.commits.map((commit, index) => (
                                    <tr key={commit.commitSha || index}>
                                        <td>#{commit.rank}</td>
                                        <td className="sha-cell">
                                            {commit.commitSha
                                                ? `${commit.commitSha.slice(0, 10)}...`
                                                : 'N/A'}
                                        </td>
                                        <td>
                                            {formatPercentage(commit.probability)}
                                        </td>
                                        <td>
                                                <span className={`risk-badge ${
                                                    typeof commit.riskCategory === 'string'
                                                        ? commit.riskCategory.toLowerCase()
                                                        : ''
                                                }`}>
                                                    {commit.riskCategory || 'Unknown'}
                                                </span>
                                        </td>
                                        <td>
                                            {commit.prediction === 1
                                                ? 'Positive'
                                                : commit.prediction === 0
                                                    ? 'Negative'
                                                    : 'Unknown'}
                                        </td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <p className="results-subtitle">
                            No commits were available for analysis.
                        </p>
                    )}
                </div>
            ) : (
                <>
                    <div className="result-summary-grid">

                        <div className="result-card">
                            <p>Defect probability</p>
                            <h3>{formatPercentage(result.probability)}</h3>
                            <span>Model estimated probability</span>
                        </div>

                        <div className="result-card">
                            <p>Risk category</p>
                            <h3>
                                <span className={`risk-badge ${result.riskCategory.toLowerCase()}`}>
                                    {result.riskCategory}
                                </span>
                            </h3>
                            <span>Based on probability ranges</span>
                        </div>

                        <div className="result-card">
                            <p>Changed files</p>
                            <h3>{result.changedFiles.length}</h3>
                            <span>Files modified in this commit</span>
                        </div>

                        <div className="result-card">
                            <p>Impacted files</p>
                            <h3>{result.impactedFiles.length}</h3>
                            <span>Potentially affected files</span>
                        </div>

                    </div>

                    <div className="results-card">
                        <h3>Commit information</h3>
                        <p className="commit-sha">{result.commitSha || 'N/A'}</p>

                        <h3>Changed files</h3>

                        {result.changedFiles.length > 0 ? (
                            <ul className="file-list">
                                {result.changedFiles.map((file, index) => (
                                    <li key={file || index}>
                                        <span>{file}</span>
                                        <span className="file-label changed">Changed</span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="results-subtitle">No changed files identified.</p>
                        )}

                        <h3>Potentially impacted files</h3>

                        {result.impactedFiles.length > 0 ? (
                            <ul className="file-list">
                                {result.impactedFiles.map((file, index) => (
                                    <li key={file || index}>
                                        <span>{file}</span>
                                        <span className="file-label impacted">Impacted</span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="results-subtitle">
                                No potentially impacted files identified.
                            </p>
                        )}
                    </div>

                    <div className="results-card">
                        <h3>SHAP feature explanations</h3>
                        <p className="results-subtitle">
                            Features influencing the model prediction.
                        </p>

                        {result.explanations.length > 0 ? (
                            <div className="table-wrapper">
                                <table className="results-table">
                                    <thead>
                                    <tr>
                                        <th>Feature</th>
                                        <th>Feature value</th>
                                        <th>SHAP value</th>
                                        <th>Direction</th>
                                    </tr>
                                    </thead>

                                    <tbody>
                                    {result.explanations.map((item, index) => (
                                        <tr key={item.feature || index}>
                                            <td>{item.feature || 'N/A'}</td>
                                            <td>{item.feature_value ?? 'N/A'}</td>
                                            <td>
                                                {typeof item.shap_value === 'number'
                                                    ? item.shap_value.toFixed(4)
                                                    : 'N/A'}
                                            </td>
                                            <td>
                                                    <span className={
                                                        typeof item.shap_value === 'number' &&
                                                        item.shap_value > 0
                                                            ? 'positive-impact'
                                                            : 'negative-impact'
                                                    }>
                                                        {item.direction || 'Unknown'}
                                                    </span>
                                            </td>
                                        </tr>
                                    ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <p className="results-subtitle">
                                No feature explanations are available.
                            </p>
                        )}
                    </div>
                </>
            )}
        </section>
    )
}

export default ResultsPanel
