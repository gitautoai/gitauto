import stripe
from config import STRIPE_API_KEY

stripe.api_key = STRIPE_API_KEY
# Export the configured stripe module for use by other services
__all__ = ['stripe', 'STRIPE_API_KEY']

