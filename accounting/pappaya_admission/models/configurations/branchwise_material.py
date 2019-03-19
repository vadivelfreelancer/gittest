# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError

class BranchwiseMaterial(models.Model):
    _name = 'branchwise.material'
    _rec_name = 'branch_id'
    _description = 'Branchwise Material'

    branch_id = fields.Many2one('operating.unit', string='Branch')
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    course_package_id = fields.Many2one('pappaya.course.package', string='Course Package')
    branchwise_material_line_ids = fields.One2many('branchwise.material.line', 'material_id', string='Branchwise Material')

    @api.constrains('branch_id', 'academic_year_id', 'course_package_id')
    def check_price_unit(self):
        if self.branch_id and self.academic_year_id and self.course_package_id:
            if len(self.search([('branch_id','=',self.branch_id.id),('academic_year_id','=',self.academic_year_id.id),('course_package_id','=',self.course_package_id.id)])) > 1:
                raise ValidationError('Branchwise Material already exists')

    @api.onchange('branch_id','academic_year_id')
    def onchange_branch(self):
        domain = []
        if self.branch_id and self.academic_year_id:
            for branch in self.branch_id.course_config_ids:
                for cp in branch.course_package_ids:
                    if self.academic_year_id == branch.academic_year_id and cp:
                        domain.append(cp.id)
        return {'domain': {'course_package_id': [('id', 'in', domain)]}}

    @api.onchange('course_package_id')
    def onchange_course_package_id(self):
        if self.course_package_id:
            existing_branchwise_ids = self.search([('course_package_id','=',self.course_package_id.id),('branch_id','=',self.branch_id.id),('academic_year_id','=',self.academic_year_id.id)])
            if existing_branchwise_ids:
                raise ValidationError("Branchwise Material already exists")
        
    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")

    @api.onchange('branchwise_material_line_ids')
    def onchange_branchwise_material_line_ids(self):
        res = {}
        if not self.branchwise_material_line_ids:
            dynamic_query = ""
            dynamic_query += "update product_product set is_assigned='f'"
            self._cr.execute(dynamic_query, ())
        else:
            for i in self.branchwise_material_line_ids.mapped('product_id'):
                i.write({'is_assigned':True})
        return res

class BranchwiseMaterialLine(models.Model):
    _name = "branchwise.material.line"
    _rec_name = 'product_id'

    material_id = fields.Many2one('branchwise.material', string="Material", ondelete="cascade")
    branch_id = fields.Many2one('operating.unit', related='material_id.branch_id', string='Branch')
    academic_year_id = fields.Many2one('academic.year', related='material_id.academic_year_id', string="Academic Year")
    course_package_id = fields.Many2one('pappaya.course.package',related='material_id.course_package_id', string='Course Package')
    sequence = fields.Integer(string='Sequence')
    from_material_set = fields.Selection([('yes','Yes'),('no','No')],string='From Material Set', default='no')
    product_id = fields.Many2one('product.product', string='Material', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict')
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure')
    price_unit = fields.Float('Per Unit Price', digits=dp.get_precision('Material Price'))
    price_subtotal = fields.Float(string='Subtotal', compute='compute_price')

    @api.depends('product_uom_qty','price_unit')
    def compute_price(self):
        for rec in self:
            rec.price_subtotal = rec.product_uom_qty * rec.price_unit

    @api.constrains('price_unit','price_subtotal','product_uom_qty')
    def check_price_unit(self):
        print (self.price_unit, self.price_subtotal, self.product_uom_qty )
        if self.price_unit <= 0 or self.price_subtotal <= 0 or self.product_uom_qty <= 0:
            raise ValidationError('Please enter the valid Price..!')

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        if self.price_unit < 0:
            raise ValidationError('Please enter the valid Price Unit..!')

    @api.onchange('product_uom_qty')
    def onchange_product_uom_qty(self):
        if self.product_uom_qty <= 0:
            raise ValidationError('Please enter the valid Quantity..!')

    @api.onchange('price_subtotal')
    def onchange_price_subtotal(self):
        if self.price_subtotal <= 0:
            raise ValidationError('Please enter the valid Price Subtotal..!')

class ProductProduct(models.Model):
    _inherit = "product.product"

    is_assigned = fields.Boolean()