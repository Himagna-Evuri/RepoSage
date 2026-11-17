
import json
import sys
from pathlib import Path

from reposage_extract import (
    run_git_command,
    get_commit_sha,
    extract_commit_features,
    get_changed_files,
    build_dependency_graph,
    find_impacted_files,
    predict_defect_risk,
    explain_defect_risk,
    analyze_recent_commits,
    rank_commits_by_risk
)


def validate_repository(repo_path):

    repo_path = Path(repo_path).expanduser().resolve()

    if not repo_path.exists() or not repo_path.is_dir():
        raise ValueError("Invalid repository path.")

    repo_status = run_git_command(
        ["rev-parse", "--is-inside-work-tree"],
        repo_path
    )

    if repo_status.strip() != "true":
        raise ValueError("Not a valid Git repository.")

    return repo_path


def analyze_commit(repo_path, commit_sha):

    repo_path = validate_repository(repo_path)

    actual_sha = get_commit_sha(repo_path, commit_sha)

    features = extract_commit_features(repo_path, actual_sha)

    changed_files = get_changed_files(repo_path, actual_sha)

    dependency_graph = build_dependency_graph(repo_path)

    impacted_files = find_impacted_files(
        changed_files,
        dependency_graph
    )

    probability, prediction, risk_category = (
        predict_defect_risk(features)
    )

    expected_value, explanations = explain_defect_risk(features)

    for item in explanations:
        value = item["feature_value"]

        if hasattr(value, "item"):
            item["feature_value"] = value.item()

        item["shap_value"] = float(item["shap_value"])

        item["direction"] = (
            "Increases defect risk"
            if item["shap_value"] > 0
            else "Decreases defect risk"
        )

    return {
        "commitSha": actual_sha,
        "features": features,
        "probability": float(probability),
        "prediction": int(prediction),
        "riskCategory": risk_category,
        "changedFiles": changed_files,
        "impactedFiles": impacted_files,
        "expectedValue": float(expected_value),
        "explanations": explanations
    }


def analyze_multiple_commits(repo_path, limit):

    repo_path = validate_repository(repo_path)

    limit = int(limit)

    if limit <= 0:
        raise ValueError("Commit limit must be greater than zero.")

    results = analyze_recent_commits(repo_path, limit)

    ranked_results = rank_commits_by_risk(results)

    formatted_results = []

    for rank, result in enumerate(ranked_results, start=1):

        formatted_results.append({
            "rank": rank,
            "commitSha": result["commit_sha"],
            "features": result["features"],
            "probability": float(result["probability"]),
            "prediction": int(result["prediction"]),
            "riskCategory": result["risk_category"]
        })

    return {
        "totalCommitsAnalyzed": len(formatted_results),
        "commits": formatted_results
    }


if __name__ == "__main__":

    try:

        if len(sys.argv) == 3:

            result = analyze_commit(
                sys.argv[1],
                sys.argv[2]
            )

        elif len(sys.argv) == 4 and sys.argv[2] == "--last":

            result = analyze_multiple_commits(
                sys.argv[1],
                sys.argv[3]
            )

        else:
            raise ValueError(
                "Usage:\n"
                "Single commit: reposage_api.py <repository_path> <commit_sha>\n"
                "Multiple commits: reposage_api.py <repository_path> --last <N>"
            )

        print(json.dumps(result))

    except Exception as error:

        print(json.dumps({
            "error": str(error)
        }))

        sys.exit(1)
