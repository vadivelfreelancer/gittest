# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError


class UniformSet(models.Model):
    _name = 'uniform.set'
    _description = 'Uniform set'

    @api.constrains('name')
    def check_name(self):
        if self.name and len(self.search([('name', '=ilike', self.name)])) > 1:
            raise ValidationError("Name already exists.")

    name = fields.Char(string='Uniform Set Name', size=40)
    uniform_set_item_ids = fields.One2many('uniform.item', 'product_set_id', string="Uniform Items")
    total_amount = fields.Float('Total Amount', compute='compute_total_amount')

    @api.multi
    @api.depends('uniform_set_item_ids.total_price')
    def compute_total_amount(self):
        amount = 0
        for line in self:
            for rec in line.uniform_set_item_ids:
                amount += rec.total_price
            line.total_amount = amount

    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")

    @api.onchange('total_amount')
    def onchange_total_amount(self):
        if self.total_amount < 0:
            raise ValidationError("Enter Valid Amount")


class UniformItem(models.Model):
    _name = 'uniform.item'
    _description = 'Uniform Items'
    _rec_name = 'product_id'
    _order = 'sequence'

    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")

    @api.constrains('quantity')
    def check_quantity(self):
        if self.quantity <= 0:
            raise ValidationError('Please enter the valid quantity..!')

    @api.constrains('price')
    def check_price(self):
        if self.price <= 0:
            raise ValidationError('Please enter the valid Price..!')

    @api.constrains('product_set_id', 'product_variant_id')
    def check_price(self):
        if self.product_variant_id and len(self.search([('product_set_id', '=', self.product_set_id.id),
                            ('product_variant_id', '=', self.product_variant_id.id)])) > 1:
            raise ValidationError('Uniform Variant already exist..!')

    sequence = fields.Integer(string='Sequence', default=0)
    product_template_id = fields.Many2one('product.template', string='Name')
    product_id = fields.Many2one('product.product', domain=[('sale_ok', '=', True)], string='Variant')
    product_variant_id = fields.Many2one('product.product', domain="""['&',('sale_ok', '=', True),
                ('product_tmpl_id', '=', product_template_id),]""", string='Variant')
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Uniform Unit of Measure'), default=1)
    product_set_id = fields.Many2one('uniform.set', string='Uniform Set', ondelete='cascade')
    price = fields.Float(string='Per Price', related='product_template_id.lst_price')
    total_price = fields.Float(string='Sub Total', compute='compute_total_price')

    @api.multi
    @api.depends('quantity', 'price')
    def compute_total_price(self):
        for rec in self:
            rec.total_price = rec.quantity * rec.price
