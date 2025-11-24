# goals/forms.py
from datetime import date

from django import forms
from .models import Goal


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['type', 'target_value', 'deadline', 'note']
    # label & widget giống cũ
        labels = {
            'type': 'Loại mục tiêu',
            'target_value': 'Cân nặng mục tiêu (kg)',
            'deadline': 'Hạn hoàn thành',
            'note': 'Ghi chú',
        }
        widgets = {
            'deadline': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].widget.attrs.update({'class': 'form-select'})
        self.fields['target_value'].widget.attrs.update({'class': 'form-control'})

    def clean_deadline(self):
        """Không cho chọn hạn < hôm nay (tránh case bạn đang gặp)."""
        d = self.cleaned_data.get('deadline')
        if not d:
            return d
        if d < date.today():
            raise forms.ValidationError("Hạn không được nhỏ hơn ngày hôm nay.")
        return d
