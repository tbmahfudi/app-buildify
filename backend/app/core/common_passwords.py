"""
Common passwords list (top 100 most common passwords to block)
Source: Compiled from various security breach datasets
"""

COMMON_PASSWORDS = {
    "password", "123456", "123456789", "12345678", "12345", "1234567", "password1",
    "1234567890", "abc123", "111111", "123123", "qwerty", "iloveyou", "admin",
    "welcome", "monkey", "login", "letmein", "1234", "master", "hello", "freedom",
    "whatever", "qazwsx", "trustno1", "jordan", "passw0rd", "batman", "zaq1zaq1",
    "qwerty123", "football", "password123", "sunshine", "princess", "123321",
    "dragon", "starwars", "charlie", "666666", "ashley", "bailey", "passw0rd!",
    "shadow", "michael", "jennifer", "jessica", "superman", "ninja", "mustang",
    "access", "696969", "654321", "password!", "test", "demo", "changeme",
    "123qwe", "1q2w3e4r", "1q2w3e4r5t", "qwertyuiop", "P@ssw0rd", "P@ssword",
    "P@ssword1", "Password1", "Password123", "admin123", "root", "toor",
    "abcd1234", "test123", "welcome1", "temp123", "pass", "pass123", "guest",
    "default", "letmein123", "hunter", "hunter2", "baseball", "hockey", "soccer",
    "killer", "harley", "ranger", "michelle", "andrew", "silver", "flower",
    "sunshine1", "summer", "football1", "winter", "master123", "lovely", "buster",
    "computer", "corvette", "mercedes", "samsung", "chicken", "purple", "cheese",
}


def is_common_password(password: str) -> bool:
    """
    Check if password is in the common passwords list (case-insensitive).

    Args:
        password: Password to check

    Returns:
        True if password is common, False otherwise
    """
    return password.lower() in COMMON_PASSWORDS
