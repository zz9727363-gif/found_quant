import unittest
from decimal import Decimal

from ndx_price import calculate_investment_amount, calculate_ma250_metrics


class InvestmentModelTests(unittest.TestCase):
    def test_positive_deviation_reduces_amount_smoothly(self):
        multiplier, amount, warning = calculate_investment_amount(Decimal("10"))
        self.assertEqual(multiplier, Decimal("0.8"))
        self.assertEqual(amount, Decimal("8.00"))
        self.assertIsNone(warning)

    def test_negative_deviation_increases_amount_smoothly(self):
        multiplier, amount, warning = calculate_investment_amount(Decimal("-20"))
        self.assertEqual(multiplier, Decimal("1.4"))
        self.assertEqual(amount, Decimal("14.00"))
        self.assertIsNone(warning)

    def test_amount_is_clamped_to_zero_and_high_warning_is_strict(self):
        multiplier, amount, warning = calculate_investment_amount(Decimal("60"))
        self.assertEqual(multiplier, Decimal("-0.2"))
        self.assertEqual(amount, Decimal("0.00"))
        self.assertEqual(warning, "极度高估警告")
        self.assertIsNone(calculate_investment_amount(Decimal("30"))[2])

    def test_amount_is_capped_at_forty_and_low_warning_is_strict(self):
        multiplier, amount, warning = calculate_investment_amount(Decimal("-200"))
        self.assertEqual(multiplier, Decimal("5"))
        self.assertEqual(amount, Decimal("40.00"))
        self.assertEqual(warning, "极度低估警告")
        self.assertIsNone(calculate_investment_amount(Decimal("-30"))[2])

    def test_ma250_uses_latest_250_valid_closes(self):
        closes = [Decimal(str(value)) for value in range(1, 252)]
        latest, ma250, deviation = calculate_ma250_metrics(closes)
        self.assertEqual(latest, Decimal("251"))
        self.assertEqual(ma250, Decimal("126.5"))
        self.assertEqual(deviation, (Decimal("251") / Decimal("126.5") - 1) * 100)

    def test_ma250_rejects_fewer_than_250_closes(self):
        with self.assertRaisesRegex(ValueError, "250"):
            calculate_ma250_metrics([Decimal("1")] * 249)


if __name__ == "__main__":
    unittest.main()
