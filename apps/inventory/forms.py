"""Inventory management forms for staff portal (S-024).

Forms for:
- Stock movements (receive, sale, adjustment, transfer)
- Purchase orders (create, edit)
- Stock counts (create, entry)
- Stock transfers
"""
from decimal import Decimal

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.inventory.models import (
    LocationType, StockLocation, StockLevel, StockBatch, StockMovement,
    Supplier, PurchaseOrder, PurchaseOrderLine, StockCount, StockCountLine,
    ReorderRule, ProductSupplier
)
from apps.store.models import Product


# Movement types that are inbound (increase stock)
INBOUND_MOVEMENT_TYPES = ['receive', 'return_customer', 'transfer_in', 'adjustment_add']

# Movement types that are outbound (decrease stock)
OUTBOUND_MOVEMENT_TYPES = [
    'sale', 'dispense', 'return_supplier', 'transfer_out',
    'adjustment_remove', 'expired', 'damaged', 'loss', 'sample'
]


class StockMovementForm(forms.ModelForm):
    """Form for recording stock movements."""

    class Meta:
        model = StockMovement
        fields = [
            'movement_type', 'product', 'batch', 'from_location',
            'to_location', 'quantity', 'reason'
        ]
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 2}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'batch': forms.Select(attrs={'class': 'form-select'}),
            'from_location': forms.Select(attrs={'class': 'form-select'}),
            'to_location': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch'].required = False
        self.fields['from_location'].required = False
        self.fields['to_location'].required = False
        self.fields['reason'].required = False

    def clean_quantity(self):
        """Ensure quantity is positive."""
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError(_('Quantity must be greater than zero.'))
        return quantity

    def clean(self):
        """Validate movement type and location requirements."""
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        from_location = cleaned_data.get('from_location')
        to_location = cleaned_data.get('to_location')

        if movement_type in INBOUND_MOVEMENT_TYPES:
            if not to_location:
                self.add_error('to_location', _('Inbound movements require a destination location.'))

        if movement_type in OUTBOUND_MOVEMENT_TYPES:
            if not from_location:
                self.add_error('from_location', _('Outbound movements require a source location.'))

        return cleaned_data


class PurchaseOrderForm(forms.ModelForm):
    """Form for creating/editing purchase orders."""

    class Meta:
        model = PurchaseOrder
        fields = [
            'supplier', 'expected_date', 'delivery_location',
            'shipping_address', 'notes'
        ]
        widgets = {
            'expected_date': forms.DateInput(attrs={'type': 'date'}),
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shipping_address'].required = False
        self.fields['notes'].required = False

    def save(self, commit=True):
        """Auto-generate PO number if not set."""
        instance = super().save(commit=False)
        if not instance.po_number:
            from apps.inventory.services import generate_po_number
            instance.po_number = generate_po_number()
        if commit:
            instance.save()
        return instance


class PurchaseOrderLineForm(forms.ModelForm):
    """Form for purchase order line items."""

    class Meta:
        model = PurchaseOrderLine
        fields = ['product', 'quantity_ordered', 'unit_cost', 'supplier_sku', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 1}),
        }

    def clean_quantity_ordered(self):
        """Ensure quantity is positive."""
        qty = self.cleaned_data.get('quantity_ordered')
        if qty is not None and qty <= 0:
            raise forms.ValidationError(_('Quantity must be greater than zero.'))
        return qty

    def save(self, commit=True):
        """Calculate line total."""
        instance = super().save(commit=False)
        instance.line_total = instance.quantity_ordered * instance.unit_cost
        if commit:
            instance.save()
        return instance


