# SQLAlchemy ORM models — imported here so SQLAlchemy can discover them
# when Base.metadata.create_all() is called at startup.
#
# Rule: every new model file MUST be imported here, otherwise its table
# will never be created in the database.

from app.models.project import Project  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.processing_job import ProcessingJob  # noqa: F401
from app.models.document_chunk import DocumentChunk  # noqa: F401
