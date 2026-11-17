
import subprocess
from pathlib import Path
import sys
import os
import re
import joblib
import pandas as pd
import csv
import shap
import json


# Function to execute Git commands
def run_git_command(args, repo_path):
    result = subprocess.run(
        ["git"] + args,
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout


# Get and validate the commit SHA
def get_commit_sha(repo_path, commit_sha=None):
    if commit_sha:
        try:
            return run_git_command(
                ["rev-parse", "--verify", commit_sha + "^{commit}"],
                repo_path
            ).strip()

        except subprocess.CalledProcessError:
            raise ValueError("Invalid commit SHA or commit not found.")

    return run_git_command(["rev-parse", "HEAD"], repo_path).strip()


# Retrieve the latest N commits from a repository

# Retrieve the latest N commits from a repository
def get_recent_commits(repo_path, limit=10):

    if limit <= 0:
        raise ValueError("Commit limit must be greater than zero.")

    try:
        commit_output = run_git_command(
            ["log", "-n", str(limit), "--format=%H"],
            repo_path
        )

    except subprocess.CalledProcessError:
        # Check whether the repository has any commits
        raise ValueError("No commits found in this repository.")

    commit_list = commit_output.strip().splitlines()

    return commit_list



# Extract all nine features from a commit
def extract_commit_features(repo_path, commit_sha):

    # Extract commit message
    commit_message = run_git_command(
        ["log", "-1", "--format=%s", commit_sha],
        repo_path
    ).strip()

    # Extract file change statistics
    change_stats = run_git_command(
        ["show", "--format=", "--numstat", commit_sha],
        repo_path
    )

    added_lines = 0
    deleted_lines = 0
    changed_files = 0

    for line in change_stats.strip().splitlines():
        parts = line.split("\t")

        if len(parts) >= 3:
            added, deleted, filename = parts[0], parts[1], parts[2]

            if added.isdigit():
                added_lines += int(added)

            if deleted.isdigit():
                deleted_lines += int(deleted)

            changed_files += 1

    # Extract commit diff with zero context lines
    diff_output = run_git_command(
        ["show", "--format=", "--unified=0", commit_sha],
        repo_path
    )

    # Count diff hunk headers
    hunk_count = sum(
        1 for line in diff_output.splitlines()
        if line.startswith("@@")
    )

    # Extract changed filenames
    changed_files_output = run_git_command(
        [
            "diff-tree", "--root", "--no-commit-id",
            "--name-only", "-r", commit_sha
        ],
        repo_path
    )

    # Store unique parent directories and file extensions
    directories = set()
    extensions = set()

    for filename in changed_files_output.splitlines():
        file_path = Path(filename)

        parent_dir = filename.rsplit("/", 1)[0] if "/" in filename else ""
        directories.add(parent_dir)

        if file_path.suffix:
            extensions.add(file_path.suffix.lower())

    ndirs = len(directories)
    nexts = len(extensions)

    # Calculate commit message features
    msg_len = len(commit_message)
    msg_ref = int(bool(re.search(r'#\d+', commit_message)))

    # Identify test-related files
    TEST = re.compile(
        r"(^|/)(tests?|spec|__tests__|testing)(/|$)|[._-](test|spec)\.|_test\.go$",
        re.I
    )

    # Calculate test_ratio
    test_files = sum(
        bool(TEST.search(filename))
        for filename in changed_files_output.splitlines()
    )

    test_ratio = test_files / changed_files if changed_files else 0.0

    # Create the feature dictionary
    features = {
        "nfiles": changed_files,
        "la": added_lines,
        "ld": deleted_lines,
        "hunks": hunk_count,
        "ndirs": ndirs,
        "nexts": nexts,
        "test_ratio": test_ratio,
        "msg_len": msg_len,
        "msg_ref": msg_ref
    }

    return features



# Extract filenames changed in a commit
def get_changed_files(repo_path, commit_sha):

    changed_files_output = run_git_command(
        [
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit_sha
        ],
        repo_path
    )

    changed_files = [
        filename
        for filename in changed_files_output.splitlines()
        if filename.strip()
    ]

    return changed_files


# Build a Java file dependency graph using import statements
def build_dependency_graph(repo_path):

    java_files = []

    # Find all Java files in the repository
    for root, dirs, files in os.walk(repo_path):

        # Ignore Git's internal directory
        dirs[:] = [directory for directory in dirs if directory != ".git"]

        for filename in files:
            if filename.endswith(".java"):
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(
                    full_path, repo_path
                ).replace("\\", "/")

                java_files.append((full_path, relative_path))

    # Map Java class names to their source files
    class_to_file = {}

    for full_path, relative_path in java_files:

        with open(full_path, "r", encoding="utf-8") as file:
            source_code = file.read()

        class_match = re.search(
            r"\b(?:class|interface|enum|record)\s+(\w+)",
            source_code
        )

        if class_match:
            class_name = class_match.group(1)
            class_to_file[class_name] = relative_path

    # Build the dependency graph
    dependency_graph = {}

    for full_path, relative_path in java_files:

        with open(full_path, "r", encoding="utf-8") as file:
            source_code = file.read()

        imports = re.findall(
            r"^\s*import\s+(?:static\s+)?[\w.]+;",
            source_code,
            re.MULTILINE
        )

        dependencies = []

        for import_statement in imports:
            imported_class = import_statement.rstrip(";").split(".")[-1]

            if imported_class in class_to_file:
                dependency_file = class_to_file[imported_class]

                if dependency_file != relative_path:
                    dependencies.append(dependency_file)

        if dependencies:
            dependency_graph[relative_path] = sorted(set(dependencies))

    return dependency_graph


# Find files that may be impacted by changed files

from collections import deque

# Find direct and indirect impacted files using BFS
def find_impacted_files(changed_files, dependency_graph):

    impacted_files = set()
    queue = deque(changed_files)

    while queue:

        current_file = queue.popleft()

        for source_file, dependencies in dependency_graph.items():

            if current_file in dependencies:
                
                if source_file not in impacted_files and source_file not in changed_files:

                    impacted_files.add(source_file)
                    queue.append(source_file)

    return sorted(impacted_files)

def display_impact_analysis(changed_files, impacted_files):

    print("\n===== Change Impact Analysis =====")

    print("\nChanged Files:")
    for filename in changed_files:
        print(f"  - {filename}")

    print("\nPotentially Impacted Files:")

    if impacted_files:
        for filename in impacted_files:
            print(f"  - {filename}")
    else:
        print("  No dependent files detected.")






# Predict defect risk using the trained model
def predict_defect_risk(features):

    # Load model files from the same folder as this script
    project_dir = Path(__file__).resolve().parent

    model = joblib.load(project_dir / "reposage_model.joblib")
    feature_names = joblib.load(project_dir / "reposage_features.joblib")

    # Convert features into a DataFrame
    input_data = pd.DataFrame([features])

    # Ensure columns follow the model's training order
    input_data = input_data[feature_names]

    # Predict defect probability
    probability = model.predict_proba(input_data)[0][1]

    # Apply the selected threshold
    threshold = 0.7
    prediction = int(probability >= threshold)

    # Categorize risk based on model score
    if probability < 0.30:
        risk_category = "Low"
    elif probability < 0.60:
        risk_category = "Medium"
    elif probability < 0.80:
        risk_category = "High"
    else:
        risk_category = "Critical"

    return probability, prediction, risk_category


# Explain an individual commit prediction using SHAP
def explain_defect_risk(features, top_n=5):

    # Load model and feature names
    project_dir = Path(__file__).resolve().parent

    model = joblib.load(project_dir / "reposage_model.joblib")
    feature_names = joblib.load(
        project_dir / "reposage_features.joblib"
    )

    # Prepare input data in training feature order
    input_data = pd.DataFrame([features])
    input_data = input_data[feature_names]

    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)

    # Calculate SHAP values
    shap_values = explainer.shap_values(input_data)
    

    # Extract contributions for Class 1
    class1_values = shap_values[0, :, 1]

    

    # Get expected model output for Class 1
    expected_value = explainer.expected_value

    if hasattr(expected_value, "__len__"):
        expected_value = expected_value[1]

    # Build explanation results
    explanations = []

    for name, value, contribution in zip(
        feature_names,
        input_data.iloc[0].values,
        class1_values
    ):
        explanations.append({
            "feature": name,
            "feature_value": value,
            "shap_value": float(contribution)
        })

    # Rank by absolute SHAP contribution
    explanations.sort(
        key=lambda item: abs(item["shap_value"]),
        reverse=True
    )
    
    return expected_value, explanations[:top_n]



