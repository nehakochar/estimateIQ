# parsers package — exposes the factory function as the public API.
# Callers should import `get_parser` from here rather than importing
# individual parser classes directly.  This keeps the rest of the
# codebase decoupled from the concrete parser implementations.

from app.services.parsers.factory import get_parser  # noqa: F401
