import os

# GitAuto's own reference templates fed to Claude for generating coverage workflows
GITAUTO_COVERAGE_WORKFLOW_TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "services",
    "github",
    "workflows",
    "templates",
)

GHA_WORKFLOW_DIR = ".github/workflows"

# CI config files for non-GitHub-Actions systems (path, display name)
CI_CONFIG_FILES = [
    ("appveyor.yml", "AppVeyor"),
    ("azure-pipelines.yml", "Azure Pipelines"),
    ("bitbucket-pipelines.yml", "Bitbucket Pipelines"),
    (".buildkite/pipeline.yml", "Buildkite"),
    ("buildkite.yml", "Buildkite"),
    (".circleci/config.yml", "CircleCI"),
    (".gitlab-ci.yml", "GitLab CI"),
    ("Jenkinsfile", "Jenkins"),
    (".travis.yml", "Travis CI"),
]
