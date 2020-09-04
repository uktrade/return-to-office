from django import forms


class GovUKCheckboxInput(forms.widgets.CheckboxInput):
    template_name = 'govuk/forms/widgets/checkbox.html'

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)

        ctx.update({"form_instance": self.form_instance})

        return ctx
