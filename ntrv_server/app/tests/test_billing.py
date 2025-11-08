import unittest
from decimal import Decimal
import pytest

from app.models import DiscountType
from app.utils import (
    calculate_line_total,
    calculate_discount_amount,
    calculate_tax_amount,
    calculate_order_totals
)


class TestBillingCalculations(unittest.TestCase):
    def test_calculate_line_total(self):
        # Test normal case
        self.assertEqual(calculate_line_total(2, Decimal('10.50')), Decimal('21.00'))
        
        # Test zero quantity
        with self.assertRaises(ValueError):
            calculate_line_total(0, Decimal('10.50'))
        
        # Test negative quantity
        with self.assertRaises(ValueError):
            calculate_line_total(-1, Decimal('10.50'))
        
        # Test negative price
        with self.assertRaises(ValueError):
            calculate_line_total(2, Decimal('-10.50'))
    
    def test_calculate_discount_amount(self):
        # Test flat discount
        self.assertEqual(
            calculate_discount_amount(
                Decimal('100.00'), 
                DiscountType.FLAT, 
                Decimal('20.00')
            ), 
            Decimal('20.00')
        )
        
        # Test percentage discount
        self.assertEqual(
            calculate_discount_amount(
                Decimal('100.00'), 
                DiscountType.PERCENT, 
                Decimal('15')
            ), 
            Decimal('15.00')
        )
        
        # Test no discount
        self.assertEqual(
            calculate_discount_amount(
                Decimal('100.00'), 
                DiscountType.NONE, 
                Decimal('0')
            ), 
            Decimal('0')
        )
        
        # Test flat discount greater than subtotal
        self.assertEqual(
            calculate_discount_amount(
                Decimal('50.00'), 
                DiscountType.FLAT, 
                Decimal('100.00')
            ), 
            Decimal('50.00')  # Should be capped at subtotal
        )
        
        # Test 100% discount
        self.assertEqual(
            calculate_discount_amount(
                Decimal('100.00'), 
                DiscountType.PERCENT, 
                Decimal('100')
            ), 
            Decimal('100.00')
        )
        
        # Test discount percentage > 100%
        with self.assertRaises(ValueError):
            calculate_discount_amount(
                Decimal('100.00'), 
                DiscountType.PERCENT, 
                Decimal('101')
            )
        
        # Test negative discount value
        with self.assertRaises(ValueError):
            calculate_discount_amount(
                Decimal('100.00'), 
                DiscountType.FLAT, 
                Decimal('-10')
            )
    
    def test_calculate_tax_amount(self):
        # Test normal case
        self.assertEqual(
            calculate_tax_amount(Decimal('100.00'), Decimal('18')),
            Decimal('18.00')
        )
        
        # Test zero tax
        self.assertEqual(
            calculate_tax_amount(Decimal('100.00'), Decimal('0')),
            Decimal('0.00')
        )
        
        # Test negative taxable amount
        with self.assertRaises(ValueError):
            calculate_tax_amount(Decimal('-100.00'), Decimal('18'))
        
        # Test negative tax percentage
        with self.assertRaises(ValueError):
            calculate_tax_amount(Decimal('100.00'), Decimal('-18'))
    
    def test_calculate_order_totals(self):
        # Test normal case
        items = [
            {"qty": 2, "unit_price": Decimal('10.00'), "unit_cost": Decimal('6.00')},
            {"qty": 1, "unit_price": Decimal('15.00'), "unit_cost": Decimal('8.00')}
        ]
        
        result = calculate_order_totals(
            items=items,
            discount_type=DiscountType.FLAT,
            discount_value=Decimal('5.00'),
            tax_percent=Decimal('10'),
            other_costs=Decimal('2.00')
        )
        
        # Expected calculations:
        # Subtotal: (2 * 10.00) + (1 * 15.00) = 35.00
        # Total making cost: (2 * 6.00) + (1 * 8.00) = 20.00
        # Discount amount: 5.00 (flat)
        # Taxable amount: 35.00 - 5.00 = 30.00
        # Tax amount: 30.00 * 10% = 3.00
        # Total amount: 30.00 + 3.00 = 33.00
        # Net amount: 33.00 - 20.00 = 13.00
        # Total profit: 13.00 - 2.00 = 11.00
        
        self.assertEqual(result["subtotal"], Decimal('35.00'))
        self.assertEqual(result["discount_amount"], Decimal('5.00'))
        self.assertEqual(result["taxable_amount"], Decimal('30.00'))
        self.assertEqual(result["tax_amount"], Decimal('3.00'))
        self.assertEqual(result["total_amount"], Decimal('33.00'))
        self.assertEqual(result["total_making_cost"], Decimal('20.00'))
        self.assertEqual(result["other_costs"], Decimal('2.00'))
        self.assertEqual(result["net_amount"], Decimal('13.00'))
        self.assertEqual(result["total_profit"], Decimal('11.00'))
    
    def test_calculate_order_totals_percentage_discount(self):
        # Test with percentage discount
        items = [
            {"qty": 2, "unit_price": Decimal('10.00'), "unit_cost": Decimal('6.00')},
            {"qty": 1, "unit_price": Decimal('15.00'), "unit_cost": Decimal('8.00')}
        ]
        
        result = calculate_order_totals(
            items=items,
            discount_type=DiscountType.PERCENT,
            discount_value=Decimal('20'),
            tax_percent=Decimal('10'),
            other_costs=Decimal('0')
        )
        
        # Expected calculations:
        # Subtotal: (2 * 10.00) + (1 * 15.00) = 35.00
        # Discount amount: 35.00 * 20% = 7.00
        # Taxable amount: 35.00 - 7.00 = 28.00
        # Tax amount: 28.00 * 10% = 2.80
        # Total amount: 28.00 + 2.80 = 30.80
        
        self.assertEqual(result["subtotal"], Decimal('35.00'))
        self.assertEqual(result["discount_amount"], Decimal('7.00'))
        self.assertEqual(result["taxable_amount"], Decimal('28.00'))
        self.assertEqual(result["tax_amount"], Decimal('2.80'))
        self.assertEqual(result["total_amount"], Decimal('30.80'))
    
    def test_calculate_order_totals_empty_items(self):
        # Test with empty items list
        with self.assertRaises(ValueError):
            calculate_order_totals(items=[])
    
    def test_calculate_order_totals_zero_quantity(self):
        # Test with zero quantity
        items = [
            {"qty": 0, "unit_price": Decimal('10.00'), "unit_cost": Decimal('6.00')}
        ]
        
        with self.assertRaises(ValueError):
            calculate_order_totals(items=items)
    
    def test_calculate_order_totals_100_percent_discount(self):
        # Test with 100% discount
        items = [
            {"qty": 2, "unit_price": Decimal('10.00'), "unit_cost": Decimal('6.00')}
        ]
        
        result = calculate_order_totals(
            items=items,
            discount_type=DiscountType.PERCENT,
            discount_value=Decimal('100'),
            tax_percent=Decimal('10')
        )
        
        # Expected calculations:
        # Subtotal: 2 * 10.00 = 20.00
        # Discount amount: 20.00 * 100% = 20.00
        # Taxable amount: 20.00 - 20.00 = 0.00
        # Tax amount: 0.00 * 10% = 0.00
        # Total amount: 0.00 + 0.00 = 0.00
        
        self.assertEqual(result["subtotal"], Decimal('20.00'))
        self.assertEqual(result["discount_amount"], Decimal('20.00'))
        self.assertEqual(result["taxable_amount"], Decimal('0.00'))
        self.assertEqual(result["tax_amount"], Decimal('0.00'))
        self.assertEqual(result["total_amount"], Decimal('0.00'))
    
    def test_calculate_order_totals_round_to_integer(self):
        # Test with rounding to nearest integer
        items = [
            {"qty": 1, "unit_price": Decimal('10.50'), "unit_cost": Decimal('6.00')}
        ]
        
        result = calculate_order_totals(
            items=items,
            round_to_integer=True
        )
        
        # Expected calculations:
        # Subtotal: 1 * 10.50 = 10.50
        # Total amount (rounded): 11.00
        
        self.assertEqual(result["subtotal"], Decimal('10.50'))
        self.assertEqual(result["total_amount"], Decimal('11'))
    
    def test_calculate_order_totals_negative_discount(self):
        # Test with negative discount value
        items = [
            {"qty": 1, "unit_price": Decimal('10.00'), "unit_cost": Decimal('6.00')}
        ]
        
        with self.assertRaises(ValueError):
            calculate_order_totals(
                items=items,
                discount_type=DiscountType.FLAT,
                discount_value=Decimal('-5.00')
            )


if __name__ == "__main__":
    unittest.main()

