import pytest
from utils.files.is_config_file import is_config_file


@pytest.mark.parametrize(
    "filename, expected",
    [
        # JavaScript/TypeScript config files - should return True
        ("jest.config.ts", True),
        ("jest.config.js", True),
        ("vite.config.js", True),
        ("vite.config.ts", True),
        ("webpack.config.js", True),
        ("rollup.config.js", True),
        ("babel.config.js", True),
        ("eslint.config.js", True),
        ("prettier.config.js", True),
        ("tailwind.config.js", True),
        ("postcss.config.js", True),
        ("next.config.js", True),
        ("nuxt.config.js", True),
        ("karma.conf.js", True),
        ("tsconfig.json", True),
        ("tsconfig.build.json", True),
        (".eslintrc", True),
        (".eslintrc.js", True),
        (".eslintrc.json", True),
        (".prettierrc", True),
        (".prettierrc.js", True),
        # Python config files - should return True
        ("conftest.py", True),
        ("test/conftest.py", True),
        ("setup.py", True),
        ("src/setup.py", True),
        # Test files - should return False
        ("Component.test.tsx", False),
        ("utils.spec.js", False),
        ("test_file.py", False),
        ("__tests__/Component.tsx", False),
        # Regular files - should return False
        ("Component.tsx", False),
        ("utils.js", False),
        ("main.py", False),
    ],
)
def test_is_config_file(filename, expected):
    assert is_config_file(filename) == expected
