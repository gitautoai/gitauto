import pytest
from services.stripe.customer import Customer

def test_customer_initialization():
    assert Customer() is not None
