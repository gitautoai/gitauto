from typing import Literal, TypedDict

from services.github.types.owner import OwnerType


class EventBridgeSchedulerEvent(TypedDict):
    """Event payload structure from AWS EventBridge Scheduler"""

    ownerId: int
    ownerType: OwnerType
    ownerName: str
    repoId: int
    repoName: str
    userId: int
    userName: str
    installationId: int
    triggerType: Literal["schedule"]
    scheduleTimeUTC: str  # "HH:MM" format
    includeWeekends: bool


class LambdaContextIdentity(TypedDict):
    """Lambda context identity structure"""

    cognito_identity_id: None
    cognito_identity_pool_id: None


class LambdaContextType(TypedDict):
    """Lambda context object structure"""

    aws_request_id: str
    log_group_name: str
    log_stream_name: str
    function_name: str
    memory_limit_in_mb: int
    function_version: str
    invoked_function_arn: str
    client_context: None
    identity: LambdaContextIdentity
    tenant_id: None
