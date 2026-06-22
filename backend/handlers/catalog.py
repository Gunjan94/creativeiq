"""catalog.py — GET /catalog. Plain function; Lambda-shaped."""
from core import data


def get_catalog():
    return data.catalog()


def lambda_handler(event, context):  # AWS Lambda entrypoint
    import json
    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(get_catalog())}
