from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_valid_line_number(val: int | str):
    # Check if the value is an integer and greater than 1
    if isinstance(val, int):
        return val > 1

    # Check if the value is a string but is a valid integer and greater than 1
    return isinstance(val, str) and val.isdigit() and int(val) > 1
