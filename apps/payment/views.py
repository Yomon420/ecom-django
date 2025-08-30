# apps/payment/views.py
import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Payment
from apps.orders.models import Order
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import PaymentIntentSerializer, PaymentSerializer

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"⚠️ Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"⚠️ Invalid signature: {str(e)}")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"⚠️ Webhook error: {str(e)}")
        return HttpResponse(status=400)

    logger.info(f"✅ Webhook received: {event['type']}")

    # Handle event
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        
        # Safely get order_id from metadata
        order_id = intent["metadata"].get("order_id")
        
        if not order_id:
            logger.error(f"⚠️ PaymentIntent {intent['id']} has no order_id in metadata")
            return HttpResponse(status=400)
        
        try:
            logger.info(f"💰 Payment succeeded for order {order_id}")
            order = Order.objects.get(id=order_id)
            
            # Get or create payment record
            payment, created = Payment.objects.get_or_create(
                stripe_payment_intent_id=intent["id"],
                defaults={
                    'order': order,
                    'amount': intent["amount"] / 100,  # Convert from cents
                    'status': "succeeded"
                }
            )
            
            if not created:
                payment.status = "succeeded"
                payment.save()

            order.status = "paid"
            order.save()
            
            logger.info(f"✅ Order {order_id} marked as paid")
            
        except Order.DoesNotExist:
            logger.error(f"⚠️ Order {order_id} not found for PaymentIntent {intent['id']}")
            return HttpResponse(status=404)
        except Exception as e:
            logger.error(f"⚠️ Error processing webhook: {str(e)}")
            return HttpResponse(status=500)

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        order_id = intent["metadata"].get("order_id")
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.status = "payment_failed"
                order.save()
                
                # Update payment record if it exists
                Payment.objects.filter(stripe_payment_intent_id=intent["id"]).update(
                    status="failed"
                )
                
                logger.info(f"❌ Payment failed for order {order_id}")
                
            except Order.DoesNotExist:
                logger.error(f"Order {order_id} not found for failed payment")

    return HttpResponse(status=200)