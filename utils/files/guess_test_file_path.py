from pathlib import Path

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def guess_test_file_path(impl_file: str, test_dir_prefixes: list[str]):
    path = Path(impl_file)  # services/github/client.py
    stem = path.stem  # client
    suffix = path.suffix  # .py
    parent = path.parent  # services/github
    prefixes = [Path(p.strip("/")) for p in test_dir_prefixes]

    if suffix == ".py":
        names = [f"test_{stem}{suffix}", f"{stem}_test{suffix}"]
        candidates = [p / parent / n for p in prefixes for n in names] + [
            parent / f"test_{stem}{suffix}",  # services/github/test_client.py
            parent / f"{stem}_test{suffix}",  # services/github/client_test.py
            # tests/services/github/test_client.py
            Path("tests") / parent / f"test_{stem}{suffix}",
            # tests/services/github/client_test.py
            Path("tests") / parent / f"{stem}_test{suffix}",
        ]
        return list(dict.fromkeys(str(c) for c in candidates))

    if suffix in (".ts", ".tsx", ".js", ".jsx"):
        parent_without_src = Path(str(parent).removeprefix("src/"))  # components
        names = [f"{stem}.test{suffix}", f"{stem}.spec{suffix}"]
        candidates = [p / parent / n for p in prefixes for n in names] + [
            parent / f"{stem}.test{suffix}",  # src/components/Button.test.tsx
            parent / f"{stem}.spec{suffix}",  # src/components/Button.spec.tsx
            # __tests__/src/components/Button.test.tsx
            Path("__tests__") / parent / f"{stem}.test{suffix}",
            # __tests__/src/components/Button.spec.tsx
            Path("__tests__") / parent / f"{stem}.spec{suffix}",
            # src/components/__tests__/Button.test.tsx
            parent / "__tests__" / f"{stem}.test{suffix}",
            # src/components/__tests__/Button.spec.tsx
            parent / "__tests__" / f"{stem}.spec{suffix}",
            # tests/src/components/Button.test.tsx
            Path("tests") / parent / f"{stem}.test{suffix}",
            # tests/src/components/Button.spec.tsx
            Path("tests") / parent / f"{stem}.spec{suffix}",
            # tests/components/Button.test.tsx
            Path("tests") / parent_without_src / f"{stem}.test{suffix}",
            # tests/components/Button.spec.tsx
            Path("tests") / parent_without_src / f"{stem}.spec{suffix}",
        ]
        return list(dict.fromkeys(str(c) for c in candidates))

    if suffix in (".java", ".kt"):
        names = [f"{stem}Test{suffix}"]
        candidates = [p / parent / n for p in prefixes for n in names] + [
            parent / f"{stem}Test{suffix}",  # com/example/ServiceTest.java
        ]
        if "src/main/java" in str(parent):
            test_parent = Path(str(parent).replace("src/main/java", "src/test/java"))
            # src/test/java/com/example/ServiceTest.java
            candidates.append(test_parent / f"{stem}Test{suffix}")
        return list(dict.fromkeys(str(c) for c in candidates))

    if suffix == ".go":
        names = [f"{stem}_test{suffix}"]
        candidates = [p / parent / n for p in prefixes for n in names] + [
            parent / f"{stem}_test{suffix}",  # pkg/handler/handler_test.go
        ]
        return list(dict.fromkeys(str(c) for c in candidates))

    if suffix == ".rb":
        names = [f"{stem}_spec{suffix}", f"{stem}_test{suffix}"]
        candidates = [p / parent / n for p in prefixes for n in names] + [
            parent / f"{stem}_spec{suffix}",  # lib/models/user_spec.rb
            parent / f"{stem}_test{suffix}",  # lib/models/user_test.rb
            # spec/lib/models/user_spec.rb
            Path("spec") / parent / f"{stem}_spec{suffix}",
            # test/lib/models/user_test.rb
            Path("test") / parent / f"{stem}_test{suffix}",
        ]
        return list(dict.fromkeys(str(c) for c in candidates))

    if suffix == ".php":
        names = [f"{stem}Test{suffix}"]
        candidates = [p / parent / n for p in prefixes for n in names] + [
            parent / f"{stem}Test{suffix}",  # app/Services/UserServiceTest.php
            # tests/app/Services/UserServiceTest.php
            Path("tests") / parent / f"{stem}Test{suffix}",
        ]
        return list(dict.fromkeys(str(c) for c in candidates))

    if suffix == ".rs":
        return [str(impl_file)]  # Rust tests are in same file

    if suffix == ".cs":
        names = [f"{stem}Tests{suffix}", f"{stem}Test{suffix}"]
        candidates = [p / parent / n for p in prefixes for n in names] + [
            parent / f"{stem}Tests{suffix}",  # Services/UserServiceTests.cs
            parent / f"{stem}Test{suffix}",  # Services/UserServiceTest.cs
        ]
        return list(dict.fromkeys(str(c) for c in candidates))

    raise ValueError(f"Unsupported file extension: {suffix} for {impl_file}")
