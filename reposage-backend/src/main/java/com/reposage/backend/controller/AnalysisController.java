
package com.reposage.backend.controller;

import com.reposage.backend.dto.AnalyzeRequest;
import com.reposage.backend.service.PythonAnalysisService;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:5173")
public class AnalysisController {

    private final PythonAnalysisService pythonAnalysisService;

    public AnalysisController(
            PythonAnalysisService pythonAnalysisService) {
        this.pythonAnalysisService = pythonAnalysisService;
    }

    // Analyze a single commit
    @PostMapping(
            value = "/analyze",
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<?> analyzeRepository(
            @RequestBody AnalyzeRequest request) {

        try {
            String result = pythonAnalysisService.analyzeRepository(
                    request.repoPath(),
                    request.commitSha()
            );

            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(result);

        } catch (IllegalArgumentException error) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", error.getMessage()));

        } catch (Exception error) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of(
                            "error",
                            "An unexpected error occurred during analysis."
                    ));
        }
    }

    // Analyze multiple recent commits
    @GetMapping(
            value = "/analyze/recent",
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<?> analyzeMultipleCommits(
            @RequestParam String repoPath,
            @RequestParam(defaultValue = "10") int limit) {

        try {
            String result = pythonAnalysisService.analyzeMultipleCommits(
                    repoPath,
                    limit
            );

            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(result);

        } catch (IllegalArgumentException error) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", error.getMessage()));

        } catch (Exception error) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of(
                            "error",
                            "An unexpected error occurred during analysis."
                    ));
        }
    }
}
