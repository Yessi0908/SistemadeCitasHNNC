from django.core.exceptions import ValidationError

PALABRAS_INSTITUCIONALES = ('hospital', 'hnncj', 'nicolasa', 'jalapa', 'clave', 'contrasena', 'contraseña')


class PalabrasInstitucionalesValidator:
    """Rechaza contraseñas que solo son el nombre del hospital o palabras obvias."""

    def validate(self, password, user=None):
        texto = password.lower()
        for palabra in PALABRAS_INSTITUCIONALES:
            resto = texto.replace(palabra, '')
            if len(resto) < 4 and palabra in texto:
                raise ValidationError(
                    'La contraseña no puede basarse en el nombre del hospital o palabras obvias.',
                    code='password_institucional',
                )

    def get_help_text(self):
        return 'La contraseña no puede basarse en el nombre del hospital o palabras obvias.'
