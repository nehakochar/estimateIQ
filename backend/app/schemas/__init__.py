# This file makes the 'schemas' directory a Python package.
#
# What goes here?
# Pydantic schemas — define the shape of request/response data for your APIs.
# They are separate from SQLAlchemy models on purpose:
#   - Models = what's stored in the database
#   - Schemas = what the API accepts and returns
#
# Example (future):
#   from app.schemas.rfp import RFPCreate, RFPResponse
