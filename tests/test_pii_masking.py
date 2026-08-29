import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.evidence.pii import pii_masker

class TestPIIMasking:

    def test_email_masking(self):
        text = "Customer reported an issue, contact at user.name@domain.com for follow-up."
        masked = pii_masker.mask_text(text)
        assert "user.name@domain.com" not in masked
        assert "[EMAIL_REDACTED]" in masked

    def test_phone_masking(self):
        text = "Customer called from +1 (555) 234-5678 regarding checkout failure."
        masked = pii_masker.mask_text(text)
        assert "555" not in masked or "234-5678" not in masked
        assert "[PHONE_REDACTED]" in masked

    def test_card_masking(self):
        text = "Payment failed on card 4111-2222-3333-4444 during 3DS challenge."
        masked = pii_masker.mask_text(text)
        assert "4111-2222-3333-4444" not in masked
        assert "[CARD_REDACTED]" in masked

    def test_name_masking(self):
        text = "Customer Johnathan Smith experienced a stockout on laptop SKU."
        masked = pii_masker.mask_text(text)
        assert "Johnathan Smith" not in masked
        assert "[NAME_REDACTED]" in masked

    def test_ip_masking(self):
        text = "Request originated from IP 192.168.1.105 on port 443."
        masked = pii_masker.mask_text(text)
        assert "192.168.1.105" not in masked
        assert "[IP_REDACTED]" in masked

    def test_pii_check_helper(self):
        raw_text = "Call me at 555-123-4567 or email admin@novamart.com"
        assert pii_masker.contains_pii(raw_text) is True
        
        masked = pii_masker.mask_text(raw_text)
        assert pii_masker.contains_pii(masked) is False
