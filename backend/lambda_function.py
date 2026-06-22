"""AWS Lambda entry point — wraps the CreativeIQ FastAPI app with Mangum.

Used only in the deployed Lambda (behind a Function URL). Local dev runs uvicorn
directly. Mangum buffers responses, so the /generate SSE returns its full body at
once on Lambda — content identical; live token streaming is a local-only nicety.
"""
from mangum import Mangum

from app import app

handler = Mangum(app, lifespan="off")