class PurchaseOrderReceiveForm(forms.Form):
    """Form for receiving items against a PO line."""

    quantity_received = forms.DecimalField(
        label=_('Quantity Received'),
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    batch_number = forms.CharField(
        label=_('Batch Number'),
        max_length=100
    )
    lot_number = forms.CharField(
        label=_('Lot Number'),
        max_length=100,
        required=False
    )
    expiry_date = forms.DateField(
        label=_('Expiry Date'),
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )

    def clean_quantity_received(self):
        """Ensure quantity is positive."""
        qty = self.cleaned_data.get('quantity_received')
        if qty is not None and qty <= 0:
            raise forms.ValidationError(_('Quantity must be greater than zero.'))
        return qty


class StockCountForm(forms.ModelForm):
    """Form for starting a stock count."""

    class Meta:
        model = StockCount
        fields = ['location', 'count_type', 'count_date', 'notes']
        widgets = {
            'count_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False
        if not self.instance.pk:
            self.fields['count_date'].initial = timezone.now().date()


class StockCountLineForm(forms.ModelForm):
    """Form for entering count quantities."""

    class Meta:
        model = StockCountLine
        fields = ['counted_quantity', 'adjustment_reason']
        widgets = {
            'adjustment_reason': forms.Textarea(attrs={'rows': 1}),
        }

    def clean_counted_quantity(self):
        """Ensure counted quantity is non-negative."""
        qty = self.cleaned_data.get('counted_quantity')
        if qty is not None and qty < 0:
            raise forms.ValidationError(_('Counted quantity cannot be negative.'))
        return qty


class SupplierForm(forms.ModelForm):
    """Form for creating/editing suppliers."""

    class Meta:
        model = Supplier
        fields = [
            'name', 'code', 'contact_name', 'email', 'phone',
            'address', 'payment_terms', 'lead_time_days', 'is_active'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['contact_name'].required = False
        self.fields['email'].required = False
        self.fields['phone'].required = False
        self.fields['address'].required = False
        self.fields['payment_terms'].required = False
        self.fields['lead_time_days'].required = False


class LocationTypeForm(forms.ModelForm):
    """Form for creating/editing location types."""

    class Meta:
        model = LocationType
        fields = [
            'name', 'code', 'description',
            'requires_temperature_control', 'requires_restricted_access', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        # Make code readonly when editing existing type
        if self.instance.pk:
            self.fields['code'].widget.attrs['readonly'] = True


class StockLocationForm(forms.ModelForm):
    """Form for creating/editing stock locations."""

    class Meta:
        model = StockLocation
        fields = [
            'name', 'location_type', 'description',
            'requires_temperature_control', 'requires_restricted_access', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['location_type'].queryset = LocationType.objects.filter(is_active=True)


class StockTransferForm(forms.Form):
    """Form for quick stock transfers between locations."""

    product = forms.ModelChoiceField(
        label=_('Product'),
        queryset=Product.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    batch = forms.ModelChoiceField(
        label=_('Batch'),
        queryset=StockBatch.objects.filter(status='available'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    from_location = forms.ModelChoiceField(
        label=_('From Location'),
        queryset=StockLocation.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    to_location = forms.ModelChoiceField(
        label=_('To Location'),
        queryset=StockLocation.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.DecimalField(
        label=_('Quantity'),
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    reason = forms.CharField(
        label=_('Reason'),
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False
    )

    def clean(self):
        """Validate transfer locations are different."""
        cleaned_data = super().clean()
        from_location = cleaned_data.get('from_location')
        to_location = cleaned_data.get('to_location')

        if from_location and to_location and from_location == to_location:
            raise forms.ValidationError(
                _('Source and destination locations must be different.')
            )

        return cleaned_data


class ReorderRuleForm(forms.ModelForm):
    """Form for creating/editing reorder rules."""

    class Meta:
        model = ReorderRule
        fields = [
            'product', 'location', 'min_level', 'reorder_point',
            'reorder_quantity', 'preferred_supplier', 'auto_create_po', 'is_active'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].required = False
        self.fields['preferred_supplier'].required = False
        self.fields['auto_create_po'].required = False


class ProductSupplierForm(forms.ModelForm):
    """Form for creating/editing product-supplier links."""

    class Meta:
        model = ProductSupplier
        fields = [
            'product', 'supplier', 'supplier_sku', 'unit_cost',
            'minimum_order_quantity', 'is_preferred', 'is_active'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier_sku'].required = False


class StockBatchForm(forms.ModelForm):
    """Form for creating/editing stock batches."""

    class Meta:
        model = StockBatch
        fields = [
            'product', 'location', 'batch_number', 'lot_number', 'serial_number',
            'initial_quantity', 'current_quantity', 'received_date', 'expiry_date',
            'unit_cost', 'status'
        ]
        widgets = {
            'received_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lot_number'].required = False
        self.fields['serial_number'].required = False
        self.fields['expiry_date'].required = False
        # unit_cost is required by model

    def clean(self):
        """Validate current quantity does not exceed initial quantity."""
        cleaned_data = super().clean()
        initial = cleaned_data.get('initial_quantity')
        current = cleaned_data.get('current_quantity')
        if initial is not None and current is not None and current > initial:
            self.add_error('current_quantity', _('Current quantity cannot exceed initial quantity.'))
        return cleaned_data


class StockLevelForm(forms.ModelForm):
    """Form for creating/editing stock levels."""

    class Meta:
        model = StockLevel
        fields = ['product', 'location', 'quantity', 'min_level', 'reorder_quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['min_level'].required = False
        self.fields['reorder_quantity'].required = False

    def clean_quantity(self):
        """Ensure quantity is non-negative."""
        qty = self.cleaned_data.get('quantity')
        if qty is not None and qty < 0:
            raise forms.ValidationError(_('Quantity cannot be negative.'))
        return qty


class StockLevelAdjustmentForm(forms.Form):
    """Form for adjusting stock level quantity."""

    adjustment = forms.DecimalField(
        label=_('Adjustment'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Positive to add, negative to subtract')
    )
    reason = forms.CharField(
        label=_('Reason'),
        widget=forms.Textarea(attrs={'rows': 2}),
        required=True
    )
