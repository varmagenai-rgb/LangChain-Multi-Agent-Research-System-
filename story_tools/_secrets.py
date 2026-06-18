"""Azure Key Vault secret fetch.

Uses the same AzureCliCredential the user already runs `az login` for. Caches
the secret per-process so we only call Key Vault once even if the agent is
constructed multiple times.
"""

import os

from azure.identity import AzureCliCredential
from azure.keyvault.secrets import SecretClient

_cached_anthropic_key: str | None = None


def get_anthropic_api_key() -> str:
    """Fetch the Anthropic API key from Azure Key Vault.

    Requires:
    - AZURE_KEYVAULT_URL in env.
    - ANTHROPIC_KEY_SECRET_NAME in env.
    - `az login` performed by the caller with Key Vault Secrets User role
      assigned on the target vault.

    Cached per process.
    """
    global _cached_anthropic_key
    if _cached_anthropic_key is not None:
        return _cached_anthropic_key
    client = SecretClient(
        vault_url=os.environ["AZURE_KEYVAULT_URL"],
        credential=AzureCliCredential(),
    )
    secret = client.get_secret(os.environ["ANTHROPIC_KEY_SECRET_NAME"])
    _cached_anthropic_key = secret.value
    return _cached_anthropic_key
