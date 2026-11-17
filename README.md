# RepoSage — Pull Request Change-Impact & Defect-Risk Analyzer

RepoSage is a machine-learning-powered software analysis tool that estimates the defect risk of software commits and identifies files that may be impacted by code changes.

It combines commit-level machine learning, Git-based change analysis, dependency analysis, and SHAP explainability to help developers prioritize code reviews.

## Features

- **Defect Risk Prediction:** Estimates the probability that a commit may be defect-inducing using a trained Random Forest model.
- **Risk Categorization:** Classifies commits into Low, Medium, High, and Critical risk categories.
- **Change Impact Analysis:** Identifies files modified by a commit and potentially impacted dependent files.
- **Multi-Commit Analysis:** Analyzes recent commits and ranks them by predicted risk.
- **Model Explainability:** Uses SHAP to show which features contribute to a prediction.
- **CSV Export:** Exports multi-commit analysis results.
- **REST API:** Connects the Python analysis engine to a Spring Boot backend.
- **Interactive Dashboard:** Provides a React-based interface for submitting repositories and viewing analysis results.

## System Architecture

```text
              React Frontend
                    |
                    | REST API
                    v
             Spring Boot Backend
                    |
                    | ProcessBuilder
                    v
             Python Analysis Engine
                    |
          +---------+----------+
          |         |          |
          v         v          v
       Git CLI   ML Model   SHAP
          |         |          |
          +---------+----------+
                    |
                    v
             JSON Analysis Results
                    |
                    v
              React Dashboard
```

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React.js, Vite, CSS |
| Backend | Java 21, Spring Boot, Maven |
| Machine Learning | Python, Pandas, Scikit-learn |
| Model Explainability | SHAP |
| Git Analysis | Git CLI, Python subprocess |
| Model Persistence | Joblib |
| Testing | Python unittest, Spring Boot tests |
| API Testing | Postman |

## Machine Learning Methodology

RepoSage uses commit-level features to estimate defect risk.

### Features

The model uses the following nine features:

- `nfiles` — Number of files changed
- `la` — Lines added
- `ld` — Lines deleted
- `hunks` — Number of code-change hunks
- `ndirs` — Number of directories affected
- `nexts` — Number of file extensions involved
- `test_ratio` — Test-related change ratio
- `msg_len` — Commit message length
- `msg_ref` — Commit message reference indicator

The commit SHA and target label are not used as model input features.

### Model Evaluation

The Random Forest model was selected over a Logistic Regression baseline using validation performance.

- Model: Random Forest
- Decision threshold: 0.7
- Data split: Chronological within each repository

| Dataset | Rows |
|---|---:|
| Training | 230,658 |
| Validation | 57,712 |
| Final Test | 72,093 |

### Performance

| Metric | Validation | Final Test |
|---|---:|---:|
| PR-AUC | 0.3257 | 0.4129 |
| Precision | 0.301 | 0.365 |
| Recall | 0.487 | 0.593 |
| Commits flagged | 8,153 | 14,288 |

At the selected threshold, the model flagged 14,288 of 72,093 test commits (approximately 19.8%).

### Risk Categories

| Predicted Probability | Risk Category |
|---|---|
| Below 0.30 | Low |
| 0.30–0.59 | Medium |
| 0.60–0.79 | High |
| 0.80 and above | Critical |

The binary prediction threshold is 0.7. Risk categorization and binary classification are separate outputs.

## Change-Impact Analysis

RepoSage uses Git to extract files changed by a commit.

It builds a dependency graph from Java source files and uses dependency relationships to identify potentially impacted files.

The analysis distinguishes between:
- Changed files — directly modified by the commit.
- Impacted files — dependent files that may be affected by those changes.

## Model Explainability

RepoSage integrates SHAP (SHapley Additive exPlanations) to explain individual predictions.

It identifies features that increase or decrease the model's predicted defect risk, helping developers understand the evidence behind a prediction.

## Application API

The Spring Boot backend exposes the following endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend health |
| POST | `/api/analyze` | Analyze a specific commit |
| GET | `/api/analyze/recent` | Analyze recent commits |

### Analyze a Commit

**POST** `/api/analyze`

Example request:

```json
{
  "repoPath": "C:/path/to/git/repository",
  "commitSha": "your-commit-sha"
}
```

### Analyze Recent Commits

**GET** `/api/analyze/recent?repoPath=C:/path/to/git/repository&limit=10`

The endpoint returns ranked analysis results for the requested recent commits.

## Project Setup

### Prerequisites

- Python 3.11
- Java 21
- Node.js and npm
- Git

### 1. Python Analysis Engine

Navigate to the Python project directory:

```bash
cd RepoSage
```

Install dependencies:

```bash
py -3.11 -m pip install -r requirements.txt
```

Run Python unit tests:

```bash
py -3.11 -m unittest test_reposage.py -v
```

### 2. Spring Boot Backend

Navigate to the backend Maven project directory:

```bash
cd reposage-backend

```

Configure Java 21 and start the backend.

On Windows PowerShell:

```powershell
.\mvnw.cmd spring-boot:run
```

The backend runs at `http://localhost:8080`.

### 3. React Frontend

Navigate to the frontend directory:

```bash
cd reposage-frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend runs at `http://localhost:5173`.

## Testing

Python unit tests:

```bash
py -3.11 -m unittest test_reposage.py -v
```

Spring Boot tests:

```powershell
.\mvnw.cmd clean test
```

## Limitations

- The target labels are SZZ-derived indicators of bug-inducing commits. They are a noisy proxy and do not prove that a commit introduced a defect.
- Dependency analysis currently focuses on Java source-file relationships.
- Model predictions are estimates and should support, not replace, developer review.
- Performance may vary across repositories and development environments.

## Future Improvements

- Support dependency analysis for additional programming languages.
- Improve dependency extraction using AST-based analysis.
- Add richer pull-request-level analysis.
- Evaluate additional machine-learning models and calibration methods.
- Extend the dashboard with historical repository insights.

## Author

Developed as a software engineering and machine learning project.
