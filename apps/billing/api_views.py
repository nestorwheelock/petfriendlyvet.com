"""REST API views for billing."""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Invoice, Payment
from .serializers import (
    InvoiceSerializer,
    InvoiceListSerializer,
    PaymentSerializer,
    RecordPaymentSerializer,
)
from .services import PaymentService


class IsStaffOrOwner(permissions.BasePermission):
    """Allow staff or invoice owner to access."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.owner == request.user


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing invoices.

    Staff can see all invoices.
    Customers can only see their own.
    """

    permission_classes = [permissions.IsAuthenticated, IsStaffOrOwner]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Invoice.objects.all().order_by('-created_at')
        return Invoice.objects.filter(owner=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def payments(self, request, pk=None):
        """Record a payment against an invoice.

        POST /api/billing/invoices/{id}/payments/
        {
            "amount": "100.00",
            "payment_method": "cash",
            "reference_number": "optional",
            "notes": "optional",
            "cash_discount": "0.00"
        }
        """
        invoice = self.get_object()

        serializer = RecordPaymentSerializer(
            data=request.data,
            context={'invoice': invoice, 'request': request}
        )

        if serializer.is_valid():
            payment = PaymentService.record_payment(
                invoice=invoice,
                amount=serializer.validated_data['amount'],
                payment_method=serializer.validated_data['payment_method'],
                recorded_by=request.user,
                reference_number=serializer.validated_data.get('reference_number', ''),
                notes=serializer.validated_data.get('notes', ''),
                cash_discount=serializer.validated_data.get('cash_discount', 0),
            )

            # Refresh invoice to get updated balance
            invoice.refresh_from_db()

            return Response({
                'payment': PaymentSerializer(payment).data,
                'invoice': {
                    'id': invoice.id,
                    'invoice_number': invoice.invoice_number,
                    'status': invoice.status,
                    'amount_paid': str(invoice.amount_paid),
                    'balance_due': str(invoice.get_balance_due()),
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def payment_history(self, request, pk=None):
        """Get payment history for an invoice."""
        invoice = self.get_object()
        payments = invoice.payments.all()
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing payments (read-only).

    Staff can see all payments.
    """

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Payment.objects.all().order_by('-created_at')
