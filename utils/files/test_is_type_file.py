from utils.files.is_type_file import is_type_file


def test_type_directories():
    # Type directories with singular and plural forms
    assert is_type_file("services/github/types/user.py") is True
    assert is_type_file("src/types/api.ts") is True
    assert is_type_file("types/constants.py") is True
    assert is_type_file("type/user.py") is True
    assert is_type_file("app/type/models.js") is True


def test_type_file_naming_patterns():
    # Files with .type. or .types. in the name
    assert is_type_file("user.types.ts") is True
    assert is_type_file("api.type.js") is True
    assert is_type_file("models.types.py") is True
    assert is_type_file("config.type.json") is True


def test_typescript_declaration_files():
    # TypeScript declaration files (.d.ts)
    assert is_type_file("index.d.ts") is True
    assert is_type_file("global.d.ts") is True
    assert is_type_file("types.d.ts") is True
    assert is_type_file("api.d.ts") is True


def test_type_prefix_patterns():
    # Files starting with types or type
    assert is_type_file("UserTypes.java") is True
    assert is_type_file("ApiType.cs") is True
    assert is_type_file("types.user.py") is True
    assert is_type_file("type.api.js") is True


def test_type_underscore_patterns():
    # Files with underscore patterns
    assert is_type_file("user_types.py") is True
    assert is_type_file("api_type.py") is True
    assert is_type_file("types_user.py") is True
    assert is_type_file("type_api.py") is True


def test_schema_directories():
    # Schema directories
    assert is_type_file("schemas/user.py") is True
    assert is_type_file("schema/api.py") is True
    assert is_type_file("app/schemas/models.js") is True
    assert is_type_file("src/schema/types.ts") is True


def test_schema_file_patterns():
    # Schema file naming patterns
    assert is_type_file("user.schema.ts") is True
    assert is_type_file("api.schema.json") is True
    assert is_type_file("UserSchema.java") is True
    assert is_type_file("ApiSchemas.cs") is True


def test_interface_directories():
    # Interface directories
    assert is_type_file("interfaces/user.py") is True
    assert is_type_file("interface/api.py") is True
    assert is_type_file("app/interfaces/models.js") is True
    assert is_type_file("src/interface/types.ts") is True


def test_interface_file_patterns():
    # Interface file naming patterns
    assert is_type_file("user.interface.ts") is True
    assert is_type_file("api.interface.js") is True
    assert is_type_file("UserInterface.java") is True
    assert is_type_file("ApiInterfaces.cs") is True


def test_model_files():
    # Python model files (data classes without business logic)
    assert is_type_file("models/user.py") is True
    assert is_type_file("model/api.py") is True
    assert is_type_file("app/models/customer.py") is True
    assert is_type_file("src/model/product.py") is True
    # Non-Python model files should not match this pattern
    assert is_type_file("models/user.js") is False
    assert is_type_file("model/api.ts") is False


def test_constants_directories():
    # Constants directories
    assert is_type_file("constants/urls.py") is True
    assert is_type_file("constant/messages.py") is True
    assert is_type_file("app/constants/config.js") is True
    assert is_type_file("src/constant/api.ts") is True


def test_constants_file_patterns():
    # Constants file naming patterns
    assert is_type_file("user.constants.ts") is True
    assert is_type_file("api.constant.js") is True
    assert is_type_file("UserConstants.java") is True
    assert is_type_file("ApiConstants.cs") is True
    assert is_type_file("user_constants.py") is True
    assert is_type_file("api_constant.py") is True


def test_enum_directories():
    # Enum directories
    assert is_type_file("enums/status.py") is True
    assert is_type_file("enum/types.py") is True
    assert is_type_file("app/enums/colors.js") is True
    assert is_type_file("src/enum/states.ts") is True


def test_enum_file_patterns():
    # Enum file naming patterns
    assert is_type_file("status.enums.ts") is True
    assert is_type_file("types.enum.js") is True
    assert is_type_file("StatusEnums.java") is True
    assert is_type_file("TypeEnums.cs") is True


def test_case_insensitive_matching():
    # Test case insensitive matching
    assert is_type_file("TYPES/USER.PY") is True
    assert is_type_file("User.TYPES.TS") is True
    assert is_type_file("API.D.TS") is True
    assert is_type_file("SCHEMAS/CONFIG.JSON") is True
    assert is_type_file("INTERFACES/MODEL.JS") is True
    assert is_type_file("CONSTANTS/URLS.PY") is True
    assert is_type_file("ENUMS/STATUS.PY") is True


def test_non_type_files():
    # Regular files that should not be considered type files
    assert is_type_file("user_service.py") is False
    assert is_type_file("api_handler.js") is False
    assert is_type_file("test_user.py") is False
    assert is_type_file("main.py") is False
    assert is_type_file("config.json") is False
    assert is_type_file("utils/helpers.py") is False
    assert is_type_file("src/components/Button.tsx") is False


def test_invalid_input():
    # Test with invalid input types (decorator should handle these)
    assert is_type_file(None) is False
    assert is_type_file(123) is False
    assert is_type_file([]) is False
    assert is_type_file({}) is False
    assert is_type_file("") is False


def test_edge_cases_with_paths():
    # Test edge cases with different path separators and structures
    assert is_type_file("src\\types\\user.py") is False  # Windows path separator not supported
    assert is_type_file("./types/config.js") is True
    assert is_type_file("../type/models.py") is True
    assert is_type_file("deeply/nested/types/complex/structure.ts") is True


def test_mixed_patterns():
    # Test files that might match multiple patterns
    assert is_type_file("types/UserTypes.java") is True  # Both directory and naming pattern
    assert is_type_file("schemas/user.schema.ts") is True  # Both directory and file pattern
    assert is_type_file("interfaces/api.interface.js") is True  # Both directory and file pattern
    assert is_type_file("constants/app.constants.py") is True  # Both directory and file pattern


def test_partial_matches_should_not_match():
    # Test files that contain type-related words but shouldn't match patterns
    assert is_type_file("user_service_types_handler.py") is False  # Contains "types" but not in pattern
    assert is_type_file("schema_validator.py") is False  # Contains "schema" but not in pattern
    assert is_type_file("interface_manager.py") is False  # Contains "interface" but not in pattern
    assert is_type_file("constant_loader.py") is False  # Contains "constant" but not in pattern
    assert is_type_file("enum_parser.py") is False  # Contains "enum" but not in pattern
    assert is_type_file("model_factory.py") is False  # Contains "model" but not in pattern


def test_boundary_conditions():
    # Test boundary conditions for regex patterns
    assert is_type_file("type") is False  # Just the word "type" without extension
    assert is_type_file("types") is False  # Just the word "types" without extension
    assert is_type_file("type.") is True  # Matches "types?." pattern
    assert is_type_file("types.") is True  # Matches "types?." pattern
    assert is_type_file("_type.py") is True  # Matches "_types?." pattern
    assert is_type_file("_types.js") is True  # Matches "_types?." pattern
    assert is_type_file("type_") is False  # Doesn't match any pattern
    assert is_type_file("types_") is False  # Doesn't match any pattern


def test_specific_model_file_restrictions():
    # Test that only Python model files match the model pattern
    assert is_type_file("models/user.py") is True
    assert is_type_file("model/api.py") is True
    assert is_type_file("models/config.js") is False  # Not Python
    assert is_type_file("model/types.ts") is False  # Not Python
    assert is_type_file("models/data.java") is False  # Not Python
    assert is_type_file("models/service.rb") is False  # Not Python
    assert is_type_file("model/handler.php") is False  # Not Python
    assert is_type_file("models/component.tsx") is False  # Not Python
