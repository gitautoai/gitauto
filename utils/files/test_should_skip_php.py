from utils.files.should_skip_php import should_skip_php


def test_includes_only():
    # File with only includes and requires
    content = """<?php

require_once 'config.php';
require_once __DIR__ . '/vendor/autoload.php';
include 'helpers.php';
include_once 'constants.php';

use App\\Models\\User;
use App\\Services\\ApiClient;"""
    assert should_skip_php(content) is True


def test_constants_only():
    # Constants only
    content = """<?php

const MAX_RETRIES = 3;
const API_URL = 'https://api.example.com';
const DEFAULT_CONFIG = ['debug' => true];

define('VERSION', '1.0.0');
define('STATUS_ACTIVE', 1);

$CONFIG_ARRAY = [
    'database' => 'mysql',
    'host' => 'localhost'
];"""
    assert should_skip_php(content) is True


def test_interface_definition():
    # Interface definition should be skipped
    content = """<?php

interface UserRepositoryInterface {
    public function findById(int $id): ?User;
    public function save(User $user): void;
    public function delete(int $id): bool;
}

interface CacheInterface {
    public function get(string $key);
    public function set(string $key, $value, int $ttl = 3600);
}"""
    assert should_skip_php(content) is True


def test_trait_definition():
    # Trait definition should be skipped
    content = """<?php

trait Timestampable {
    public $created_at;
    public $updated_at;
}

trait Cacheable {
    protected $cache_key;
    protected $cache_ttl = 3600;
}"""
    assert should_skip_php(content) is True


def test_simple_data_class():
    # Simple data class with only properties
    content = """<?php

class UserData {
    public string $name;
    public string $email;
    public int $age;
    protected bool $active;
}

class ConfigData {
    public $database_host;
    public $database_name;
}"""
    assert should_skip_php(content) is True


def test_with_function_definition():
    # File with function should not be skipped
    content = """<?php

require_once 'config.php';

const MAX_RETRIES = 3;

function calculateTax(float $amount): float {
    return $amount * 0.1;
}"""
    assert should_skip_php(content) is False


def test_class_with_methods():
    # Class with methods should not be skipped
    content = """<?php

class Calculator {
    public function add(int $a, int $b): int {
        return $a + $b;
    }

    public function multiply(int $x, int $y): int {
        return $x * $y;
    }
}"""
    assert should_skip_php(content) is False


def test_config_file_with_return():
    # Config file that returns array should be skipped
    content = """<?php

return [
    'database' => [
        'host' => 'localhost',
        'name' => 'myapp'
    ],
    'cache' => [
        'driver' => 'redis'
    ]
];"""
    assert should_skip_php(content) is True
