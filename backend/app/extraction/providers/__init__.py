"""Provider registry. To support a new measurement provider, add a ProviderParser subclass here."""

from .base import ProviderParser
from .demo_a import DemoProviderAParser
from .demo_b import DemoProviderBParser
from .generic import GenericParser

PROVIDERS: list[ProviderParser] = [DemoProviderAParser(), DemoProviderBParser()]
GENERIC = GenericParser()


def detect(text: str) -> ProviderParser | None:
    return next((p for p in PROVIDERS if p.matches(text)), None)
