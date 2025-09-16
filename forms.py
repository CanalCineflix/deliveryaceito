from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, TextAreaField, SelectField, DecimalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from models import User, Product
import re

class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    phone = StringField('Telefone', validators=[DataRequired(), Length(min=10, max=20)])
    restaurant_name = StringField('Nome do Restaurante', validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

class ProductForm(FlaskForm):
    name = StringField('Nome do Produto', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição')
    price = DecimalField('Preço', validators=[DataRequired(), NumberRange(min=0)])
    category = StringField('Categoria', validators=[Length(max=50)])
    is_active = BooleanField('Ativo')
    photo_url = StringField('URL da Foto', validators=[Length(max=255)])
    is_delivery = BooleanField('Disponível para Delivery')
    is_balcao = BooleanField('Disponível para Retirada no Balcão')
    submit = SubmitField('Salvar Produto')

    def validate_photo_url(self, field):
        if field.data and not re.match(r'^https?://.+', field.data):
            raise ValidationError('A URL da foto deve ser uma URL válida começando com http:// ou https://.')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Senha Antiga', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Alterar Senha')

class RequestPasswordResetForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar Redefinição de Senha')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Redefinir Senha')
