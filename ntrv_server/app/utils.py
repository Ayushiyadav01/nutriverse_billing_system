from datetime import datetime, date, time
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Union

from app.models import DiscountType


def calculate_line_total(qty: int, unit_price: Decimal) -> Decimal:
    """Calculate line total for an order item"""
    if qty <= 0:
        raise ValueError("Quantity must be positive")
    if unit_price < 0:
        raise ValueError("Unit price cannot be negative")
    
    return (qty * unit_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_discount_amount(
    subtotal: Decimal, 
    discount_type: DiscountType, 
    discount_value: Decimal
) -> Decimal:
    """Calculate discount amount based on type and value"""
    if subtotal < 0:
        raise ValueError("Subtotal cannot be negative")
    if discount_value < 0:
        raise ValueError("Discount value cannot be negative")
    
    discount_amount = Decimal('0')
    
    if discount_type == DiscountType.FLAT:
        discount_amount = min(discount_value, subtotal)  # Can't discount more than subtotal
    elif discount_type == DiscountType.PERCENT:
        if discount_value > 100:
            raise ValueError("Percentage discount cannot exceed 100%")
        discount_amount = (subtotal * discount_value / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return discount_amount


def calculate_tax_amount(taxable_amount: Decimal, tax_percent: Decimal) -> Decimal:
    """Calculate tax amount based on taxable amount and tax percentage"""
    if taxable_amount < 0:
        raise ValueError("Taxable amount cannot be negative")
    if tax_percent < 0:
        raise ValueError("Tax percentage cannot be negative")
    
    return (taxable_amount * tax_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_order_totals(
    items: List[Dict],
    discount_type: DiscountType = DiscountType.NONE,
    discount_value: Decimal = Decimal('0'),
    tax_percent: Decimal = Decimal('0'),
    other_costs: Decimal = Decimal('0'),
    round_to_integer: bool = False
) -> Dict:
    """
    Calculate all order totals based on items and other parameters
    
    Args:
        items: List of dicts with keys: qty, unit_price, unit_cost
        discount_type: Type of discount (none, percent, flat)
        discount_value: Value of discount (amount or percentage)
        tax_percent: Tax percentage
        other_costs: Additional costs to subtract from profit
        round_to_integer: Whether to round the final total to nearest integer
    
    Returns:
        Dict with all calculated totals
    """
    # Validate inputs
    if not items:
        raise ValueError("Order must contain at least one item")
    
    # Calculate subtotal and total making cost
    subtotal = Decimal('0')
    total_making_cost = Decimal('0')
    
    for item in items:
        qty = item.get('qty', 0)
        unit_price = item.get('unit_price', Decimal('0'))
        unit_cost = item.get('unit_cost', Decimal('0'))
        
        if qty <= 0:
            raise ValueError("Item quantity must be positive")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        if unit_cost < 0:
            raise ValueError("Unit cost cannot be negative")
        
        line_total = calculate_line_total(qty, unit_price)
        line_cost = calculate_line_total(qty, unit_cost)
        
        subtotal += line_total
        total_making_cost += line_cost
    
    # Calculate discount
    discount_amount = calculate_discount_amount(subtotal, discount_type, discount_value)
    
    # Calculate tax
    taxable_amount = subtotal - discount_amount
    tax_amount = calculate_tax_amount(taxable_amount, tax_percent)
    
    # Calculate final totals
    total_amount = taxable_amount + tax_amount
    
    # Round to nearest integer if requested
    if round_to_integer:
        total_amount = total_amount.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
    
    # Calculate profit metrics
    net_amount = total_amount - total_making_cost
    total_profit = net_amount - other_costs
    
    return {
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "taxable_amount": taxable_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "total_making_cost": total_making_cost,
        "other_costs": other_costs,
        "net_amount": net_amount,
        "total_profit": total_profit
    }


def round_to_nearest_integer(amount: Decimal) -> Decimal:
    """Round amount to nearest integer"""
    return amount.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)


def get_time_of_day(dt: datetime) -> str:
    """Get time of day category (morning, afternoon, evening, night) from datetime"""
    hour = dt.hour
    
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"

