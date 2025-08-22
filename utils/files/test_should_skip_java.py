from utils.files.should_skip_java import should_skip_java


def test_export_only():
    # File with only package and import statements
    content = """package com.example;

import java.util.List;
import java.util.Map;
import com.example.types.User;"""
    assert should_skip_java(content) is True


def test_constants_only():
    # Constants only
    content = """package com.example;

public static final int MAX_SIZE = 100;
private static final String API_URL = "https://api.example.com";
public static final boolean DEBUG = true;
protected static final List<String> ALLOWED_TYPES = Arrays.asList("user", "admin");"""
    assert should_skip_java(content) is True


def test_interface_definitions_only():
    # Interface definitions only
    content = """package com.example;

public interface UserService {
    User findById(Long id);
    void save(User user);
    List<User> findAll();
}

interface Repository<T> {
    T find(Long id);
    void save(T entity);
}"""
    assert should_skip_java(content) is True


def test_annotation_definitions_only():
    # Annotation definitions only
    content = """package com.example;

@interface CustomAnnotation {
    String value();
    int priority() default 0;
    boolean enabled() default true;
}

public @interface Validated {
    String message() default "Invalid input";
}"""
    assert should_skip_java(content) is True


def test_record_definitions_only():
    # Java record definitions only (Java 14+)
    content = """package com.example;

public record User(Long id, String name, String email) {}

record Config(int timeout, int retries) {}

public record Address(
    String street,
    String city,
    String zipCode
) {}"""
    assert should_skip_java(content) is True


def test_mixed_imports_and_constants():
    # Mixed imports and constants
    content = """package com.example;

import java.util.Map;
import java.util.HashMap;

public static final int DEFAULT_TIMEOUT = 30;
private static final Map<String, String> CONFIG = new HashMap<>();

public static final String VERSION = "1.0.0";"""
    assert should_skip_java(content) is True


def test_method_with_logic():
    # Method definitions - should NOT be skipped
    content = """package com.example;

public class Calculator {
    public double calculateTotal(List<Item> items) {
        return items.stream()
                   .mapToDouble(Item::getPrice)
                   .sum();
    }

    public List<Integer> processData(List<Integer> data) {
        return data.stream()
                  .map(x -> x * 2)
                  .collect(Collectors.toList());
    }
}"""
    assert should_skip_java(content) is False


def test_class_with_methods():
    # Class with methods - should NOT be skipped
    content = """package com.example;

public class UserService {
    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }

    public User findById(Long id) {
        return repository.findById(id)
                        .orElseThrow(() -> new UserNotFoundException(id));
    }

    public void save(User user) {
        repository.save(user);
    }
}"""
    assert should_skip_java(content) is False


def test_mixed_interface_and_implementation():
    # Mixed interface and implementation - should NOT be skipped
    content = """package com.example;

interface Service {
    void process();
}

class ServiceImpl implements Service {
    @Override
    public void process() {
        System.out.println("Processing");
    }
}"""
    assert should_skip_java(content) is False


def test_static_methods():
    # Static methods - should NOT be skipped
    content = """package com.example;

public class Utils {
    public static int add(int a, int b) {
        return a + b;
    }

    public static String formatName(String first, String last) {
        return first + " " + last;
    }
}"""
    assert should_skip_java(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """package com.example;

public class Config {
    public static final int MAX_SIZE = 1024;
    private static final String DEFAULT_NAME = "Unknown";

    public static int getMaxSize() {
        return MAX_SIZE;
    }

    public static String getDefaultName() {
        return DEFAULT_NAME;
    }
}"""
    assert should_skip_java(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_java("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_java(content) is True
