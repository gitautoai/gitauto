# GitAuto AI

## What we do

We provide an AI agent that automatically generates pull requests from issues for backend code, enabling engineers to concentrate on core development.

## Who we target

Here is the list of our ICP (Ideal Customer Profile):

- **Platform**: GitHub users not GitLab or Bitbucket users
- **Size**: Individual developers or small teams in SMEs (Small and Medium-sized Enterprises) less than 100 employees not large enterprises due to compliance, security, and long sales cycle.
- **Geolocation**: San Francisco Bay Area in the United States
- **Language**: Backend code like Python and JavaScript / TypeScript

## What we measure

- **Merge Rate**: Aim for 90% (PRs merged / PRs created).
- **Churn Rate**: Aim for <5% (Unsubscriptions / (exisiting subscriptions + new subscriptions)).

## What the user workflow is

### 1. User preparation

First, users need to take the following steps to use our service:

- **User**: Visit our homepage or GitHub marketplace.
- **User**: Sign up with GiHub using the GitHub Authentication API.
- **User**: Install our app to repositories where the user wants to.

### 2. Demonstration on installation

Then, we demonstrate how to create a pull request from an issue:

- **AI**: Automatically creates an issue with a template in the repository.
- **AI**: Assigns itself as the assignee for that issue.
- **AI**: Reads the issue and comment on its current understanding of the issue.
- **AI**: Proposes a solution to that issue.
- **AI**: Presents a link to begin creating a PR.

### 3. Create an issue - Agree on a solution

- **User**: Assigns our AI to an issue. (The AI won't do anything until it's assigned so as not to disturb the user.)
- **AI**: Reads the issue and comment on its current understanding of the issue.
- **AI**: Proposes a solution to that issue.
- **AI**: Presents a link to begin creating a PR.
- **User**: Comments back to the AI if there's any disagreement.
- **User**: Clicks the link if the user agrees with the AI's proposal.

### 4. Create a PR - Ask for a review

- **AI**: Creates a new branch for that issue.
- **AI**: Inputs the content of that issue (text only).
- **AI**: Inputs the file tree of the repository.
- **AI**: Reads any files that seem relevant.
- **AI**: Suggests code changes in `the Unified Diff Format with no context lines`.
- **AI**: Double check for unnecessary lines that could cause bugs
- **AI**: Patches the code with the suggested changes.
- **AI**: Stages those file changes to the local branch.
- **AI**: Commits those file changes with a message in a format (e.g. `AI: Fixes #123: Add a new feature`) to the local branch.
- **AI**: Pushes those files to the remote branch from the local branch.
- **AI**: Identifies the base branch such as `main`.
- **AI**: Creates a new pull request to that base branch.
- **AI**: Write a description of that pull request in a format.
- **AI**: Assigns the user as a reviewer who clicked the link.

### 5. Review the PR - Merge the PR

- **User**: Reviews the PR.
- **User**: Comments on the PR if there's any disagreement.
- **AI**: Reads the comment and comments back to the user if there's any ambiguity.
- **AI**: Makes extra commits based on the user's comments.
- **User**: Approves the PR if the user is satisfied with the changes.
- **User**: Merges the PR if the user is satisfied with the changes.

## How to develop locally

### Create your GitHub app for local development

### Install your GitHub app to the repository where you want to test

1. Go to GitHub Apps in the GitHub Developer Settings.
2. Or go to `https://github.com/settings/apps/{your-github-app-name}/installations` such as `https://github.com/settings/apps/gitauto-for-dev/installations`.

### Tunnel to localhost with ngrok

1. Create a new ngrok configuration file `ngrok.yml` in the root directory. It should contain `authtoken: YOUR_NGROK_AUTH_TOKEN` and `version: 2`.
2. Ask @hiroshinishio about the ngrok auth token.
3. Open a new terminal in the root directory in VSCode.
4. Run `ngrok http --config=ngrok.yml --domain=gitauto.ngrok.dev 8000`.
5. ngrok will generate a URL `https://gitauto.ngrok.dev` that tunnels to `http://localhost:8000`.
6. Use `https://gitauto.ngrok.dev/webhook` as the webhook URL in the GitHub app settings as GitHub requires HTTPS for the webhook URL instead of HTTP.
7. You can check this setting in ngrok dashboard at `https://dashboard.ngrok.com/cloud-edge/domains`.

### Create a virtual environment

1. Run `deactivate` to deactivate the virtual environment if you have activated it and not sure where you are.
2. Run `rm -rf venv` to remove the virtual environment if you have created it and not sure what's in it.
3. Run `python3 -m venv --upgrade-deps venv` to create a virtual environment.
4. Run `source venv/bin/activate` to activate the virtual environment. You will see `(venv)` in the terminal. Note that you need to activate the virtual environment every time you open a new terminal.
5. Run `which python`, `which pip`, and `python --version` to check the Python version and make sure it points to the virtual environment.
6. Run `pip install -r requirements.txt` to install the dependencies.

