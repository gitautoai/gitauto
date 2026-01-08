from utils.files.is_code_file import is_code_file


def test_is_code_file_web_technologies():
    assert is_code_file("app.js") is True
    assert is_code_file("component.jsx") is True
    assert is_code_file("main.ts") is True
    assert is_code_file("component.tsx") is True
    assert is_code_file("app.vue") is True
    assert is_code_file("component.svelte") is True


def test_is_code_file_backend_languages():
    assert is_code_file("main.py") is True
    assert is_code_file("App.java") is True
    assert is_code_file("Main.kt") is True
    assert is_code_file("service.scala") is True
    assert is_code_file("build.groovy") is True
    assert is_code_file("Program.cs") is True
    assert is_code_file("Module.vb") is True
    assert is_code_file("script.fs") is True
    assert is_code_file("index.php") is True
    assert is_code_file("app.rb") is True
    assert is_code_file("main.go") is True
    assert is_code_file("lib.rs") is True
    assert is_code_file("ViewController.swift") is True


def test_is_code_file_c_family():
    assert is_code_file("main.c") is True
    assert is_code_file("app.cpp") is True
    assert is_code_file("lib.cc") is True
    assert is_code_file("module.cxx") is True
    assert is_code_file("header.h") is True
    assert is_code_file("header.hpp") is True


def test_is_code_file_mobile_development():
    assert is_code_file("app.dart") is True
    assert is_code_file("ViewController.m") is True
    assert is_code_file("ViewController.mm") is True
    assert is_code_file("script.kts") is True


def test_is_code_file_functional_languages():
    assert is_code_file("main.hs") is True
    assert is_code_file("app.elm") is True
    assert is_code_file("core.clj") is True
    assert is_code_file("frontend.cljs") is True
    assert is_code_file("module.ml") is True
    assert is_code_file("server.ex") is True
    assert is_code_file("script.exs") is True
    assert is_code_file("gen_server.erl") is True
    assert is_code_file("header.hrl") is True


def test_is_code_file_other_languages():
    assert is_code_file("analysis.r") is True
    assert is_code_file("compute.jl") is True
    assert is_code_file("script.lua") is True
    assert is_code_file("parser.pl") is True
    assert is_code_file("Module.pm") is True
    assert is_code_file("query.sql") is True
    assert is_code_file("schema.graphql") is True
    assert is_code_file("service.proto") is True
    assert is_code_file("config.vim") is True
    assert is_code_file("boot.asm") is True
    assert is_code_file("init.s") is True


def test_is_code_file_legacy_languages():
    assert is_code_file("program.pas") is True
    assert is_code_file("unit.pp") is True
    assert is_code_file("compute.f") is True
    assert is_code_file("module.f90") is True
    assert is_code_file("lib.f95") is True
    assert is_code_file("payroll.cobol") is True
    assert is_code_file("batch.cob") is True
    assert is_code_file("report.cbl") is True
    assert is_code_file("package.ada") is True
    assert is_code_file("body.adb") is True
    assert is_code_file("spec.ads") is True
    assert is_code_file("script.tcl") is True
    assert is_code_file("design.vhdl") is True
    assert is_code_file("entity.vhd") is True
    assert is_code_file("module.v") is True
    assert is_code_file("testbench.sv") is True


def test_is_code_file_case_insensitive():
    assert is_code_file("APP.PY") is True
    assert is_code_file("Main.JS") is True
    assert is_code_file("Component.TSX") is True
    assert is_code_file("Service.JAVA") is True
    assert is_code_file("module.CPP") is True


def test_is_code_file_non_code_extensions():
    assert is_code_file("README.md") is False
    assert is_code_file("notes.txt") is False
    assert is_code_file("config.json") is False
    assert is_code_file("data.xml") is False
    assert is_code_file("settings.yml") is False
    assert is_code_file("docker.yaml") is False
    assert is_code_file("data.csv") is False
    assert is_code_file("index.html") is False
    assert is_code_file("style.css") is False
    assert is_code_file("icon.svg") is False
    assert is_code_file("image.png") is False
    assert is_code_file("photo.jpg") is False
    assert is_code_file("picture.jpeg") is False
    assert is_code_file("animation.gif") is False
    assert is_code_file("favicon.ico") is False
    assert is_code_file("document.pdf") is False
    assert is_code_file("package.lock") is False
    assert is_code_file("environment.env") is False


def test_is_code_file_files_without_extension():
    assert is_code_file("README") is False
    assert is_code_file("Makefile") is False
    assert is_code_file("Dockerfile") is False
    assert is_code_file("LICENSE") is False


def test_is_code_file_multiple_dots():
    assert is_code_file("config.test.js") is True
    assert is_code_file("component.spec.ts") is True
    assert is_code_file("data.backup.py") is True
    assert is_code_file("file.min.js") is True
    assert is_code_file("archive.tar.gz") is False
    assert is_code_file("backup.sql.bak") is False


def test_is_code_file_edge_cases():
    assert is_code_file("") is False
    assert is_code_file(".") is False
    assert is_code_file("..") is False
    assert is_code_file(".py") is True
    assert is_code_file(".js") is True
    assert is_code_file("file.") is False


def test_is_code_file_with_paths():
    assert is_code_file("src/main.py") is True
    assert is_code_file("utils/helper.js") is True
    assert is_code_file("lib/module.rb") is True
    assert is_code_file("package/file.go") is True
    assert is_code_file("very/long/path/to/deeply/nested/file.cpp") is True
    assert is_code_file("src/components/Button.tsx") is True


def test_is_code_file_real_world_examples():
    assert is_code_file("services/webhook/merge_handler.py") is True
    assert is_code_file("utils/files/is_code_file.py") is True
    assert is_code_file("config/database.yml") is False
    assert is_code_file("README.md") is False
    assert is_code_file("package-lock.json") is False
