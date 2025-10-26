from os import system, name


def clear():
    """Cross-platform clear."""
    if name == 'nt':
        system('cls')
    else:
        system('clear')


def prompt_with_back(prompt_text):
    """Prompt helper: returns None if user pressed Enter or 'b' (case-insensitive).
    Otherwise returns the raw stripped input string.
    """
    choice = input(prompt_text).strip()
    if choice == '' or choice.lower() == 'b':
        return None
    return choice