# Analyze multiple recent commits
def analyze_recent_commits(repo_path, limit=10):

    # Retrieve recent commit SHAs
    commit_list = get_recent_commits(repo_path, limit)

    results = []

    # Analyze each commit individually
    for commit_sha in commit_list:

        # Extract features
        features = extract_commit_features(repo_path, commit_sha)

       # Predict defect risk
        probability, prediction, risk_category = predict_defect_risk(features)

       # Store the results
        results.append({
        "commit_sha": commit_sha,
        "features": features,
        "probability": probability,
        "risk_category": risk_category,
        "prediction": prediction
                })

    return results

def rank_commits_by_risk(results):
    ranked_results = sorted(
        results,
        key=lambda result: result["probability"],
        reverse=True
    )

    return ranked_results


def export_results_to_csv(results, filename="reposage_results.csv"):

    if not results:
        print("No results available to export.")
        return

    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                    "rank",
                    "commit_sha",
                    "probability",
                   "risk_category",
                  "prediction"
]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for rank, result in enumerate(results, start=1):
                writer.writerow({
    "rank": rank,
    "commit_sha": result["commit_sha"],
    "probability": round(result["probability"], 4),
    "risk_category": result["risk_category"],
    "prediction": result["prediction"]
})
        print(f"Results exported successfully to {filename}")

    except (PermissionError, OSError) as error:
        print(f"CSV export failed: {error}")



