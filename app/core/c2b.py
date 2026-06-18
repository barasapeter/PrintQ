from requests.auth import HTTPBasicAuth
import base64
import json
import datetime
import platform
import traceback
import httpx

from app.core.phone import process_phone as normalize_phone_number
from app.core.config import settings


class MpesaAPI:
    def __init__(
        self, consumer_key, consumer_secret, business_shortcode, online_passkey
    ):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.business_shortcode = business_shortcode
        self.online_passkey = online_passkey

    async def get_mpesa_token(self):
        api_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                api_url, auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret)
            )

        if response.status_code == 200:
            return {
                "success": True,
                "detail": response.json(),
                "status_code": response.status_code,
                "token": response.json()["access_token"],
            }
        else:
            print("response::", response.text, response)
            return {
                "success": False,
                "detail": response.text
                or "Access token not granted. This is an error on our side, if it happens please report as soon as possible.",
                "status_code": response.status_code,
                "token": None,
            }

    def generate_password(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        data_to_encode = (
            f"{self.business_shortcode}{self.online_passkey}{timestamp}".encode("utf-8")
        )
        password = base64.b64encode(data_to_encode).decode("utf-8")
        return password, timestamp

    async def make_stk_push(self, phone, amount, callback_url):
        try:
            access_token = await self.get_mpesa_token()
            if access_token["success"]:
                password, timestamp = self.generate_password()

                headers = {
                    "Authorization": f"Bearer {access_token['token']}",
                    "Content-Type": "application/json",
                }

                request_body = {
                    "BusinessShortCode": self.business_shortcode,
                    "Password": password,
                    "Timestamp": timestamp,
                    "TransactionType": "CustomerBuyGoodsOnline",
                    "Amount": amount,
                    "PartyA": normalize_phone_number(phone),
                    "PartyB": 4858770,
                    "PhoneNumber": normalize_phone_number(phone),
                    "CallBackURL": callback_url,
                    "AccountReference": "UNIQUE_REFERENCE",
                    "TransactionDesc": "Payment for shit",
                }

                print("Phone number for STK PUSH:", normalize_phone_number(phone))

                api_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        api_url, json=request_body, headers=headers
                    )

                if response.status_code == 200:
                    print(f"Safaricom stk prompt: OK, RESPONSE:: {response}")
                    print(f"RESPONSE.TEXT:\n{response.text}")
                    return {
                        "success": True,
                        "detail": json.loads(
                            response.text
                        ),  # can safaricom return an empty response with 200 status code?? BUG RENDEZVOUS #1
                        "status_code": response.status_code,
                    }
                else:
                    return {
                        "success": False,
                        "detail": json.loads(response.text),
                        "status_code": response.status_code,
                    }
            else:
                return access_token

        except Exception as e:
            return {
                "success": False,
                "detail": str(e),
                "trace": traceback.format_exc(),
                "status_code": 500,
            }


async def utils_initiate_stk_push(phone, amount, callback_url):
    consumer_key = settings.c2b_consumer_key
    consumer_secret = settings.c2b_consumer_secret
    business_shortcode = settings.c2b_shortcode
    online_passkey = settings.c2b_online_passkey
    print("Passed callback", callback_url)
    if platform.system() == "Windows":
        callback_url = "https://mucra.pythonanywhere.com"
    print("Final callback", callback_url)
    mpesa_api = MpesaAPI(
        consumer_key, consumer_secret, business_shortcode, online_passkey
    )

    response = await mpesa_api.make_stk_push(phone, amount, callback_url)
    return response


if __name__ == "__main__":
    phone_number = "254114068425"
    amount_to_pay = "50"
    response = utils_initiate_stk_push(
        phone_number, amount_to_pay, "htps://mucra.pythonanywhere.com"
    )
    print(response)
