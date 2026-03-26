"""
Pricing service: cost calculation from model catalog prices.
"""
from decimal import Decimal


def calculate_cost(
    input_price_per_1k: float,
    output_price_per_1k: float,
    prompt_tokens: int,
    completion_tokens: int,
) -> tuple[float, float, float]:
    """
    Calculate (cost_input, cost_output, total_cost) in USD.
    Prices are per 1,000 tokens.
    Uses Decimal arithmetic to avoid floating-point drift.
    """
    p_in = Decimal(str(input_price_per_1k))
    p_out = Decimal(str(output_price_per_1k))

    cost_in = p_in * Decimal(prompt_tokens) / Decimal("1000")
    cost_out = p_out * Decimal(completion_tokens) / Decimal("1000")
    total = cost_in + cost_out

    return float(cost_in), float(cost_out), float(total)
