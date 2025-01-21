# GitAuto AI
# Table of Contents

1. [What is GitAuto](#1-what-is-gitauto)
2. [How to use GitAuto](#2-how-to-use-gitauto)
3. [How to run GitAuto locally](#3-how-to-run-gitauto-locally)
   1. [Create your GitHub app for local development](#3-1-create-your-github-app-for-local-development)
   2. [Install your GitHub app to a repository where you want to test](#3-2-install-your-github-app-to-a-repository-where-you-want-to-test)
   3. [Tunnel GitHub webhook events to your localhost with ngrok](#3-3-tunnel-github-webhook-events-to-your-localhost-with-ngrok)
   4. [Create a virtual Python dependency environment in your local machine](#3-4-create-a-virtual-python-dependency-environment-in-your-local-machine)
   5. [Get the .env file](#3-5-get-the-env-file)
   6. [How to encode a GitHub app private key to base64](#3-6-how-to-encode-a-github-app-private-key-to-base64)
   7. [How to run the code](#3-7-how-to-run-the-code)
   8. [Other information](#3-8-other-information)
![Coverage Badge](https://img.shields.io/badge/coverage-80%25-green)

## 1. What is GitAuto

[GitAuto](https://gitauto.ai) is a GitHub coding agent that opens pull requests from backlog tickets for software engineering managers to complete more bug fixes and feature requests. Assign tasks to GitAuto first, and have people work on more complex tickets.

- Want to give GitAuto a try? Go to [GitAuto installation](https://github.com/apps/gitauto-ai).
- Want to see demo videos? Go to [GitAuto YouTube](https://www.youtube.com/@gitautoai).
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
5. Fill in `Webhook URL` like `https://gitauto.ngrok.dev/webhook`. GitHub requires HTTPS for the webhook URL, so we need to use ngrok or something similar instead of `localhost`. GitHub sends webhook events (e.g. an issue is created) to the webhook URL and ngrok tunnels to localhost. You can update this URL later after setting up the ngrok tunnel.
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

### 3-3. Tunnel GitHub webhook events to your localhost with ngrok

GitHub allows only a HTTPS URL for webhook events, so we need to use ngrok or something similar service to tunnel/forward the GitHub webhook events to your localhost.

1. Create a new ngrok configuration file `ngrok.yml` in the root directory. It should contain `authtoken: YOUR_NGROK_AUTH_TOKEN` and `version: 2`.
2. Get your own auth token from [Your Authtoken on the dashboard](https://dashboard.ngrok.com/get-started/your-authtoken) or ask [@hiroshinishio](https://github.com/hiroshinishio) about the paid ngrok auth token.
3. Get your own endpoint URL from [Endpoints on the dashboard](https://dashboard.ngrok.com/endpoints). For free users, it varies every time you create a new ngrok tunnel. (Yes, it is really annoying.)
4. Open a new terminal in the root directory in your IDE.
5. Run `ngrok http --config=ngrok.yml --domain={your-endpoint-url} 8000`. Replace `{your-endpoint-url}` with your own endpoint URL, so it looks like `ngrok http --config=ngrok.yml --domain=gitauto.ngrok.dev 8000`.
6. ngrok starts tunneling to `http://localhost:8000`.
7. Use `{your-endpoint-url}/webhook` like `https://gitauto.ngrok.dev/webhook` as the webhook URL in the GitHub app settings as GitHub requires HTTPS for the webhook URL instead of HTTP.

### 3-4. Create a virtual Python dependency environment in your local machine

1. Run `deactivate` to deactivate the virtual environment if you have activated it and not sure where you are.
2. Run `rm -rf venv` to remove the virtual environment if you have created it and not sure what's in it.
3. Run `python3 -m venv --upgrade-deps venv` to create a virtual environment.
4. Run `source venv/bin/activate` to activate the virtual environment. You will see `(venv)` in the terminal. Note that you need to activate the virtual environment every time you open a new terminal.
5. Run `which python`, `which pip`, and `python --version` to check the Python version and make sure it points to the virtual environment.
6. Run `pip install -r requirements.txt` to install the dependencies.

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

1. Run `uvicorn main:app --reload --port 8000 --log-level warning` to start the ASGI server and run `main.py` with `app` as the FastAPI instance.
   1. `--reload` is for auto-reloading the server when the code changes.
   2. `--log-level warning` is to suppress the INFO logs.
2. Let's see if it works and there are no errors! Here's the success message if your log-level is set to `info` (default):

```zsh
(venv) rwest@Roshis-MacBook-Pro gitauto % uvicorn main:app --reload --port 8000
INFO:     Will watch for changes in these directories: ['/Users/rwest/Repositories/gitauto']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [63742] using WatchFiles
INFO:     Started server process [63744]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3-8. Other information

For communication (Slack), database (Supabase), payment (Stripe), and serverless functions (AWS Lambda), provide your preferred email to [@hiroshinishio](https://github.com/hiroshinishio) so that he can invite you to the local development environment.
