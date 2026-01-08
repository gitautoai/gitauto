def get_first_name(user_name: str) -> str:
    if not user_name:
        return "there"

    # Split by spaces and take the first part
    parts = user_name.strip().split()
    if parts:
        return parts[0]

    return "there"
