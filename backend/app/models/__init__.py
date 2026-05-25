# SQLAlchemy ORM models — imported here so SQLAlchemy can discover them
# when Base.metadata.create_all() is called.

from app.models.project import Project  # noqa: F401
from app.models.document import Document  # noqa: F401
