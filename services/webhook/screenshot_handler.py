# Standard imports
import os
import shutil
import tempfile
from time import sleep
from urllib.parse import quote, urlparse

# Third party imports
import boto3
from playwright.async_api import async_playwright

# Local imports
from constants.general import GITHUB_APP_USER_NAME
from services.aws.clients import AWS_REGION
from services.git.clone_repo import clone_repo
from services.git.git_manager import fetch_branch, get_current_branch, switch_to_branch
from services.github.comments.create_comment import create_comment
from services.github.comments.delete_comment import delete_comment
from services.github.comments.get_all_comments import get_all_comments
from services.github.installations.get_installation_access_token import (
    get_installation_access_token,
)
from services.github.pulls.get_pull_request_file_changes import (
    get_pull_request_file_changes,
)
from services.supabase.local_server import start_local_server
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def get_url_filename(url: str) -> str:
    parsed_url = urlparse(url)
    path = parsed_url.path.strip("/")
    if not path:
        return "index.png"
    return f"{path}.png"


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def capture_screenshots(urls: list[str], output_dir: str) -> None:
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
                "--single-process",
            ]
        )
        context = await browser.new_context()
        page = await context.new_page()
        viewport_size = {"width": 1512, "height": 982}
        await page.set_viewport_size(viewport_size)
        print(f"\nOpened browser and set viewport size to `{viewport_size}`")

        for url in urls:
            file_name = get_url_filename(url)
            file_path = os.path.join(output_dir, file_name)

            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(10000)
            await page.screenshot(path=file_path, full_page=True)
            print(f"\nCaptured screenshot for `{url}`")
            print(f"Saved screenshot to `{file_path}`")

        await browser.close()
        print("Closed browser")


@handle_exceptions(raise_on_error=True)
def upload_to_s3(file_path: str, s3_key: str) -> str:
    # S3 and IAM access policies are attached to the Lambda Function role so we don't need to specify AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION
    # https://us-east-1.console.aws.amazon.com/iam/home?region=us-west-1#/roles/details/pr-agent-prod-role-5hjanfe3?section=permissions
    s3_client = boto3.client("s3")
    aws_s3_bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    if aws_s3_bucket_name is None:
        raise ValueError("AWS_S3_BUCKET_NAME is not set")
    extra_args = {"ContentType": "image/png"}
    s3_client.upload_file(file_path, aws_s3_bucket_name, s3_key, ExtraArgs=extra_args)
    print(f"Uploaded to S3: {quote(s3_key)}")
    return f"https://{aws_s3_bucket_name}.s3.{AWS_REGION}.amazonaws.com/{quote(s3_key)}"


@handle_exceptions(raise_on_error=True)
def find_all_html_pages(repo_dir: str) -> list[str]:
    all_paths = set()

    for root, _, files in os.walk(repo_dir):
        for file in files:
            if file.endswith((".html", ".tsx", ".jsx")):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_dir)

                # Handle HTML files
                if file.endswith(".html"):
                    path = "/" + rel_path.replace("index.html", "").rstrip("/")
                    all_paths.add(path or "/")
                    print(f"Found HTML file: `{file_path}`")

                # Handle Next.js App Router
                elif "app/" in rel_path and file.endswith((".tsx", ".jsx")):
                    # Skip layout files as they don't represent routes
                    if file in ("layout.tsx", "layout.jsx"):
                        print(f"Found Next.js App Router file: `{file_path}`")
                        continue
                    
                    # Only process page files
                    if file in ("page.tsx", "page.jsx"):
                        path = rel_path.rsplit("app/", maxsplit=1)[-1]
                        # Remove the page file name to get the directory path
                        path = path.replace("/page.tsx", "").replace("/page.jsx", "")
                        path = path.replace("page.tsx", "").replace("page.jsx", "")
                        # Convert to route path
                        route_path = "/" + path.rstrip("/") if path else "/"
                        all_paths.add(route_path)
                        print(f"Found Next.js App Router file: `{file_path}`")

                # Handle Next.js Pages Router
                elif "pages/" in rel_path and file.endswith((".tsx", ".jsx")):
                    path = (
                        rel_path.rsplit("pages/", maxsplit=1)[-1]
                        .replace("index.tsx", "")
                        .replace("index.jsx", "")
                        .replace(".tsx", "")
                        .replace(".jsx", "")
                    )
                    all_paths.add("/" + path.rstrip("/"))
                    print(f"Found Next.js Pages Router file: `{file_path}`")

    return list(all_paths)


