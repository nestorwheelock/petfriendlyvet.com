"""Serializers for billing API."""
from decimal import Decimal

from rest_framework import serializers

from .models import Invoice, InvoiceLineItem, Payment


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    """Serializer for invoice line items."""

    class Meta:
        model = InvoiceLineItem
        fields = [
            'id', 'description', 'quantity', 'unit_price',
            'discount_percent', 'line_total'
        ]
        read_only_fields = ['id', 'line_total']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payment records."""

    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True
    )
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'payment_method', 'payment_method_display',
            'reference_number', 'notes', 'cash_discount_applied',
            'recorded_by', 'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'created_at']

    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.get_full_name() or obj.recorded_by.username
        return None


class RecordPaymentSerializer(serializers.Serializer):
    """Serializer for recording a new payment."""

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_METHODS)
    reference_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    cash_discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal('0')
    )

    def validate_amount(self, value):
        """Validate payment amount doesn't exceed balance."""
        invoice = self.context.get('invoice')
        if invoice:
            balance = invoice.get_balance_due()
            if value > balance:
                raise serializers.ValidationError(
                    f"Payment amount ({value}) exceeds balance due ({balance})"
                )
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for invoices."""

    items = InvoiceLineItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    owner_name = serializers.SerializerMethodField()
    pet_name = serializers.SerializerMethodField()
    balance_due = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'owner', 'owner_name', 'pet', 'pet_name',
            'subtotal', 'discount_amount', 'tax_amount', 'total',
            'amount_paid', 'balance_due', 'status', 'status_display',
            'due_date', 'created_at', 'paid_at',
            'order', 'appointment', 'items', 'payments'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'created_at', 'paid_at', 'amount_paid'
        ]

    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username

    def get_pet_name(self, obj):
        return obj.pet.name if obj.pet else None

    def get_balance_due(self, obj):
        return str(obj.get_balance_due())


class InvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for invoice lists."""

    owner_name = serializers.SerializerMethodField()
    balance_due = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'owner_name', 'total',
            'amount_paid', 'balance_due', 'status', 'status_display',
            'due_date', 'created_at'
        ]

    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username

    def get_balance_due(self, obj):
        return str(obj.get_balance_due())
