
package com.reposage.backend.service;

import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class PythonAnalysisService {

    private static final String PYTHON_COMMAND = "py";

    private static final String PYTHON_SCRIPT =
            "C:/Users/himag/OneDrive/Documents/RepoSage/reposage_api.py";

    // Analyze a single commit
    public String analyzeRepository(String repoPath, String commitSha)
            throws Exception {

        List<String> command = new ArrayList<>();

        command.add(PYTHON_COMMAND);
        command.add("-3.11");
        command.add(PYTHON_SCRIPT);
        command.add(repoPath);
        command.add(commitSha);

        return executePythonCommand(command);
    }

    // Analyze multiple recent commits
    public String analyzeMultipleCommits(String repoPath, int limit)
            throws Exception {

        if (limit <= 0) {
            throw new IllegalArgumentException(
                    "Commit limit must be greater than zero."
            );
        }

        List<String> command = new ArrayList<>();

        command.add(PYTHON_COMMAND);
        command.add("-3.11");
        command.add(PYTHON_SCRIPT);
        command.add(repoPath);
        command.add("--last");
        command.add(String.valueOf(limit));

        return executePythonCommand(command);
    }

    // Execute Python and capture its JSON response
    private String executePythonCommand(List<String> command)
            throws Exception {

        ProcessBuilder processBuilder = new ProcessBuilder(command);
        processBuilder.redirectErrorStream(true);

        Process process = processBuilder.start();

        StringBuilder output = new StringBuilder();

        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(process.getInputStream()))) {

            String line;

            while ((line = reader.readLine()) != null) {
                output.append(line);
            }
        }

        int exitCode = process.waitFor();

        if (exitCode != 0) {

            String errorOutput = output.toString();

            // Extract the error message returned by Python
            Pattern pattern = Pattern.compile(
                    "\"error\"\\s*:\\s*\"([^\"]*)\""
            );

            Matcher matcher = pattern.matcher(errorOutput);

            if (matcher.find()) {
                throw new IllegalArgumentException(matcher.group(1));
            }

            // Handle unexpected Python execution failures
            throw new RuntimeException(
                    "Python analysis failed. Please try again."
            );
        }

        return output.toString();
    }
}
