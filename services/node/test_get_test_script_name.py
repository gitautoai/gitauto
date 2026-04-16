import json
import os
import tempfile

from config import UTF8
from services.node.get_test_script_name import get_test_script_name

# Real scripts sections from customer/local repos, used as test fixtures.
# gitautoai/website: "test" uses jest, but both jest AND vitest binaries exist (the bug scenario)
WEBSITE_SCRIPTS = {
    "dev": "npm run kill-port && npm run types:generate && (npm run stripe &) && next dev -p 4000",
    "dev:ci": "next dev -p 4000 & npm run stripe",
    "kill-port": "lsof -ti:4000 | xargs kill -9 2>/dev/null || true",
    "stripe": "stripe listen --events payment_intent.succeeded --forward-to localhost:4000/api/stripe/webhook",
    "build": "next build",
    "start": "next start",
    "lint": "eslint .",
    "types:generate": "supabase gen types typescript --project-id dkrxtcbaqzrodvsagwwn > types/supabase.ts && prettier --write types/supabase.ts",
    "test": "jest",
    "test:integration": "jest --config jest.integration.config.ts",
    "test:watch": "jest --watch",
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build",
}

# ghostwriter: vitest-based project
GHOSTWRITER_SCRIPTS = {
    "lint": "tsc --noEmit",
    "build": "tsc",
    "generate-drafts": "tsx src/lambda/generateDrafts.ts",
    "dev": "tsx watch src/lambda/generateDrafts.ts",
    "test": "vitest run",
    "test:watch": "vitest",
}

# posthog: has both "test" and "test:unit", prefers "test:unit"
POSTHOG_SCRIPTS = {
    "copy-scripts": "mkdir -p frontend/dist/ && ./bin/copy-posthog-js",
    "test": "pnpm test:unit && pnpm test:visual",
    "test:unit": "jest --testPathPattern=frontend/",
    "jest": "jest",
    "test:visual": "rm -rf frontend/__snapshots__/__failures__/ && docker compose -f docker-compose.playwright.yml run --rm -it --build playwright pnpm test:visual:update --url http://host.docker.internal:6006",
    "start": 'concurrently -n ESBUILD,TYPEGEN -c yellow,green "pnpm start-http" "pnpm run typegen:watch"',
    "build": "pnpm copy-scripts && pnpm build:esbuild",
}

# circle-ci-test: jest with NODE_OPTIONS for ESM support
CIRCLE_CI_TEST_SCRIPTS = {
    "test": "NODE_OPTIONS='--experimental-vm-modules' jest",
    "test:watch": "NODE_OPTIONS='--experimental-vm-modules' jest --watch",
    "test:coverage": "NODE_OPTIONS='--experimental-vm-modules' jest --coverage",
    "test:ci": "NODE_OPTIONS='--experimental-vm-modules' jest --ci --coverage --maxWorkers=2",
    "test:report": "NODE_OPTIONS='--experimental-vm-modules' jest --reporters=jest-html-reporters --reporters=jest-junit",
}


def test_get_test_script_name_website_jest():
    # gitautoai/website: "test": "jest" — the repo where the --related vs --findRelatedTests bug was found
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump({"scripts": WEBSITE_SCRIPTS}, f)
        result = get_test_script_name(tmpdir)
        assert result == ("test", "jest")


def test_get_test_script_name_ghostwriter_vitest():
    # ghostwriter: "test": "vitest run"
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump({"scripts": GHOSTWRITER_SCRIPTS}, f)
        result = get_test_script_name(tmpdir)
        assert result == ("test", "vitest run")


def test_get_test_script_name_posthog_prefers_test_unit():
    # posthog: has both "test" and "test:unit", should prefer "test:unit"
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump({"scripts": POSTHOG_SCRIPTS}, f)
        result = get_test_script_name(tmpdir)
        assert result == ("test:unit", "jest --testPathPattern=frontend/")


def test_get_test_script_name_circle_ci_test_jest_with_node_options():
    # circle-ci-test: jest invoked with NODE_OPTIONS for ESM
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump({"scripts": CIRCLE_CI_TEST_SCRIPTS}, f)
        result = get_test_script_name(tmpdir)
        assert result == ("test", "NODE_OPTIONS='--experimental-vm-modules' jest")


def test_get_test_script_name_returns_none_when_no_package_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = get_test_script_name(tmpdir)
        assert result == (None, "")


def test_get_test_script_name_returns_none_when_no_scripts():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {"name": "test"}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result == (None, "")


def test_get_test_script_name_returns_none_when_no_test_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {"scripts": {"build": "tsc"}}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result == (None, "")


def test_get_test_script_name_returns_none_for_empty_test_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {"scripts": {"test": ""}}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result == (None, "")


def test_get_test_script_name_returns_none_for_invalid_package_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        # package.json is a list instead of dict
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(["invalid"], f)
        result = get_test_script_name(tmpdir)
        assert result == (None, "")


def test_get_test_script_name_returns_none_for_invalid_scripts():
    with tempfile.TemporaryDirectory() as tmpdir:
        # scripts is a list instead of dict
        package_json = {"scripts": ["invalid"]}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result == (None, "")


def test_get_test_script_name_returns_none_for_non_string_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        # test script is a number instead of string
        package_json = {"scripts": {"test": 123}}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result == (None, "")


def test_get_test_script_name_ignores_empty_test_unit():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {"scripts": {"test": "jest", "test:unit": ""}}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result == ("test", "jest")
