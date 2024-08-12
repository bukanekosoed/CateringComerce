from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Regexp

# Regex untuk password: minimal 8 karakter, termasuk huruf besar, huruf kecil, angka, dan simbol
PASSWORD_REGEX = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField(
        'Password', 
        validators=[
            DataRequired(), 
            Regexp(PASSWORD_REGEX, message=(
                'Password must be at least 8 characters long, include at least one uppercase letter, '
                'one lowercase letter, one number, and one special character.'
            ))
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password', 
        validators=[
            DataRequired(), 
            EqualTo('password', message='Passwords must match.')
        ]
    )
    submit = SubmitField('Register')
    
class CategoriesForm(FlaskForm):
    nama_kategori = StringField('Nama Kategori', validators=[DataRequired()])
    gambar = FileField('Gambar', validators=[DataRequired()])
    submit = SubmitField('Simpan Kategori')