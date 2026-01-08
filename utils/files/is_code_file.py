from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_code_file(filename: str) -> bool:

    # Extract file extension
    if "." not in filename:
        return False

    extension = filename.split(".")[-1].lower()

    # Code file extensions (whitelist approach)
    code_extensions = {
        # Web technologies (logic-containing)
        "js",
        "jsx",
        "ts",
        "tsx",
        "vue",
        "svelte",
        # Backend languages
        "py",
        "java",
        "kt",  # Kotlin
        "scala",
        "groovy",
        "cs",  # C#
        "vb",  # Visual Basic
        "fs",  # F#
        "php",
        "rb",
        "go",
        "rs",  # Rust
        "swift",
        "c",  # C
        "cpp",
        "cc",  # C++
        "cxx",  # C++
        "h",  # C header
        "hpp",  # C++ header
        # Mobile development
        "dart",
        "m",  # Objective-C
        "mm",  # Objective-C++
        "kts",  # Kotlin script
        # Functional languages
        "hs",  # Haskell
        "elm",  # Elm
        "clj",  # Clojure
        "cljs",  # ClojureScript
        "ml",  # OCaml
        "ex",  # Elixir
        "exs",  # Elixir script
        "erl",  # Erlang
        "hrl",  # Erlang header
        # Other languages
        "r",  # R
        "jl",  # Julia
        "lua",  # Lua
        "pl",  # Perl
        "pm",  # Perl module
        "sql",  # SQL
        "graphql",  # GraphQL
        "proto",  # Protocol Buffers
        "vim",  # Vim script
        "asm",  # Assembly
        "s",  # Assembly
        "pas",  # Pascal
        "pp",  # Pascal
        "f",  # Fortran
        "f90",  # Fortran 90
        "f95",  # Fortran 95
        "cobol",  # COBOL
        "cob",  # COBOL
        "cbl",  # COBOL
        "ada",  # Ada
        "adb",  # Ada
        "ads",  # Ada
        "tcl",  # Tcl
        "vhdl",  # VHDL
        "vhd",  # VHDL
        "v",  # Verilog
        "sv",  # SystemVerilog
    }

    return extension in code_extensions
