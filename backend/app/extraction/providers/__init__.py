"""Provider registry. To support a new measurement provider, add a ProviderParser subclass here."""

from .aeroroof import AeroRoofParser
from .base import ProviderParser
from .generic import GenericParser
from .skymeasure import SkyMeasureParser

PROVIDERS: list[ProviderParser] = [SkyMeasureParser(), AeroRoofParser()]
GENERIC = GenericParser()


def detect(text: str) -> ProviderParser | None:
    return next((p for p in PROVIDERS if p.matches(text)), None)
