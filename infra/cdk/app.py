"""CDK app entry — CreativeIQ.

Pinned to the account set via DEPLOY_ACCOUNT / ap-southeast-1, with a guardrail
that aborts if the resolved credentials point anywhere else.
"""
import os
import sys

import aws_cdk as cdk

from creative_iq_stack import CreativeIqStack

ACCOUNT = os.environ.get("DEPLOY_ACCOUNT") or os.environ.get("CDK_DEFAULT_ACCOUNT")
REGION = "ap-southeast-1"

resolved = os.environ.get("CDK_DEFAULT_ACCOUNT")
if resolved and resolved != ACCOUNT:
    sys.exit(
        f"\n[GUARDRAIL] Refusing to deploy: resolved AWS account {resolved} != "
        f"personal account {ACCOUNT}.\nUse `AWS_PROFILE=gunjan-aws cdk deploy`.\n"
    )

app = cdk.App()
CreativeIqStack(
    app, "CreativeIqStack",
    env=cdk.Environment(account=ACCOUNT, region=REGION),
    description="CreativeIQ — AI retail ad studio (personal account only)",
)
app.synth()
