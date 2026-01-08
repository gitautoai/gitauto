import re
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_type_file(filename: str) -> bool:

    # Convert to lowercase for case-insensitive matching
    filename_lower = filename.lower()

    # Type definition patterns
    type_patterns = [
        # Type directories
        r"/types?/",  # services/github/types/, src/types/
        r"^types?/",  # types/user.py, type/constants.py
        # Type file naming patterns
        r"\.types?\.",  # user.types.ts, api.type.js
        r"\.d\.ts$",  # TypeScript declaration files
        r"types?\.",  # UserTypes.java, ApiType.cs
        r"_types?\.",  # user_types.py, api_type.py
        r"^types?_",  # types_user.py, type_api.py
        # Schema and interface files
        r"/schemas?/",  # schemas/user.py, schema/api.py
        r"^schemas?/",  # schemas/user.py, schema/api.py
        r"\.schema\.",  # user.schema.ts, api.schema.json
        r"schemas?\.",  # UserSchema.java, ApiSchemas.cs
        # Interface files
        r"/interfaces?/",  # interfaces/user.py, interface/api.py
        r"^interfaces?/",  # interfaces/user.py, interface/api.py
        r"\.interface\.",  # user.interface.ts, api.interface.js
        r"interfaces?\.",  # UserInterface.java, ApiInterfaces.cs
        # Model definition files (without business logic)
        r"/models?/.*\.py$",  # Only Python model files that are typically just data classes
        r"^models?/.*\.py$",  # models/user.py, model/api.py
        # Constants and enums (often don't need testing)
        r"/constants?/",  # constants/urls.py, constant/messages.py
        r"^constants?/",  # constants/urls.py, constant/messages.py
        r"\.constants?\.",  # user.constants.ts, api.constant.js
        r"constants?\.",  # UserConstants.java, ApiConstants.cs
        r"_constants?\.",  # user_constants.py, api_constant.py
        r"/enums?/",  # enums/status.py, enum/types.py
        r"^enums?/",  # enums/status.py, enum/types.py
        r"\.enums?\.",  # status.enums.ts, types.enum.js
        r"enums?\.",  # StatusEnums.java, TypeEnums.cs
    ]

    # Check against all patterns
    for pattern in type_patterns:
        if re.search(pattern, filename_lower):
            return True

    return False
