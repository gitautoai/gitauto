from utils.files.should_skip_csharp import should_skip_csharp


def test_using_statements_only():
    # File with only using statements
    content = """using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.DependencyInjection;

namespace MyApp.Models;"""
    assert should_skip_csharp(content) is True


def test_constants_only():
    # Constants only
    content = """using System;

namespace MyApp {
    public const int MAX_RETRIES = 3;
    public const string API_URL = "https://api.example.com";
    public static readonly Dictionary<string, int> STATUS_CODES = new() {
        ["OK"] = 200,
        ["NOT_FOUND"] = 404
    };

    internal const bool DEBUG_MODE = true;
}"""
    assert should_skip_csharp(content) is True


def test_interface_definition():
    # Interface definition should be skipped
    content = """using System;
using System.Threading.Tasks;

namespace MyApp.Services {
    public interface IUserService {
        Task<User> GetByIdAsync(int id);
        Task SaveAsync(User user);
        void Delete(int id);
    }

    internal interface ICacheService {
        T Get<T>(string key);
        void Set<T>(string key, T value);
    }
}"""
    assert should_skip_csharp(content) is True


def test_record_definition():
    # Record definition (C# 9.0+) should be skipped
    content = """namespace MyApp.Models;

public record UserDto(int Id, string Name, string Email);
public record ProductDto(string Name, decimal Price, bool IsActive);

public record ConfigData {
    public string DatabaseUrl { get; init; }
    public int MaxConnections { get; init; }
}"""
    assert should_skip_csharp(content) is True


def test_struct_definition():
    # Struct definition should be skipped
    content = """using System;

namespace MyApp.ValueTypes {
    public struct Point {
        public int X;
        public int Y;
    }

    public readonly struct Vector {
        public readonly double X;
        public readonly double Y;
    }
}"""
    assert should_skip_csharp(content) is True


def test_enum_definition():
    # Enum definition should be skipped
    content = """namespace MyApp.Enums {
    public enum OrderStatus {
        Pending = 0,
        Processing = 1,
        Shipped = 2,
        Delivered = 3,
        Cancelled = 4
    }

    internal enum LogLevel {
        Debug,
        Info,
        Warning,
        Error
    }
}"""
    assert should_skip_csharp(content) is True


def test_with_method_implementation():
    # File with method implementation should not be skipped
    content = """using System;

namespace MyApp.Services {
    public class UserService {
        public User GetById(int id) {
            // Method implementation
            return repository.Find(id);
        }
    }
}"""
    assert should_skip_csharp(content) is False


def test_class_with_logic():
    # Class with logic should not be skipped
    content = """using System;

namespace MyApp {
    public class Calculator {
        public int Add(int a, int b) {
            if (a < 0 || b < 0) {
                throw new ArgumentException("Negative numbers not allowed");
            }
            return a + b;
        }
    }
}"""
    assert should_skip_csharp(content) is False


def test_property_with_logic():
    # Properties with custom logic should not be skipped
    content = """using System;

namespace MyApp.Models {
    public class User {
        private string _name;

        public string Name {
            get => _name;
            set {
                if (string.IsNullOrEmpty(value)) {
                    throw new ArgumentException("Name cannot be empty");
                }
                _name = value;
            }
        }
    }
}"""
    assert should_skip_csharp(content) is False
