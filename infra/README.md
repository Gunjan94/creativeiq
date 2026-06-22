# infra/ — AWS CDK (deferred)

This is a **stub** for the cloud deploy. The prototype is graded as a **local run** (see the
repo README) — CDK/cloud deploy is intentionally deferred per the build plan.

When you take this to AWS, `lib/creativeiq-stack.ts` provisions (BUILDER §10):

- **S3** bucket for creatives + the pre-generated hero set.
- **4 Lambdas** (Python 3.12) wrapping `backend/handlers/{generate,predict,segments,catalog}.py`
  via their `lambda_handler(event, context)` entrypoints (already present).
- **API Gateway (HTTP API)** routing `POST /generate`, `POST /predict`, `GET /segments`, `GET /catalog`.
  `/generate` uses Lambda response streaming for SSE.
- **IAM least-privilege:** only `bedrock:InvokeModel` + `bedrock:InvokeModelWithResponseStream`
  and S3 read/write on the single bucket. No broad permissions.

Deploy (after implementing the stack):
```bash
cd infra && npm install && npx cdk bootstrap && npx cdk deploy --require-approval never
```
The handlers swap `core/storage.py` (local file writes) for S3 `put_object`; everything else
(perf model, prompts, cache, bedrock) is already cloud-ready and runs unchanged in Lambda.
