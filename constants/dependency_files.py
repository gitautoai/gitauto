CONFIGURATION_FILES_JS = [
    "angular.json",
    "babel.config.js",
    "next.config.js",
    "nuxt.config.js",
    "package.json",
    "remix.config.js",
    "rollup.config.js",
    "svelte.config.js",
    "tsconfig.json",
    "vite.config.js",
    "vue.config.js",
    "webpack.config.js",
]

CONFIGURATION_FILES_PYTHON = [
    "requirements.txt",  # Standard, a dependency manager
    "Pipfile",  # by pipenv, a dependency manager
    "pyproject.toml",  # by poetry, a dependency manager
    "conda.yaml",  # by conda, a dependency manager
    "environment.yml",  # by conda, a dependency manager
    "django.settings.py",  # by django, a framework
    "setup.py",  # Traditional
]

CONFIGURATION_FILES_RUBY = [
    "Gemfile",  # Bundler, a dependency manager
    "application.rb",  # Rails, a framework
]

CONFIGURATION_FILES_PHP = [
    "composer.json",  # Composer, a dependency manager
    "artisan",  # Laravel, a framework
    "wp-config.php",  # WordPress, a CMS
]

CONFIGURATION_FILES_JAVA = [
    "pom.xml",  # Maven
    "build.gradle",  # Gradle build file
    "build.gradle.kts",  # Gradle Kotlin build file
    "settings.gradle",  # Gradle settings file
    "settings.gradle.kts",  # Gradle Kotlin settings file
    "gradle.properties",  # Gradle properties file
    "ivy.xml",  # Apache Ivy configuration
    "build.xml",  # Apache Ant build file
    "AndroidManifest.xml",  # Android manifest file
]

CONFIGURATION_FILES_C = [
    "CMakeLists.txt",  # CMake, a build system
    "Makefile",  # Makefile, a build system
    "configure.ac",  # Autotools, a build system
    "*.vcxproj",  # Visual Studio, a build system
    "*.pro",  # Qt, a build system
    "conanfile.txt",  # Conan, a build system
    "meson.build",  # Meson, a build system
]

CONFIGURATION_FILES_DOTNET = [
    "packages.config",  # NuGet, a dependency manager
    "*.csproj",  # C# project file
    "*.fsproj",  # F# project file
    "*.vbproj",  # VB.NET project file
    "paket.dependencies",  # Paket, a dependency manager
    "nuget.config",  # NuGet, a dependency manager
    "appsettings.json",  # ASP.NET Core, a framework
    "web.config",  # ASP.NET Core, a framework
]

CONFIGURATION_FILES_GO = [
    "go.mod",  # Go, a dependency manager
    "go.sum",  # Go, a dependency manager
]

CONFIGURATION_FILES_RUST = [
    "Cargo.toml",  # Cargo, a dependency manager
]

CONFIGURATION_FILES_SWIFT = [
    "Package.swift",  # Swift, a dependency manager
    "Podfile",  # CocoaPods, a dependency manager
    "Cartfile",  # Carthage, a dependency manager
]

CONFIGURATION_FILES_ELIXIR = [
    "mix.exs",  # Mix, a dependency manager
]

CONFIGURATION_FILES_HASKELL = [
    "package.yaml",  # Haskell, a dependency manager
    "*.cabal",  # Haskell, a dependency manager
]

CONFIGURATION_FILES_SHELL = [
    ".bashrc",
    ".zshrc",
]

CONFIGURATION_FILES_AWS = [
    "*.tf",  # Terraform, a configuration management tool
    "terraform.tfstate",  # Terraform, a configuration management tool
]

CONFIGURATION_FILES_DOCKER = [
    "Dockerfile",  # Dockerfile, a containerization tool
    "docker-compose.yml",  # Docker Compose, a containerization tool
    "docker-compose.yaml",  # Docker Compose, a containerization tool
]

CONFIGURATION_FILES = [
    *CONFIGURATION_FILES_JS,
    *CONFIGURATION_FILES_PYTHON,
    *CONFIGURATION_FILES_RUBY,
    *CONFIGURATION_FILES_PHP,
    *CONFIGURATION_FILES_JAVA,
    *CONFIGURATION_FILES_C,
    *CONFIGURATION_FILES_DOTNET,
    *CONFIGURATION_FILES_GO,
    *CONFIGURATION_FILES_SWIFT,
    *CONFIGURATION_FILES_RUST,
    *CONFIGURATION_FILES_ELIXIR,
    *CONFIGURATION_FILES_HASKELL,
    *CONFIGURATION_FILES_AWS,
    *CONFIGURATION_FILES_DOCKER,
    "pubspec.yaml",  # Dart/Flutter, a dependency manager
    "DESCRIPTION",  # R, a dependency manager
    "build.sbt",  # Scala, a build system
    "project.clj",  # Clojure, a build system
    "rebar.config",  # Erlang, a build system
    "dune-project",  # OCaml, a build system
    "*.opam",  # OCaml, a build system
    "*.nimble",  # Nim, a build system
]
