# CircleCI Integration

## Hierarchy

```text
GitHub Project: gh/{owner}/{repo}
└── GitHub Pull Request #123          (1 Project : N PRs)
    └── GitHub Commit (sha: abc123)   (1 PR : N Commits)
        └── GitHub check_suite        (1 Commit : 1 check_suite per CI app)
            └── CircleCI Pipeline #456  (1 check_suite : 1 Pipeline)
                ├── CircleCI Workflow: "build-and-test" → GitHub check_run  (1 Pipeline : N Workflows, 1 Workflow : 1 check_run)
                │   ├── CircleCI Job: "install-deps" (success)       (1 Workflow : N Jobs)
                │   ├── CircleCI Job: "lint" (success)
                │   ├── CircleCI Job: "test" (failed)
                │   └── CircleCI Job: "build" (blocked)
                └── CircleCI Workflow: "deploy" → GitHub check_run
                    └── CircleCI Job: "deploy-prod" (not started)
```
