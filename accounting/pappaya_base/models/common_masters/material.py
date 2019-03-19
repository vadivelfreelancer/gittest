# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class MaterialSet(models.Model):
    _name = 'material.set'
    _description = 'Material set'

    name = fields.Char(string='Material Set Name', size=40)
    set_line_ids = fields.One2many('material.set.line', 'product_set_id', string="Material")
    total_material_price = fields.Float(string='Total', compute='compute_material_price')

    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")

    @api.depends('set_line_ids.total_price')
    def compute_material_price(self):
        amt = 0
        for material in self:
            for rec in material.set_line_ids:
                amt += rec.total_price
            material.total_material_price = amt


class MaterialSetLine(models.Model):
    _name = 'material.set.line'
    _description = 'Material set line'
    _rec_name = 'product_id'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=0)
    product_set_id = fields.Many2one('material.set', string='Material Set', ondelete='cascade')
    product_template_id = fields.Many2one('product.template', string='Name')
    product_id = fields.Many2one('product.product', domain=[('sale_ok', '=', True)], string='Name')
    product_variant_ids = fields.Many2many('product.product',
                                           domain="""['&',('sale_ok', '=', True), ('product_tmpl_id', '=', product_template_id),]""",
                                           string='Variant')
    quantity = fields.Float(string='Quantity', default=1)
    price = fields.Float(string='Per Price')
    total_price = fields.Float(string='Subtotal', compute='compute_total_price')

    @api.constrains('price')
    def check_price(self):
        if self.price < 0:
            raise ValidationError('Please enter the valid Price..!')

    @api.onchange('price')
    def onchange_price(self):
        if self.price:
            self.check_price()

    @api.onchange('quantity')
    def onchange_quantity(self):
        if self.quantity:
            self.check_quantity()

    @api.onchange('quantity')
    def check_quantity(self):
        if self.quantity <= 0:
            raise ValidationError('Please enter the valid Quantity..!')

    @api.depends('quantity', 'price')
    def compute_total_price(self):
        for rec in self:
            rec.total_price = rec.quantity * rec.price


class ProductProduct(models.Model):
    _inherit = "product.product"

    select_type = fields.Selection([('product', 'Product'), ('uniform', 'Uniform'),
                                    ('nslate', 'Nslate'), ('fees_head', 'Fee Type')], string='Type')

    @api.constrains('lst_price')
    def check_price(self):
        if self.lst_price < 0:
            raise ValidationError('Please enter the valid Price..!')

    @api.onchange('lst_price')
    def onchange_check_price(self):
        if self.lst_price < 0:
            raise ValidationError('Please enter the valid Price..!')

    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    name = fields.Char('Name', index=True, required=True, translate=True, size=40)
    select_type = fields.Selection([('product', 'Product'), ('uniform', 'Uniform'), ('nslate', 'Nslate'),
                                    ('fees_head', 'Fee Type')], string='Type')

    @api.one
    @api.constrains('name', 'select_type')
    def check_name(self):
        if self.name and len(self.search([('name', '=', self.name), ('select_type', '=', self.select_type)])) > 1:
            raise ValidationError('Name Already exist..!')

    @api.constrains('lst_price')
    def check_price(self):
        if self.lst_price < 0:
            raise ValidationError('Please enter the valid Price..!')

    @api.onchange('lst_price')
    def onchange_check_price(self):
        if self.lst_price < 0:
            raise ValidationError('Please enter the valid Price..!')

    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    name = fields.Char('Name', required=True, translate=True, size=40)

    @api.constrains('name')
    def check_attribute(self):
        if self.name and len(self.search([('name', '=ilike', self.name)])) > 1:
            raise ValidationError("Attribute already exists.")


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            existing_attrinutes = self.search([('attribute_id', '=', self.attribute_id.id), ('name', '=', self.name)])
            if existing_attrinutes:
                raise ValidationError("You are not allowed to Duplicate")
