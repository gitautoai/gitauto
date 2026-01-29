# Third-party libraries
import requests

# Internal libraries
from config import TIMEOUT
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_project_pipelines(
    project_slug: str,
    circle_token: str,
    branch: str | None = None,
    per_page: int = 20,
    max_pages: int = 1,
):
    # https://circleci.com/docs/api/v2/index.html#tag/Pipeline/operation/listPipelinesForProject
    base_url = "https://circleci.com/api/v2"
    headers = {"Circle-Token": circle_token}
    all_pipelines: list[dict] = []
    page_token = None

    for _ in range(max_pages):
        url = f"{base_url}/project/{project_slug}/pipeline"
        params = []
        if branch:
            params.append(f"branch={branch}")
        if page_token:
            params.append(f"page-token={page_token}")
        if params:
            url += "?" + "&".join(params)

        response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
        if response.status_code == 404:
            return []
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])
        all_pipelines.extend(items)

        page_token = data.get("next_page_token")
        if not page_token or len(items) < per_page:
            break

    return all_pipelines
