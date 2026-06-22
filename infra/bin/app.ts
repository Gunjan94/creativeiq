#!/usr/bin/env node
// CreativeIQ CDK app entrypoint (DEFERRED stub — see infra/README.md).
import * as cdk from "aws-cdk-lib";
import { CreativeIqStack } from "../lib/creativeiq-stack";

const app = new cdk.App();
new CreativeIqStack(app, "CreativeIqStack", {
  env: { region: process.env.CDK_DEFAULT_REGION || "ap-southeast-1" },
});
