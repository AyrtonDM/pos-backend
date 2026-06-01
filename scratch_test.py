import json
import stripe
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import SessionLocal
from app.services.pago_service import PagoService
import traceback

payload_str = """{
  "id": "evt_1TdXzoHftUtrXixN8CJhEy6r",
  "object": "event",
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_test_a1JOjtcwyr35OABTapsOck7thO7LB4YQs5GQWcZftYTTY7uqDknWrNMN04",
      "object": "checkout.session",
      "metadata": {
        "id_usuario": "1",
        "id_empresa": "1",
        "id_plan": "2"
      },
      "payment_intent": "pi_3TdXznHftUtrXixN1dlDf2Jn",
      "payment_status": "paid"
    }
  }
}"""

event = stripe.Event.construct_from(json.loads(payload_str), stripe.api_key)
data_object = event.data.object

db = SessionLocal()
try:
    PagoService._webhook_checkout_completado(db, data_object)
    print("Éxito!")
except Exception as e:
    print("ERROR:")
    traceback.print_exc()
finally:
    db.close()
