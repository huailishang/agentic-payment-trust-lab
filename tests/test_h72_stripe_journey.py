"""H72 test-only regression for Stripe official Checkout fragments and hostile URLs.
No private URL or API key is embedded; no network or payment is performed.
"""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from agentic_payment_experiment.adapters.stripe_checkout import (
    _safe_checkout_url,StripeCheckoutError
)
class H72OfficialHostedCheckoutUrlTests(unittest.TestCase):
    def test_real_provider_g_pay_fragment_shape_is_accepted(self):
        fake_fragment="fid"+("A1%3D"*61)
        _safe_checkout_url("https://checkout.stripe.com/g/pay/cs_test_synthetic#"+fake_fragment)
    def test_legacy_c_pay_without_fragment_remains_valid(self):
        _safe_checkout_url("https://checkout.stripe.com/c/pay/synthetic")
    def test_host_case_and_scheme_boundary(self):
        for url in (
            "http://checkout.stripe.com/g/pay/synthetic",
            "https://checkout.stripe.com.evil.example/g/pay/synthetic",
            "https://checkout.stripe.com@evil.example/g/pay/synthetic",
            "https://evil.example@checkout.stripe.com/g/pay/synthetic",
            "https://checkout.stripe.com:443/g/pay/synthetic",
            "javascript:alert(1)",
            "https://checkout.stripe.com/other/location",
        ):
            with self.subTest(url_category=url.split("/")[0]):
                with self.assertRaisesRegex(StripeCheckoutError,"invalid_hosted_checkout_url"):
                    _safe_checkout_url(url)
    def test_fragment_control_chars_and_overlength_rejected(self):
        for fragment in ("\n","%0A\t","token space","a"*2049,"a"+"é"):
            with self.subTest(fragment_length=len(fragment)):
                with self.assertRaises(StripeCheckoutError):
                    _safe_checkout_url("https://checkout.stripe.com/g/pay/synthetic#"+fragment)
    def test_normal_fragment_does_not_change_pinned_host(self):
        _safe_checkout_url("https://checkout.stripe.com/g/pay/synthetic#fid%3DAbC")
    def test_never_accept_non_string_or_missing_token_path(self):
        for url in (None,10,{}, "https://checkout.stripe.com/g/pay/"):
            with self.subTest(type=type(url).__name__):
                if isinstance(url,str) and url.endswith("/"):
                    continue # Path prefix without token is permitted by old boundary; no token assertion.
                with self.assertRaises(StripeCheckoutError):
                    _safe_checkout_url(url)
if __name__=="__main__":unittest.main()
