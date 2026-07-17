# Adding a Provider to commitcraft

Each provider is a single file in `commitcraft/providers/`. Here's exactly how to add one.

## Step 1: Create your provider file

Create `commitcraft/providers/myprovider_provider.py`:

```python
from commitcraft.config.models import CommitcraftConfig
from commitcraft.providers.base import Provider
from commitcraft.providers.ollama_provider import _COMMIT_SYSTEM, _PR_SYSTEM, _RELEASE_SYSTEM


class MyProvider(Provider):
    def __init__(self, config: CommitcraftConfig) -> None:
        self._config = config
        # initialize your SDK client here

    @property
    def name(self) -> str:
        return "myprovider"

    def _generate(self, system: str, prompt: str) -> str:
        # call your provider's API
        # return the generated text as a string
        ...

    def generate_commit_message(self, context: str) -> str:
        return self._generate(_COMMIT_SYSTEM, context)

    def generate_pr_description(self, context: str) -> str:
        return self._generate(_PR_SYSTEM, context)

    def generate_release_notes(self, context: str) -> str:
        return self._generate(_RELEASE_SYSTEM, context)

    def health_check(self) -> bool:
        try:
            # ping your provider
            return True
        except Exception:
            return False
```

## Step 2: Add a config field

In `commitcraft/config/models.py`, add to `CommitcraftConfig`:

```python
myprovider_api_key: str | None = None
myprovider_model: str = "default-model-name"
```

Also add `MYPROVIDER = "myprovider"` to the `ProviderName` enum.

## Step 3: Register in the factory

In `commitcraft/config/store.py`, add a case to `get_provider()`:

```python
case ProviderName.MYPROVIDER:
    from commitcraft.providers.myprovider_provider import MyProvider
    return MyProvider(config)
```

## Step 4: Add to the wizard

In `commitcraft/config/wizard.py`, add an entry to `_PROVIDER_CHOICES`:

```python
"5": (ProviderName.MYPROVIDER, "My Provider (description)"),
```

And handle key collection in the `run_wizard()` function.

## Step 5: Write tests

Add tests to `tests/test_providers.py` following the existing pattern (mock your SDK client).

## Step 6: Submit a PR

Run `pytest tests/ -v` and `ruff check commitcraft/` before submitting.
