"""Env-var-backed credentials.

Populated by a k8s secret mounted via `envFrom` on the agent container.
The secret name is selected per-session through `secret_refs` on start_session,
falling back to whatever is configured in DEFAULT_AGENT_SECRET_REF on the
agent-server.
"""

import os

SERVICE_NAME = "intacct-integration"  # retained for back-compat only
ENV_PREFIX = "INTACCT_"

REQUIRED_KEYS = (
    "sender_id",
    "sender_password",
    "company_id",
    "user_id",
    "user_password",
)


def get_secret(key: str) -> str:
    """Retrieve a credential from the process environment."""
    env_name = f"{ENV_PREFIX}{key.upper()}"
    value = os.environ.get(env_name)
    if not value:
        raise KeyError(
            f"Missing env var {env_name}. Ensure the job has a k8s secret mounted "
            f"via `secret_refs` on start_session, or that a default "
            f"`intacct-credentials` secret is configured in the cluster."
        )
    return value
