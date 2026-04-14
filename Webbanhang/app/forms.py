from django import forms
from django.core.exceptions import ValidationError

from .models import Review


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """
    Django mặc định không hỗ trợ multiple cho ClearableFileInput.
    Field này nhận list file từ request.FILES.getlist().
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            'widget',
            MultipleFileInput(attrs={'multiple': True, 'class': 'form-control', 'accept': 'image/*', 'name': 'images', 'style': 'display:block !important;'})
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if data is None:
            return []
        if isinstance(data, (list, tuple)):
            files = data
        else:
            files = [data]
        cleaned_files = []
        for f in files:
            cleaned_files.append(super().clean(f, initial))
        return cleaned_files


class ReviewForm(forms.ModelForm):
    """
    Form đánh giá sản phẩm:
    - rating 1..5
    - nếu rating thấp thì yêu cầu comment dài hơn để tránh spam
    """

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Chia sẻ trải nghiệm của bạn...'}),
        }

    rating = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=5,
        error_messages={
            'required': 'Vui lòng chọn số sao.',
            'invalid': 'Vui lòng nhập số nguyên hợp lệ.',
            'min_value': 'Số sao phải từ 1 đến 5.',
            'max_value': 'Số sao phải từ 1 đến 5.',
        },
    )

    comment = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Chia sẻ trải nghiệm của bạn...'}),
        error_messages={
            'required': 'Vui lòng nhập nội dung đánh giá.',
        },
    )

    images = MultipleFileField(required=False)

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None:
            raise ValidationError('Vui lòng chọn số sao.')
        if rating < 1 or rating > 5:
            raise ValidationError('Số sao phải từ 1 đến 5.')
        return rating

    def clean_comment(self):
        comment = (self.cleaned_data.get('comment') or '').strip()
        if not comment:
            raise ValidationError('Vui lòng nhập nội dung đánh giá.')
        if len(comment) < 10:
            raise ValidationError('Nội dung đánh giá quá ngắn (tối thiểu 10 ký tự).')
        return comment

    def clean(self):
        cleaned = super().clean()
        rating = cleaned.get('rating')
        comment = (cleaned.get('comment') or '').strip()

        # Nếu rating thấp, yêu cầu comment dài hơn để tránh đánh giá "1 sao" không lý do
        if rating in (1, 2) and len(comment) < 20:
            raise ValidationError('Với đánh giá 1-2 sao, vui lòng mô tả chi tiết hơn (tối thiểu 20 ký tự).')

        return cleaned

    def clean_images(self):
        files = self.cleaned_data.get('images') or []
        if len(files) > 6:
            raise ValidationError('Bạn chỉ được tải lên tối đa 6 ảnh.')

        allowed = {'image/jpeg', 'image/png', 'image/webp'}
        max_size = 2 * 1024 * 1024  # 2MB / ảnh
        for f in files:
            content_type = getattr(f, 'content_type', '')
            if content_type not in allowed:
                raise ValidationError('Chỉ chấp nhận ảnh JPG/PNG/WebP.')
            if getattr(f, 'size', 0) > max_size:
                raise ValidationError('Mỗi ảnh tối đa 2MB.')
        return files