In short, instead, run `[ ! -d "venv" ] && python -m venv venv; source venv/bin/activate && pip install -r requirements.txt && pip list --outdated --format=columns | awk 'NR>2 {print $1}' | xargs -n1 pip install -U && pip freeze > requirements.txt` at the project root.

### How to run the code

1. Run `pip install -r requirements.txt` to install the dependencies.
2. Ask for the `.env` file from the team and put it in the root directory.
3. Run `uvicorn main:app --reload --port 8000` to start the ASGI server and run `main.py` with `app` as the FastAPI instance. `--reload` is for auto-reloading the server when the code changes.

### How to encode a GitHub app private key to base64

GitHub app private key is in `.env` file. So basically you don't need to do this. But if you need to do this, follow the steps below. (Like when you create a new GitHub app and need to encode the private key to base64.)

1. Run `base64 -i /Users/rwest/Downloads/gitauto-ai-for-stg.2024-03-07.private-key.pem` to encode the private key to base64. Change the path to the actual path of your private key.
2. Copy the output and paste it in the `PRIVATE_KEY` field in the `.env` file.

## How to test in the development environment

Once you have developed the code locally and satisfied with the result, you must test the code in the development environment before merging the code to the main branch and deploying it to the production environment. AWS Lambda OS is `Amazon Linux 2`, which is based on `Fedora` and `CentOS` but optimized for AWS Lambda and not identical to your OS. So you need to test the code in the development environment to make sure it works as expected.

### Create your development GitHub app

First, you need to create your personal development GitHub app.

1. Go to GitHub Apps in the GitHub Developer Settings.
2. Create a new GitHub app for your development environment to your `personal` account instead of the `organization` account.
3. Copy the production settings to your development settings.
4. Set a temporary webhook URL like `https://gitauto/temp/webhook` in the `Webhook URL` section. You will change this to the actual URL later after setting up the development environment in AWS Lambda Functions.
5. We will find a way to automate this process in the future.

### Create your development environment in Supabase

First, you need to create your development `organization` and `project` in Supabase.

1. Go to [Supabase](https://app.supabase.io/).
2. Create your Supabase organization and project for the development environment.
3. Ask @hiroshinishio about how to migrate the database schema to your development environment project. You need to pass Supabase `URL` and `Password` to @hiroshinishio.
4. We will find a way to automate this process in the future.

### AWS Lambda Functions

Then, you need to create/update your development environment in AWS Lambda Functions.

1. Ask @hiroshinishio to invite you to the AWS Management Console.
2. Go to [AWS Lambda Functions](https://us-west-1.console.aws.amazon.com/lambda/home?region=us-west-1#/functions) in the AWS Management Console.
3. Select your function like `gitauto-ai-for-stg`.
4. Go to the configuration of the function in the `Configuration` tab.
5. Go to the `Environment variables` section.
6. Update the variables such as `GH_APP_ID`, `GH_PRIVATE_KEY`, `GH_WEBHOOK_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_URL`.
7. Update the GitHub development app settings with the actual webhook URL like `https://dzisvvf4lhztl75moorb5dohma0hirag.lambda-url.us-west-1.on.aws/webhook`.
8. We will find a way to automate this process in the future.

### Let's test

1. Install your development GitHub app to the repository where you want to test.
2. Confirm that installation event and the log is shown in the [AWS CloudWatch Logs](https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#logsV2:log-groups).
3. Push the code to your working branch.
4. GitHub Actions will deploy the code to the development environment automatically which is hosted on AWS Lambda.
5. You will be notified by the Slack bot created by @hiroshinishio.

## How to access Supabase from your terminal

1. Run `brew install postgresql` to install PostgreSQL if you haven't installed it yet.
2. Run `brew services start postgresql` to start the PostgreSQL service if you haven't started it yet.
3. Run `psql --version` to check the version of PostgreSQL and make sure it's installed correctly.
4. Go to [Supabase](https://supabase.com/dashboard/project/awegqusxzsmlgxaxyyrq/settings/database) and copy PSQL connection string.
5. It should be like `psql -h aws-0-us-west-1.pooler.supabase.com -p 6543 -d postgres -U postgres.xxxxxx`.
6. Type the password when prompted. You need to ask @hiroshinishio for the password.

## Others

- When you want to create a new AWS key ID, run `aws iam create-access-key`. See [this article](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user_manage_add-key.html).
- When you want to delete an old AWS key ID, run `aws iam delete-access-key --access-key-id YOUR_ACCESS_KEY_ID`. See [this article](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user_manage_delete-key.html).

## What the tech stack is

- Main: Python
- Framework: Fast API
- Runtime: Uvicorn
- Hosting: AWS Lambda Functions
- DB: Supabase
- Payment: Stripe
- Unit Testing: Pytest