# Display multi-commit analysis results
def display_commit_results(results):

    print("\nRepoSage Multi-Commit Analysis")
    print("=" * 90)

    if not results:
        print("No commits found in this repository.")
        return

    for index, result in enumerate(results, start=1):

        print(f"\nCommit {index}")
        print("-" * 40)

        print("Commit SHA:", result["commit_sha"])
        print(
            f"Defect probability: "
            f"{result['probability']:.4f}"
        )
        print("Risk Category:", result["risk_category"])
        print("Prediction:", result["prediction"])

        if result["prediction"] == 1:
            print("Assessment: Potentially defect-inducing")
        else:
         print("Assessment: Not classified as defect-inducing")  

        print("Features:", result["features"])

    print("\n" + "=" * 90)
    print("Total commits analyzed:", len(results))



# Main function: coordinates single and multi-commit workflows
def main():

    # Validate command-line arguments
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "Single commit: py -3.11 reposage_extract.py "
            "<repository_path> [commit_sha]\n"
            "Multiple commits: py -3.11 reposage_extract.py "
            "<repository_path> --last <N>"
        )
        return

    # Get repository path
    repo_path = Path(sys.argv[1]).expanduser().resolve()

    if not repo_path.exists():
        print("Error: Repository path does not exist!")
        return

    if not repo_path.is_dir():
        print("Error: Provided path is not a directory!")
        return

    # Validate Git repository
    try:
        repo_status = run_git_command(
            ["rev-parse", "--is-inside-work-tree"],
            repo_path
        )

        if repo_status.strip() != "true":
            print("Error: Not a valid Git working repository!")
            return

    except subprocess.CalledProcessError:
        print("Error: Not a valid Git repository!")
        return

    print("RepoSage Git repository found successfully!")

    try:

        # Multi-commit analysis mode
        if len(sys.argv) >= 3 and sys.argv[2] == "--last":

            if len(sys.argv) != 4:
                print(
                    "Usage: py -3.11 reposage_extract.py "
                    "<repository_path> --last <N>"
                )
                return

            try:
                limit = int(sys.argv[3])
            except ValueError:
                raise ValueError(
                    "Commit limit must be a valid integer."
                )

            if limit <= 0:
                raise ValueError(
                    "Commit limit must be greater than zero."
                )

            print(f"Analyzing the latest {limit} commits...")

            results = analyze_recent_commits(repo_path, limit)

            ranked_results = rank_commits_by_risk(results)

            display_commit_results(ranked_results)

            export_results_to_csv(ranked_results)

        # Single-commit analysis mode
        else:

            if len(sys.argv) > 3:
                print("Error: Too many command-line arguments.")
                return

            # Get requested commit or default to HEAD
            commit_sha = (
                sys.argv[2] if len(sys.argv) == 3 else None
            )

            latest_commit = get_commit_sha(
                repo_path, commit_sha
            )

            print("Latest commit:", latest_commit)

            # Extract commit features
            features = extract_commit_features(
                repo_path, latest_commit
            )

            print("\nFeature dictionary:")
            print(features)

            # Perform change-impact analysis
            changed_files = get_changed_files(
    repo_path, latest_commit
)

            dependency_graph = build_dependency_graph(repo_path)

            impacted_files = find_impacted_files(
    changed_files, dependency_graph
)

            display_impact_analysis(
    changed_files, impacted_files
)


            # Predict defect risk
            probability, prediction, risk_category = (
                predict_defect_risk(features)
            )

            # Generate SHAP explanation
            expected_value, explanations = (
                explain_defect_risk(features)
            )

            # Display SHAP explanation
            print("\n===== SHAP Explanation =====")
            print("Expected model output:", expected_value)

            for item in explanations:

                if item["shap_value"] > 0:
                    direction = "Increases defect risk"
                else:
                    direction = "Decreases defect risk"

                print(
                    f'{item["feature"]}: '
                    f'value={item["feature_value"]}, '
                    f'SHAP={item["shap_value"]:.5f}, '
                    f'{direction}'
                )

            # Display prediction
            print("\nRepoSage Prediction:")
            print(f"Defect probability: {probability:.4f}")
            print(f"Risk Category: {risk_category}")
            print(f"Prediction: {prediction}")

            if prediction == 1:
                print(
                    "This commit is classified as "
                    "potentially defect-inducing."
                )
            else:
                print(
                    "This commit is classified as "
                    "not defect-inducing."
                )

            print("test_ratio:", features["test_ratio"])

    except subprocess.CalledProcessError as error:
        print("Git command failed:", error)

    except ValueError as error:
        print("Error:", error)

    except FileNotFoundError as error:
        print("Required project file not found:", error)




# Entry point
if __name__ == "__main__":
    main()