@handle_exceptions(raise_on_error=True)
def get_target_paths(file_changes: list[dict[str, str]], repo_dir: str = None):
    has_css_changes = any(
        change.get("filename", "").endswith((".css", ".scss", ".sass", ".less"))
        for change in file_changes
    )

    # If there are any CSS changes, scan all pages in the repository
    if has_css_changes and repo_dir:
        return find_all_html_pages(repo_dir)

    changed_paths: set[str] = set()
    for i, change in enumerate(file_changes):
        print(f"Processing {i + 1} of {len(file_changes)}")
        file_path = change.get("filename", "")
        print(f"Processing file: {file_path}")

        # HTML files - direct path conversion
        if file_path.endswith(".html"):
            path = "/" + file_path.replace("index.html", "").rstrip("/")
            changed_paths.add(path or "/")
            print(f"Found HTML file: {file_path}")
            print(f"Affected path: {path}")

        # Next.js App Router
        elif "app/" in file_path and (
            file_path.endswith(".tsx") or file_path.endswith(".jsx")
        ):
            # Skip layout files as they don't represent routes
            filename = os.path.basename(file_path)
            if filename in ("layout.tsx", "layout.jsx"):
                print(f"Found Next.js App Router file: {file_path}")
                continue
            
            # Only process page files
            if filename in ("page.tsx", "page.jsx"):
                path = (
                    file_path.split("app/")[-1]
                    .replace("/page.tsx", "")
                    .replace("/page.jsx", "")
                    .replace("page.tsx", "")
                    .replace("page.jsx", "")
                )
                route_path = "/" + path.rstrip("/") if path else "/"
                changed_paths.add(route_path)
                print(f"Found Next.js App Router file: {file_path}")
                print(f"Affected path: {route_path}")

        # Next.js Pages Router
        elif "pages/" in file_path and (
            file_path.endswith(".tsx") or file_path.endswith(".jsx")
        ):
            path = (
                file_path.split("pages/")[-1]
                .replace("index.tsx", "")
                .replace("index.jsx", "")
                .replace(".tsx", "")
                .replace(".jsx", "")
            )
            changed_paths.add("/" + path.rstrip("/"))
            print(f"Found Next.js Pages Router file: {file_path}")
            print(f"Affected path: {path}")

        # React components that might affect multiple pages
        # elif file_path.endswith((".tsx", ".jsx")) and (
        #     "components/" in file_path or "layouts/" in file_path
        # ):

    return list(changed_paths)


