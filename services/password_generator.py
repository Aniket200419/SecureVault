import secrets
import string

UPPERCASE = string.ascii_uppercase
LOWERCASE = string.ascii_lowercase
NUMBERS = string.digits
SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

def generate_password(length=16, use_uppercase=True, use_lowercase=True, use_numbers=True, use_symbols=True):
    """
    Generate a cryptographically secure random password based on specified criteria.
    Length ranges between 8 and 64.
    """
    length = max(8, min(64, int(length)))
    
    pools = []
    guaranteed = []
    
    if use_uppercase:
        pools.append(UPPERCASE)
        guaranteed.append(secrets.choice(UPPERCASE))
    if use_lowercase:
        pools.append(LOWERCASE)
        guaranteed.append(secrets.choice(LOWERCASE))
    if use_numbers:
        pools.append(NUMBERS)
        guaranteed.append(secrets.choice(NUMBERS))
    if use_symbols:
        pools.append(SYMBOLS)
        guaranteed.append(secrets.choice(SYMBOLS))
        
    if not pools:
        # Default fallback if nothing selected
        pools = [LOWERCASE, NUMBERS]
        guaranteed = [secrets.choice(LOWERCASE), secrets.choice(NUMBERS)]
        
    all_chars = "".join(pools)
    remaining_length = length - len(guaranteed)
    
    random_chars = [secrets.choice(all_chars) for _ in range(remaining_length)]
    combined = guaranteed + random_chars
    
    # Shuffle cryptographically using secrets
    shuffled = []
    while combined:
        idx = secrets.randbelow(len(combined))
        shuffled.append(combined.pop(idx))
        
    return "".join(shuffled)
