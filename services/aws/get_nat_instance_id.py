from services.aws.clients import ec2_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_nat_instance_id():
    response = ec2_client.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": ["gitauto-nat-instance"]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    reservations = response.get("Reservations", [])
    if not reservations:
        return None
    instances = reservations[0].get("Instances", [])
    if not instances:
        return None
    return instances[0].get("InstanceId")
