// CreativeIqStack — DEFERRED stub for cloud deploy (prototype runs locally; see infra/README.md).
//
// When activated, this stack provisions: an S3 bucket for creatives + hero set, four Python 3.12
// Lambdas wrapping backend/handlers/*.py, an HTTP API Gateway, and least-privilege IAM
// (bedrock:InvokeModel[WithResponseStream] + S3 on the single bucket only). Streaming /generate
// uses Lambda response streaming. The skeleton below shows the intended shape.
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
// import * as s3 from "aws-cdk-lib/aws-s3";
// import * as lambda from "aws-cdk-lib/aws-lambda";
// import * as apigw from "aws-cdk-lib/aws-apigatewayv2";
// import * as iam from "aws-cdk-lib/aws-iam";

export class CreativeIqStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // const bucket = new s3.Bucket(this, "CreativesBucket", {
    //   blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    //   removalPolicy: cdk.RemovalPolicy.DESTROY, // demo only
    // });

    // const bedrockPolicy = new iam.PolicyStatement({
    //   actions: ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
    //   resources: ["*"], // scope to specific model ARNs in production
    // });

    // const makeFn = (name: string, handler: string) =>
    //   new lambda.Function(this, name, {
    //     runtime: lambda.Runtime.PYTHON_3_12,
    //     code: lambda.Code.fromAsset("../backend"),
    //     handler, // e.g. "handlers.generate.lambda_handler"
    //     timeout: cdk.Duration.seconds(30),
    //     environment: { USE_BEDROCK: "1", CREATIVEIQ_REGION: this.region },
    //   });

    // const generateFn = makeFn("GenerateFn", "handlers.generate.lambda_handler");
    // ... predict / segments / catalog ...
    // bucket.grantReadWrite(generateFn);
    // generateFn.addToRolePolicy(bedrockPolicy);

    // const api = new apigw.HttpApi(this, "CreativeIqApi");
    // api.addRoutes({ path: "/generate", methods: [apigw.HttpMethod.POST], integration: ... });

    // new cdk.CfnOutput(this, "ApiBaseUrl", { value: api.apiEndpoint });

    new cdk.CfnOutput(this, "Status", {
      value: "DEFERRED: implement resources above to deploy. Prototype runs locally (see repo README).",
    });
  }
}
