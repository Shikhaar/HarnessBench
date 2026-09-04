"""Model pricing definitions and financial cost calculation."""

from decimal import Decimal
from typing import Dict, Optional
from pydantic import BaseModel


class PricingModel(BaseModel):
    """Cost rates per 1,000,000 tokens in USD."""
    input_cost_per_million: Decimal
    output_cost_per_million: Decimal
    cache_read_cost_per_million: Decimal = Decimal("0.0")
    cache_write_cost_per_million: Decimal = Decimal("0.0")

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
    ) -> float:
        """Calculate total USD cost with high decimal precision."""
        in_cost = (Decimal(input_tokens) * self.input_cost_per_million) / Decimal("1000000")
        out_cost = (Decimal(output_tokens) * self.output_cost_per_million) / Decimal("1000000")
        cache_read_cost = (Decimal(cache_read_tokens) * self.cache_read_cost_per_million) / Decimal("1000000")
        cache_write_cost = (Decimal(cache_write_tokens) * self.cache_write_cost_per_million) / Decimal("1000000")

        total = in_cost + out_cost + cache_read_cost + cache_write_cost
        return float(round(total, 6))


# Standard model pricing catalog (USD per million tokens)
PRICING_CATALOG: Dict[str, PricingModel] = {
    # Anthropic Claude 3.5 Sonnet
    "claude-3-5-sonnet-20241022": PricingModel(
        input_cost_per_million=Decimal("3.00"),
        output_cost_per_million=Decimal("15.00"),
        cache_read_cost_per_million=Decimal("0.30"),
        cache_write_cost_per_million=Decimal("3.75"),
    ),
    "claude-3-5-sonnet-latest": PricingModel(
        input_cost_per_million=Decimal("3.00"),
        output_cost_per_million=Decimal("15.00"),
        cache_read_cost_per_million=Decimal("0.30"),
        cache_write_cost_per_million=Decimal("3.75"),
    ),
    "claude-3-5-haiku-20241022": PricingModel(
        input_cost_per_million=Decimal("1.00"),
        output_cost_per_million=Decimal("5.00"),
        cache_read_cost_per_million=Decimal("0.10"),
        cache_write_cost_per_million=Decimal("1.25"),
    ),
    "claude-3-opus-20240229": PricingModel(
        input_cost_per_million=Decimal("15.00"),
        output_cost_per_million=Decimal("75.00"),
        cache_read_cost_per_million=Decimal("1.50"),
        cache_write_cost_per_million=Decimal("18.75"),
    ),
    # OpenAI GPT-4o
    "gpt-4o": PricingModel(
        input_cost_per_million=Decimal("2.50"),
        output_cost_per_million=Decimal("10.00"),
        cache_read_cost_per_million=Decimal("1.25"),
    ),
    "gpt-4o-mini": PricingModel(
        input_cost_per_million=Decimal("0.15"),
        output_cost_per_million=Decimal("0.60"),
        cache_read_cost_per_million=Decimal("0.075"),
    ),
    # Fallback default pricing (Sonnet baseline)
    "default": PricingModel(
        input_cost_per_million=Decimal("3.00"),
        output_cost_per_million=Decimal("15.00"),
        cache_read_cost_per_million=Decimal("0.30"),
        cache_write_cost_per_million=Decimal("3.75"),
    ),
}


def get_pricing_for_model(model_name: str) -> PricingModel:
    """Find pricing model for a given model string, with fuzzy alias matching."""
    norm = model_name.strip().lower()
    if norm in PRICING_CATALOG:
        return PRICING_CATALOG[norm]

    for key, pricing in PRICING_CATALOG.items():
        if key in norm or norm in key:
            return pricing

    return PRICING_CATALOG["default"]


def calculate_api_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """Convenience helper to compute USD cost for a model usage record."""
    pricing = get_pricing_for_model(model)
    return pricing.calculate_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
    )
