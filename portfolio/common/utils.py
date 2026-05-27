def sanitize_header(value: str) -> str:
    """Strip CR/LF from a string before splicing into an email header.

    Why: prevents header injection (Bcc/Cc/Reply-To smuggling) via
    newline characters in user-controlled form fields.
    """
    return (value or '').replace('\r', ' ').replace('\n', ' ').strip()
