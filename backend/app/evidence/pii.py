import re
from typing import Tuple

class PIIMasker:
    """
    Deterministic PII Redaction Engine.
    Masks emails, phone numbers, customer names, card numbers, and IP addresses
    BEFORE text is passed to embedding or indexed in the vector store.
    """

    # Precompiled regular expressions
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
    PHONE_PATTERN = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
    CARD_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
    IP_PATTERN = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
    
    # Common name patterns in support/customer logs (e.g., "Customer John Smith", "User Alice Baker", "Buyer Robert")
    NAME_PATTERNS = [
        re.compile(r'\b(Customer|User|Buyer|Client|Shopper)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'),
        re.compile(r'\b(Account holder)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'),
    ]

    @classmethod
    def mask_text(cls, text: str) -> str:
        """
        Applies all deterministic PII masking rules to the input text.
        """
        if not text:
            return ""

        masked = text

        # 1. Mask Email addresses
        masked = cls.EMAIL_PATTERN.sub("[EMAIL_REDACTED]", masked)

        # 2. Mask Phone numbers
        masked = cls.PHONE_PATTERN.sub("[PHONE_REDACTED]", masked)

        # 3. Mask Credit Card / Payment account numbers
        masked = cls.CARD_PATTERN.sub("[CARD_REDACTED]", masked)

        # 4. Mask IP addresses
        masked = cls.IP_PATTERN.sub("[IP_REDACTED]", masked)

        # 5. Mask Identified Customer Names
        for pattern in cls.NAME_PATTERNS:
            masked = pattern.sub(r"\1 [NAME_REDACTED]", masked)

        return masked

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """
        Validation helper to check if unmasked PII exists in text.
        """
        if not text:
            return False
        if cls.EMAIL_PATTERN.search(text):
            return True
        if cls.PHONE_PATTERN.search(text):
            return True
        if cls.CARD_PATTERN.search(text):
            return True
        return False

pii_masker = PIIMasker()
