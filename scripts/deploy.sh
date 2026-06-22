#!/usr/bin/env bash
# CreativeIQ — deploy to the PERSONAL AWS account only.
#   Frontend: S3 + CloudFront (HTTPS).  Backend: FastAPI on Lambda via Mangum
#   behind a Function URL (no Docker — Linux wheels). Bundles synthetic data +
#   pre-generated hero images (served by the app's /data route). Keyless image
#   generation runs in DIRECT mode (browser loads net-new images client-side).
#
# Usage:  AWS_PROFILE=gunjan-aws ./scripts/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."                      # scenario root
ROOT="$(pwd)"

PROFILE="${AWS_PROFILE:-gunjan-aws}"
ACCOUNT_EXPECTED="<APP_ACCOUNT>"
REGION="ap-southeast-1"

echo "==> 0/5  Verifying credentials point to the PERSONAL account"
ACCT=$(aws sts get-caller-identity --profile "$PROFILE" --query Account --output text)
if [ "$ACCT" != "$ACCOUNT_EXPECTED" ]; then
  echo "ABORT: profile '$PROFILE' resolves to account $ACCT, expected $ACCOUNT_EXPECTED."
  echo "       Refusing to deploy so your work account is never touched."
  exit 1
fi
echo "    OK — account $ACCT (region $REGION) via profile '$PROFILE'"
export AWS_PROFILE="$PROFILE" AWS_REGION="$REGION" CDK_DEFAULT_REGION="$REGION"
export CDK_DEFAULT_ACCOUNT="$ACCT"
export BACKEND_ASSET="$ROOT/build/backend"
export FRONTEND_ASSET="$ROOT/frontend/dist"

echo "==> 1/5  Packaging backend (Linux wheels — no Docker)"
rm -rf build/backend && mkdir -p build/backend/data
cp backend/app.py backend/lambda_function.py build/backend/
cp -r backend/core build/backend/core
cp -r backend/handlers build/backend/handlers
# Synthetic data + pre-generated hero assets served by the /data route.
cp data/*.json build/backend/data/
cp -r data/catalog build/backend/data/catalog
cp -r data/generated build/backend/data/generated
cp -r data/hero_set build/backend/data/hero_set
# strip caches
find build/backend -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
python3 -m pip install \
  --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 \
  --only-binary=:all: --no-compile --upgrade --target build/backend \
  -r backend/requirements.txt

echo "==> 2/5  CDK bootstrap (idempotent) + first deploy"
cd infra/cdk
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip install --quiet -r requirements.txt
export PATH="$PWD/.venv/bin:$PATH"
( cd "$ROOT/frontend" && npm install >/dev/null 2>&1 || true && npm run build >/dev/null )
cdk bootstrap "aws://$ACCOUNT_EXPECTED/$REGION" >/dev/null 2>&1 || cdk bootstrap "aws://$ACCOUNT_EXPECTED/$REGION"
cdk deploy --require-approval never

echo "==> 3/5  Reading the Function URL"
FURL=$(aws cloudformation describe-stacks --stack-name CreativeIqStack \
  --query "Stacks[0].Outputs[?OutputKey=='FunctionUrl'].OutputValue" --output text)
FURL="${FURL%/}"
echo "    Function URL: $FURL"

echo "==> 4/5  Rebuilding frontend against the live API + redeploying"
# Both /api calls and /data images resolve to the Lambda Function URL.
( cd "$ROOT/frontend" && VITE_API_BASE="$FURL" VITE_ASSET_BASE="$FURL" npm run build >/dev/null )
cdk deploy --require-approval never

echo "==> 5/5  Done"
SITE=$(aws cloudformation describe-stacks --stack-name CreativeIqStack \
  --query "Stacks[0].Outputs[?OutputKey=='SiteUrl'].OutputValue" --output text)
echo
echo "CreativeIQ is live:"
echo "  Frontend : $SITE"
echo "  API      : $FURL"
echo "  (Bedrock live AI: redeploy with USE_BEDROCK=1 once model access is enabled.)"
