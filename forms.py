from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, FileField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    """
    Formulário de registro de usuário.
    """
    name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password_confirm = PasswordField('Confirmar Senha',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

class LoginForm(FlaskForm):
    """
    Formulário de login de usuário.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    """
    Formulário para adicionar e editar produtos.
    """
    name = StringField('Nome do Produto', validators=[DataRequired()])
    description = TextAreaField('Descrição', validators=[Optional()])
    price = DecimalField('Preço', validators=[DataRequired()])
    category = StringField('Categoria', validators=[Optional()])
    photo = FileField('Foto do Produto')
    is_delivery = BooleanField('Disponível para Delivery')
    is_balcao = BooleanField('Disponível para Balcão')
    submit = SubmitField('Salvar')
