# forms.py
# Você pode usar Flask-WTF ou WTForms para criar formulários
# Para este exemplo, vamos definir uma classe de formulário simples

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, FileField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Optional

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

