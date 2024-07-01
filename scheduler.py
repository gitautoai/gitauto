# This is scheduled to run by AWS Lambda
def schedule_handler(event, context) -> dict[str, int]:
    print(f"Event: {event}")
    print(f"Context: {context}")
    return {"statusCode": 200}