@handle_exceptions(raise_on_error=True)
async def handle_screenshot_comparison(payload: dict) -> None:
    # Return if this feature is not enabled
    return

    # Return if the author of the pull request is not GitAuto itself
    print("\n\n\n\nStarting screenshot comparison")
    pull: dict = payload["pull_request"]
    if pull["user"]["login"] != GITHUB_APP_USER_NAME:
        return

    # Get the basic information
    repo_obj: dict = payload["repository"]
    owner: str = repo_obj["owner"]["login"]
    repo: str = repo_obj["name"]
    pr_number: int = pull["number"]
    pr_url: str = pull["url"]
    branch_name: str = pull["head"]["ref"]
    installation_id: int = payload["installation"]["id"]

    # Get the access token
    access_token: str = get_installation_access_token(installation_id)

    # Get the file changes
    file_changes: list[dict[str, str]] = get_pull_request_file_changes(
        owner=owner, repo=repo, pr_number=pr_number, access_token=access_token
    )

    # Get the target paths
    target_paths: list[str] = get_target_paths(file_changes)
    if not target_paths:
        print("No target paths found")
        return

    print(f"Target paths: {target_paths}")

    # Delete existing screenshot comparison comments
    all_comments: list[dict] = get_all_comments(
        owner=owner, repo=repo, pr_number=pr_number, access_token=access_token
    )
    for comment in all_comments:
        if "Screenshot Comparison" in comment.get("body", ""):
            delete_comment(
                owner=owner,
                repo=repo,
                comment_id=comment["id"],
                access_token=access_token,
            )

    # Create a temporary directory for the repository
    temp_dir = tempfile.mkdtemp()
    server_process = None

    try:
        # Clone the repository
        clone_repo(
            owner=owner,
            repo=repo,
            access_token=access_token,
            target_dir=temp_dir,
        )

        # Check if package.json exists
        package_json_path = os.path.join(temp_dir, "package.json")
        if not os.path.exists(package_json_path):
            print("package.json not found, skipping screenshot comparison")
            return

        # Start the local server
        server_process = start_local_server(temp_dir)
        if server_process is None:
            print("Failed to start local server")
            return

        print(f"Started local server with PID: {server_process.pid}")
        sleep(10)  # Wait for the server to start

        # Capture screenshots for the main branch
        main_branch = get_current_branch(temp_dir)
        print(f"Current branch: {main_branch}")

        main_screenshots_dir = os.path.join(temp_dir, "screenshots_main")
        os.makedirs(main_screenshots_dir, exist_ok=True)

        main_urls = [f"http://localhost:3000{path}" for path in target_paths]
        await capture_screenshots(main_urls, main_screenshots_dir)

        # Switch to the PR branch
        fetch_branch(temp_dir, branch_name)
        switch_to_branch(temp_dir, branch_name)

        # Restart the server for the new branch
        server_process.terminate()
        server_process.wait()
        sleep(5)

        server_process = start_local_server(temp_dir)
        if server_process is None:
            print("Failed to restart local server")
            return

        print(f"Restarted local server with PID: {server_process.pid}")
        sleep(10)  # Wait for the server to start

        # Capture screenshots for the PR branch
        pr_screenshots_dir = os.path.join(temp_dir, "screenshots_pr")
        os.makedirs(pr_screenshots_dir, exist_ok=True)

        pr_urls = [f"http://localhost:3000{path}" for path in target_paths]
        await capture_screenshots(pr_urls, pr_screenshots_dir)

        # Upload screenshots to S3 and create comparison comment
        comment_body = "## Screenshot Comparison\n\n"
        comment_body += "| Path | Main Branch | PR Branch |\n"
        comment_body += "|------|-------------|----------|\n"

        for path in target_paths:
            filename = get_url_filename(f"http://localhost:3000{path}")

            # Upload main branch screenshot
            main_file_path = os.path.join(main_screenshots_dir, filename)
            if os.path.exists(main_file_path):
                main_s3_key = f"screenshots/{owner}/{repo}/{pr_number}/main/{filename}"
                main_url = upload_to_s3(main_file_path, main_s3_key)
            else:
                main_url = "N/A"

            # Upload PR branch screenshot
            pr_file_path = os.path.join(pr_screenshots_dir, filename)
            if os.path.exists(pr_file_path):
                pr_s3_key = f"screenshots/{owner}/{repo}/{pr_number}/pr/{filename}"
                pr_url = upload_to_s3(pr_file_path, pr_s3_key)
            else:
                pr_url = "N/A"

            # Add row to the table
            main_img = f"![Main]({main_url})" if main_url != "N/A" else "N/A"
            pr_img = f"![PR]({pr_url})" if pr_url != "N/A" else "N/A"
            comment_body += f"| `{path}` | {main_img} | {pr_img} |\n"

        # Create the comment
        create_comment(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            body=comment_body,
            access_token=access_token,
        )

    finally:
        # Clean up
        if server_process:
            server_process.terminate()
            server_process.wait()
            print(f"Terminated server process with PID: {server_process.pid}")

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")