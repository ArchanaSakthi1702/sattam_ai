import razorpay
from app.config import get_settings

settings=get_settings()

client = razorpay.Client(
    auth=(
        settings.RAZOR_PAY_API_KEY,
        settings.RAZOR_PAY_API_SECRET,
    )
)
