"""App-level pytest config for the transactions app.

Add transactions-specific fixtures here as needed. Project-level fixtures in
`src/conftest.py` will be available automatically.
"""

import pytest
from transactions.models import UserAccountTransaction, TransactionType

__all__ = ["pytest"]


@pytest.fixture
def transaction(db, admin_user):
    """Create and return a UserAccountTransaction instance."""
    return UserAccountTransaction.objects.create(
        user_account=admin_user,
        amount=100.00,
        transaction_type=TransactionType.DEPOSIT,
        notes="Test transaction"
    )
