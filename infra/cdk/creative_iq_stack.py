"""
CreativeIQ CDK stack (mirrors the CarbonClarity / DriveScore pattern).

  * Lambda (Python 3.12, x86_64) running the FastAPI backend via Mangum behind a
    Function URL (no Docker — Linux wheels). Bundles the synthetic data + the
    pre-generated hero images, served by the app's /data route.
  * Image generation uses the keyless text-to-image endpoint in DIRECT mode
    (CREATIVEIQ_IMAGE_DIRECT=1) so a cache-miss returns the image URL for the
    browser to load — no writes to the read-only Lambda filesystem.
  * IAM: bedrock:InvokeModel* (used only when USE_BEDROCK=1).
  * Frontend: private S3 + CloudFront (OAC, HTTPS) serving frontend/dist, built
    with VITE_API_BASE = VITE_ASSET_BASE = the Function URL (so /api calls and
    /data images both resolve to the Lambda).

Personal account <APP_ACCOUNT> / ap-southeast-1 only (see app.py guardrail +
scripts/deploy.sh account check).
"""
import os

from aws_cdk import (
    Stack, Duration, CfnOutput, RemovalPolicy,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cf,
    aws_cloudfront_origins as origins,
)
from constructs import Construct

REGION = "ap-southeast-1"


class CreativeIqStack(Stack):
    def __init__(self, scope: Construct, cid: str, **kwargs) -> None:
        super().__init__(scope, cid, **kwargs)

        backend_asset = os.environ.get("BACKEND_ASSET", "../../build/backend")
        frontend_asset = os.environ.get("FRONTEND_ASSET", "../../frontend/dist")

        fn = _lambda.Function(
            self, "Api",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.X86_64,
            handler="lambda_function.handler",
            code=_lambda.Code.from_asset(backend_asset),
            timeout=Duration.seconds(60),
            memory_size=1024,
            environment={
                "CREATIVEIQ_DATA_DIR": "/var/task/data",
                "CREATIVEIQ_IMAGE_DIRECT": "1",
                "USE_BEDROCK": os.environ.get("USE_BEDROCK", "0"),
                "CREATIVEIQ_REGION": REGION,
            },
        )

        fn.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
            resources=[
                "arn:aws:bedrock:*::foundation-model/anthropic.*",
                "arn:aws:bedrock:*::foundation-model/amazon.*",
                f"arn:aws:bedrock:*:{self.account}:inference-profile/*",
            ],
        ))

        furl = fn.add_function_url(auth_type=_lambda.FunctionUrlAuthType.NONE)

        site = s3.Bucket(
            self, "Site",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=True,
        )

        dist = cf.Distribution(
            self, "Cdn",
            default_behavior=cf.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(site),
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
            error_responses=[
                cf.ErrorResponse(http_status=403, response_http_status=200, response_page_path="/index.html"),
                cf.ErrorResponse(http_status=404, response_http_status=200, response_page_path="/index.html"),
            ],
            comment="CreativeIQ static site",
        )

        s3deploy.BucketDeployment(
            self, "Deploy",
            sources=[s3deploy.Source.asset(frontend_asset)],
            destination_bucket=site,
            distribution=dist,
            distribution_paths=["/*"],
        )

        CfnOutput(self, "FunctionUrl", value=furl.url)
        CfnOutput(self, "SiteUrl", value=f"https://{dist.distribution_domain_name}")
        CfnOutput(self, "BucketName", value=site.bucket_name)
