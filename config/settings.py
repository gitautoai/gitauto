from config import STRIPE_PRODUCT_ID_FREE, STRIPE_PRODUCT_ID_STANDARD


SETTINGS = {
    "free": {
        "name": "Free",
        "check_run": False,
        "product_id": STRIPE_PRODUCT_ID_FREE,
    },
    "standard": {
        "name": "Standard",
        "check_run": True,
        "product_id": STRIPE_PRODUCT_ID_STANDARD,
    },
}
