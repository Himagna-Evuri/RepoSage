# RepoSage

RepoSage is a machine-learning project that predicts which software commits may be defect-inducing, using commit-level features.

## Model and evaluation

- Model: Random Forest
- Decision threshold: 0.7
- Data split: chronological within each repository
- Training rows: 230,658
- Validation rows: 57,712
- Test rows: 72,093

| Metric | Validation | Final test |
|---|---:|---:|
| PR-AUC | 0.3257 | 0.4129 |
| Precision | 0.301 | 0.365 |
| Recall | 0.487 | 0.593 |
| Commits flagged | 8,153 | 14,288 |

At the selected threshold, the model flagged 14,288 of 72,093 test commits (about 19.8%).

## Limitation

The target labels are SZZ-derived indicators of bug-inducing commits. They are a noisy proxy and do not prove that a commit introduced a defect.