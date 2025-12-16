# GitAuto AI

## 1. What is GitAuto

[GitAuto](https://gitauto.ai) is a GitHub coding agent that opens pull requests from backlog tickets for software engineering managers to complete more bug fixes and feature requests. Assign tasks to GitAuto first, and have people work on more complex tickets.

- Want to give GitAuto a try? Go to [GitAuto installation](https://github.com/apps/gitauto-ai).
- Want to see demo videos? Go to [GitAuto YouTube](https://www.youtube.com/@gitauto).
- Want to know more about GitAuto? Go to [GitAuto homepage](https://gitauto.ai).
- Want to chat about your use case? Feel free to contact us at [email](mailto:info@gitauto.ai), [admin](https://github.com/hiroshinishio), [X](https://x.com/gitautoai), or [LinkedIn](https://www.linkedin.com/company/gitauto/).

## 2. How to use GitAuto

1. Install GitAuto to your repositories from [GitHub Marketplace](https://github.com/apps/gitauto-ai).
   1. Choose the repositories where you want to use GitAuto.
   2. You can change the repositories later.
2. Create a new issue, then GitAuto shows up in the issue comment.
   1. Or create a new issue with a template.
   2. Or pick up an existing issue.
3. Check the checkbox to assign GitAuto to the issue, then GitAuto starts to work on the issue.
   1. Or label the issue with `gitauto`, which also assigns GitAuto to the issue.
4. Check the progress of GitAuto in the bottom of the issue comment. You will get a notification once GitAuto completes the PR.
5. Review the PR and merge it if it looks good.
6. If not, update the issue with more details and re-run GitAuto by checking the checkbox again.

## 3. How to run GitAuto locally

### 3-1. Create your GitHub app for local development

1. Go to <https://github.com/settings/apps>
2. Click `New GitHub App`.
3. Fill in `GitHub App name` like `GitAuto Dev {Your Name}` e.g. `GitAuto Dev John`.
4. Fill in `Homepage URL` like `http://localhost:8000`.
5. Fill in `Webhook URL` like `https://your-name.ngrok.dev/webhook`. GitHub requires HTTPS for the webhook URL, so we need to use ngrok or something similar instead of `localhost`. GitHub sends webhook events (e.g. an issue is created) to the webhook URL and ngrok tunnels to localhost. You can update this URL later after setting up the ngrok tunnel.
6. Fill in `Webhook secret` with your preferred secret.
7. Fill in `Repository permissions`
   - `Actions`: Read & Write
   - `Checks`: Read & Write
   - `Commit statuses`: Read & Write
   - `Contents`: Read & Write
   - `Issues`: Read & Write
   - `Pull requests`: Read & Write
   - `Secrets`: Read & Write
   - `Variables`: Read & Write
   - `Workflows`: Read & Write
8. Fill in `Organization permissions`
   - `Members`: Read-only
9. Fill in `Subscribe to events`
   - `Installation target`: Checked
   - `Metadata`: Checked
   - `Check run`: Checked
   - `Commit comment`: Checked
   - `Issue comment`: Checked
   - `Issues`: Checked
   - `Pull request`: Checked
   - `Pull request review`: Checked
   - `Pull request review comment`: Checked
   - `Pull request review thread`: Checked
   - `Push`: Checked
   - `Status`: Checked
10. Check `Where can this GitHub App be installed?` and select `Only on this account`.
11. Click `Create GitHub App`
12. Click `Generate a private key` and download the private key.

### 3-2. Install your GitHub app to a repository where you want to test

1. Go to [GitHub Apps](https://github.com/settings/apps) in the GitHub Developer Settings.
2. Choose your local GitHub app and go to the `Install App` page.
3. Install the app to the repository where you want to test.
4. Or directly go to `https://github.com/settings/apps/{your-github-app-name}/installations` such as `https://github.com/settings/apps/gitauto-for-dev/installations`.

### 3-3. Set up ngrok configuration

GitHub allows only a HTTPS URL for webhook events, so we need to use ngrok or something similar service to tunnel/forward the GitHub webhook events to your localhost.

1. Create a new ngrok configuration file `ngrok.yml` in the root directory. It should contain `authtoken: YOUR_NGROK_AUTH_TOKEN` and `version: 2`.
2. Get your own auth token from [Your Authtoken on the dashboard](https://dashboard.ngrok.com/get-started/your-authtoken) or ask [@hiroshinishio](https://github.com/hiroshinishio) about the paid ngrok auth token.
3. Get your own endpoint URL from [Endpoints on the dashboard](https://dashboard.ngrok.com/endpoints). **Each developer needs their own unique domain** (e.g., `wes.ngrok.dev`, `john.ngrok.dev`) to avoid conflicts.
4. Update the `start.sh` script to use your specific ngrok domain.

### 3-4. Managing Git branches

To update your local branch with the latest changes from our default branch (`main`), run the following commands:

```bash
git checkout your-branch
git pull origin main
```

For example:

```bash
git checkout wes
git pull origin main
```

If you have uncommitted changes, stash them first:

```bash
git stash        # Save changes
git pull origin main
git stash pop    # Reapply changes
```

### 3-5. Get the `.env` file

1. Ask for the `.env` file from [@hiroshinishio](https://github.com/hiroshinishio).
2. Put the `.env` file in the root directory.

### 3-6. How to encode a GitHub app private key to base64

In `.env` file, you need to set your own `GH_PRIVATE_KEY`. Here's the step:

1. Go to <https://github.com/settings/apps>. Choose your local GitHub app.
2. Go to `General` tab on the left.
3. Scroll down to `Private key` section. Generate a private key.
4. Run `base64 -i your/path/to/private-key.pem` to encode the private key to base64.
5. Copy the output and paste it in the `GH_PRIVATE_KEY` field in your `.env` file.

### 3-7. How to run the code

1. **Update the start script** with your ngrok domain:

   ```bash
   # Edit start.sh and change this line:
   ngrok http --config=ngrok.yml --domain=your-name.ngrok.dev 8000
   ```

2. **Make the start script executable:**

   ```bash
   chmod +x start.sh
   ```

3. **Run the development environment:**

   ```bash
   ./start.sh
   ```

This script will automatically:

- Create and activate virtual environment (if needed)
- Install dependencies (if needed)
- Start ngrok tunnel with your specific domain
- Start FastAPI server with visible logs
- Clean up both services when you press Ctrl+C

**Important for multiple developers**: Each developer must use a different ngrok domain in their `start.sh` script to avoid conflicts. For example:

- Developer 1: `wes.ngrok.dev`
- Developer 2: `john.ngrok.dev`

### 3-8. Success indicators

When everything is working correctly, you should see:

**From start.sh:**

- ✅ Virtual environment activation
- ✅ ngrok tunnel started with your domain
- ✅ FastAPI server starting with logs below

**FastAPI server:**

- Server running on `http://localhost:8000`
- Watching for file changes (auto-reload enabled)
- No error messages during startup

If you see any errors, check:

- `.env` file is present and configured
- `ngrok.yml` is configured with your auth token
- Your ngrok domain is available
- Port 8000 is not already in use

### 3-9. How to view AWS Lambda logs

When GitAuto runs in production, it uses AWS Lambda. To view logs and debug issues:

**Using AWS CLI:**

```bash
aws logs tail /aws/lambda/pr-agent-prod --follow | grep -v -E "(START RequestId|END RequestId|REPORT RequestId)" | sed -E 's/[0-9]{4}\/[0-9]{2}\/[0-9]{2}\/\[\$LATEST\][a-f0-9]+ //'
```

**Using AWS Console:**

1. Go to [AWS CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Navigate to `Logs` > `Log groups`
3. Find `/aws/lambda/pr-agent-prod` log group
4. Click on the latest log stream to view real-time logs
5. Use the filter box to exclude system messages: `- "START RequestId" - "END RequestId" - "REPORT RequestId"`

### 3-10. GitHub Check Suite Architecture

```text
Pull Request #123
└── Commit (sha: abc123)
    └── check_suite
        ├── GitHub Actions (GitAuto)
        │   ├── Workflow: "ci" (.github/workflows/ci.yml)
        │   │   ├── Job: build → check_run: "build"
        │   │   ├── Job: test → check_run: "test"
        │   │   └── Job: lint → check_run: "lint"
        │   └── Workflow: "deploy" (.github/workflows/deploy.yml)
        │       └── Job: deploy → check_run: "deploy"
        │
        └── CircleCI (Foxquilt)
            ├── Workflow: "ci"
            │   ├── Job: build
            │   ├── Job: test
            │   ├── Job: lint
            │   └── check_run: "ci" (represents entire workflow)
            └── Workflow: "deploy"
                ├── Job: deploy
                └── check_run: "deploy" (represents entire workflow)
```

### 3-11. Other information

For communication (Slack), database (Supabase), payment (Stripe), and serverless functions (AWS Lambda), provide your preferred email to [@hiroshinishio](https://github.com/hiroshinishio) so that he can invite you to the local development environment.
