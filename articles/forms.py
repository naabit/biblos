from django import forms


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="Selecciona un archivo Excel",
        help_text="Formatos permitidos: .xlsx, .csv",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
