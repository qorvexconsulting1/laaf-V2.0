from laaf.platforms.base import AbstractPlatform, PlatformResponse
from laaf.platforms.mock_platform import MockPlatform

__all__ = ["AbstractPlatform", "PlatformResponse", "MockPlatform"]


def get_platform(name: str, **kwargs) -> AbstractPlatform:
    """Factory to instantiate a platform by name."""
    name = name.lower().strip()

    if name == "openai":
        from laaf.platforms.openai_platform import OpenAIPlatform
        return OpenAIPlatform(**kwargs)
    elif name in ("anthropic", "claude"):
        from laaf.platforms.anthropic_platform import AnthropicPlatform
        return AnthropicPlatform(**kwargs)
    elif name in ("google", "gemini"):
        from laaf.platforms.google_platform import GooglePlatform
        return GooglePlatform(**kwargs)
    elif name in ("huggingface", "hf"):
        from laaf.platforms.huggingface_platform import HuggingFacePlatform
        return HuggingFacePlatform(**kwargs)
    elif name in ("azure", "azure-openai", "copilot"):
        from laaf.platforms.azure_platform import AzureOpenAIPlatform
        return AzureOpenAIPlatform(**kwargs)
    elif name in ("openrouter", "or"):
        from laaf.platforms.openrouter_platform import OpenRouterPlatform
        return OpenRouterPlatform(**kwargs)
    elif name == "mock":
        return MockPlatform(**kwargs)
    else:
        raise ValueError(f"Unknown platform: {name!r}. Choose: openai, anthropic, google, huggingface, azure, openrouter, mock")
