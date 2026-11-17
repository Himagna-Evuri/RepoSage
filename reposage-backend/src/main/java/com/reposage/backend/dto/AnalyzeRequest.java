
package com.reposage.backend.dto;

public record AnalyzeRequest(
        String repoPath,
        String commitSha
) {
}
