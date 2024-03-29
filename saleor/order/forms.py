from django import forms
from django.utils.functional import lazy
from django.utils.translation import pgettext_lazy

from ..account.forms import SignupForm
from ..payment import gateway
from ..payment.models import Payment
from . import events
from .models import Order, OrderImage


class OrderImageForm(forms.ModelForm):

    class Meta:
        model = OrderImage
        exclude = ("order", "sort_order" , "Description")
        labels = {
            "image": pgettext_lazy("Order image", "Image"),
            "alt": pgettext_lazy("Description", "Description"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.image:
            self.fields["image"].widget = ImagePreviewWidget()

    def save(self, commit=True):
        image = super().save(commit=commit)
        # create_product_thumbnails.delay(image.pk)
        return image


def get_gateways():
    gateways = [
        (gtw["name"], gtw["name"].capitalize() + " gateway")
        for gtw in gateway.list_gateways()
    ]
    return gateways


class PaymentsForm(forms.Form):
    gateway = forms.ChoiceField(
        label=pgettext_lazy("Payments form label", "Payment Method"),
        choices=lazy(get_gateways, tuple),
        widget=forms.RadioSelect,
    )


class PaymentDeleteForm(forms.Form):
    payment_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop("order")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        payment_id = cleaned_data.get("payment_id")
        payment = Payment.objects.filter(is_active=True, id=payment_id).first()
        if not payment:
            self._errors["number"] = self.error_class(
                [pgettext_lazy("Payment delete form error", "Payment does not exist")]
            )
        elif not payment.can_void():
            self._errors["number"] = self.error_class(
                [
                    pgettext_lazy(
                        "Payment delete form error", "Payment cannot be cancelled."
                    )
                ]
            )
        else:
            cleaned_data["payment"] = payment
        return cleaned_data

    def save(self):
        payment = self.cleaned_data["payment"]
        gateway.void(payment)


class PasswordForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget = forms.HiddenInput()


class CustomerNoteForm(forms.ModelForm):
    customer_note = forms.CharField(
        max_length=250,
        required=False,
        strip=True,
        label=False,
        widget=forms.Textarea({"rows": 3}),
    )

    class Meta:
        model = Order
        fields = ["customer_note"]

    def save(self, *, user, commit=True):
        events.order_note_added_event(
            order=self.instance, user=user, message=self.instance.customer_note
        )
        return super().save(commit)
