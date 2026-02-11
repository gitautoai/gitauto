from utils.files.is_dependency_file import is_dependency_file


def test_vendor_directory():
    assert is_dependency_file("php/lib/vendor/phpoffice/phpspreadsheet/src/File.php")


def test_node_modules_directory():
    assert is_dependency_file("node_modules/lodash/index.js")


def test_nested_node_modules():
    assert is_dependency_file("packages/app/node_modules/react/index.js")


def test_venv_directory():
    assert is_dependency_file("venv/lib/python3.13/site-packages/requests/api.py")


def test_bower_components():
    assert is_dependency_file("bower_components/jquery/dist/jquery.js")


def test_regular_source_file():
    assert not is_dependency_file("src/components/App.tsx")


def test_regular_php_file():
    assert not is_dependency_file("php/lib/MyClass.php")


def test_file_with_vendor_in_name():
    assert not is_dependency_file("src/vendor_config.py")


def test_root_level_file():
    assert not is_dependency_file("main.py")
