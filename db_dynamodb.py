# db_dynamodb.py
import boto3
from datetime import datetime
from .addon import AddonStorage
from decimal import Decimal
from uuid import uuid4
REGION = "eu-north-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)

TABLE_MEASUREMENTS = "BreastMeasurements"
TABLE_PENDING = "PendingMeasurements"


def send_to_dynamodb(height, w_left, w_right, band, bust, volume, h_type, v_type):
    email = AddonStorage.get("USER_EMAIL") or f"anonymous_{uuid4().hex[:8]}"
    timestamp = datetime.now().isoformat()

    item = {
        "email": email,
        "timestamp": timestamp,
        "height_cm": Decimal(str(height)),
        "width_left_cm": Decimal(str(w_left)),
        "width_right_cm": Decimal(str(w_right)),
        "band_circumference_cm": Decimal(str(band)),
        "bust_circumference_cm": Decimal(str(bust)),
        "volume_cm3": Decimal(str(volume)),
        "horizontal_type": h_type,
        "vertical_type": v_type
    }

    try:
        table = dynamodb.Table(TABLE_MEASUREMENTS)
        table.put_item(Item=item)
        print(f"✅ Mesure envoyée à DynamoDB (utilisateur : {email})")
    except Exception as e:
        print("❌ Erreur DynamoDB:", e)


