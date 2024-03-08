import os
import json
import requests
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import ValidationError

from apps.accounts.serializers import UserSerializer

MERCURY_CLOUD_PRO_ID = 839780
MERCURY_CLOUD_BUSINESS_ID = 839783

PADDLE_VENDOR_ID = os.environ.get("PADDLE_VENDOR_ID")
PADDLE_API_KEY = os.environ.get("PADDLE_API_KEY")


class SubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def check_subscription(self, request):
        checkout_id = request.data.get("checkoutId")
        if checkout_id is None:
            raise ValidationError("Missing checkout id")

        url = f"https://checkout.paddle.com/api/1.0/order?checkout_id={checkout_id}"
        print(url)
        response = requests.get(url, timeout=15)
        user = request.user
        if response.status_code != 200:
            user.profile.info = json.dumps(
                {
                    "plan": "starter",
                    "status": "error",
                    "error": "Problem with subscription check",
                }
            )
            user.profile.save()
            raise ValidationError("Cant receive data from paddle")

        data = response.json()
        subscription_id = data.get("order", {}).get("subscription_id")
        receipt_url = data.get("order", {}).get("receipt_url")
        product_id = data.get("order", {}).get("product_id")

        print(data)

        if subscription_id is None:
            user.profile.info = json.dumps(
                {
                    "plan": "starter",
                    "status": "error",
                    "error": "Problem with subscription check, empty Paddle reponse",
                }
            )
        else:
            user.profile.info = json.dumps(
                {
                    "plan": "business"
                    if product_id == MERCURY_CLOUD_BUSINESS_ID
                    else "pro",
                    "status": "active",
                    "error": "",
                    "subscription_id": subscription_id,
                    "receipt_url": receipt_url,
                    "product_id": product_id,
                }
            )
        user.profile.save()

    def is_active(self, request):
        user = request.user
        user_data = json.loads(user.profile.info)

        plan = user_data.get("plan", "starter")

        if plan != "starter":
            if PADDLE_API_KEY is None or PADDLE_VENDOR_ID is None:
                raise ValidationError("Paddle not configured")

            url = "https://vendors.paddle.com/api/2.0/subscription/users"

            subscription_id = user_data.get("subscription_id")
            if subscription_id is None:
                raise ValidationError("Missing user subscription information")

            data = {
                "vendor_id": PADDLE_VENDOR_ID,
                "vendor_auth_code": PADDLE_API_KEY,
                "subscription_id": subscription_id,
                "state": "active",
            }
            response = requests.post(url, data=data, timeout=15)
            if response.status_code != 200:
                raise ValidationError("Error when get information from Paddle")

            success = response.json().get("success", False)
            data = response.json().get("response", [])

            if not success or len(data) == 0:
                user_data["plan"] = "starter"
                user_data["status"] = "not_active"

            else:
                user_data["cancel_url"] = data[0].get("cancel_url", "")
                user_data["status"] = "active"

            user.profile.info = json.dumps(user_data)
            user.profile.save()

    def post(self, request, format=None):
        action = request.data.get("action")

        if action == "check":
            self.check_subscription(request)
            self.is_active(request)
        elif action == "is_active":
            self.is_active(request)

        user = request.user

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
