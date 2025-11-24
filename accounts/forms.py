# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Profile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Nhập email để khôi phục mật khẩu (khuyến nghị).",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    # Trang trí input cho đẹp (Bootstrap)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Tên đăng nhập"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Mật khẩu"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Nhập lại mật khẩu"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "").strip()
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "full_name",
            "age",
            "gender",
            "height_cm",
            "weight_kg",
            "activity_level",
        ]
        labels = {
            "full_name": "Họ tên",
            "age": "Tuổi",
            "gender": "Giới tính",
            "height_cm": "Chiều cao (cm)",
            "weight_kg": "Cân nặng (kg)",
            "activity_level": "Mức độ vận động",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nhập họ tên đầy đủ",
            }),
            "age": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 5,
                "max": 100,
            }),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "height_cm": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 50,
                "max": 250,
                "step": 0.1,
            }),
            "weight_kg": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 20,
                "max": 200,
                "step": 0.1,
            }),
            "activity_level": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned = super().clean()
        h = cleaned.get("height_cm") or 0
        w = cleaned.get("weight_kg") or 0
        if h <= 0 or w <= 0:
            raise forms.ValidationError("Chiều cao và cân nặng phải lớn hơn 0.")
        return cleaned


class PasswordResetRequestForm(forms.Form):
    identifier = forms.CharField(
        label="Tên đăng nhập hoặc Email",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập tên đăng nhập hoặc email"
            }
        )
    )

    def clean_identifier(self):
        value = self.cleaned_data["identifier"].strip()

        # Ưu tiên tìm theo username
        qs = User.objects.filter(username=value)

        # Nếu không có username trùng → tìm theo email
        if not qs.exists():
            qs = User.objects.filter(email=value)

        if not qs.exists():
            raise ValidationError("Không tìm thấy tài khoản nào khớp với thông tin này.")

        # Nếu có nhiều user chung email → lấy user đầu tiên
        user = qs.order_by("id").first()
        self.user = user
        return value


class PasswordResetVerifyForm(forms.Form):
    code = forms.CharField(
        label="Mã OTP",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập mã 6 số"
            }
        )
    )
    new_password1 = forms.CharField(
        label="Mật khẩu mới",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập mật khẩu mới"
            }
        )
    )
    new_password2 = forms.CharField(
        label="Nhập lại mật khẩu mới",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập lại mật khẩu mới"
            }
        )
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 != p2:
            raise ValidationError("Hai mật khẩu không khớp.")
        if p1 and len(p1) < 6:
            raise ValidationError("Mật khẩu phải có ít nhất 6 ký tự.")
        return cleaned