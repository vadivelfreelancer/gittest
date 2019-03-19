# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp

class PappayaCoursePackage(models.Model):
    _name = 'pappaya.course.package'

    school_id = fields.Many2one('operating.unit', 'Branch')
    academic_year_id = fields.Many2one('academic.year','Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char('Course Package Name', size=124)
    course_id = fields.Many2one('pappaya.course','Course')
    group_id = fields.Many2one('pappaya.group',"Group")
    batch_id = fields.Many2one('pappaya.batch','Batch')
    package_id = fields.Many2one('pappaya.package','Package')
    entity_id = fields.Many2one('operating.unit', 'Entity',domain=[('type','=','entity')])
    office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    material_set_ids = fields.One2many('admission.material.line', 'course_package_id', string='Material Set')
    material_amt = fields.Float(string='Material Amount', compute='compute_material_amt')
    cp_material_set_ids = fields.One2many('cp.material.set', 'course_package_id', string='Material Set')

    @api.depends('cp_material_set_ids.material_set_price')
    def compute_material_amt(self):
        amt = 0.0
        for rec in self:
            for line in rec.cp_material_set_ids:
                amt += line.material_set_price
            rec.material_amt = amt

    @api.one
    @api.constrains('course_id', 'group_id', 'batch_id', 'package_id')
    def check_name_exists(self):
        if self.course_id and self.group_id and self.batch_id and self.package_id and self.office_type_id:
            if len(self.search([('entity_id','=',self.entity_id.id),('office_type_id', '=', self.office_type_id.id),('course_id', '=', self.course_id.id),('group_id', '=', self.group_id.id),
                                ('batch_id', '=', self.batch_id.id),('package_id', '=', self.package_id.id)])) > 1:
                raise ValidationError('Course Package is already exists for selected CGBP.')
            
    @api.model
    def create(self, vals):
        res = super(PappayaCoursePackage, self).create(vals)
        for c in res:
            name = ''
            if c.course_id and c.group_id and c.batch_id and c.package_id:
                name = str(c.course_id.name)+'-' + str(c.group_id.name) + '-' + str(c.batch_id.name) + '-' + str(c.package_id.name)
            if name:
                c.name = name
        return res

    @api.onchange('course_id', 'group_id', 'batch_id', 'package_id')
    def onchange_course_group_batch_program_id(self):
        for record in self:
            if record.course_id and record.group_id and record.batch_id and record.package_id:
                record.name = str(record.course_id.name) + '-' + str(record.group_id.name) + '-' + str(record.batch_id.name) + '-' + str(record.package_id.name)
            else:
                record.name = False
    
#     @api.multi
#     def write(self, vals):
#         res = super(PappayaCoursePackage, self).write(vals)
#         for c in self:
#             name = ''
#             if c.course_id and c.group_id and c.batch_id and c.package_id:
#                 name = str(c.course_id.name)+'-' + str(c.group_id.name) + '-' + str(c.batch_id.name) + '-' + str(c.package_id.name)
#             if name:
#                 c.name = name
#         return res

    @api.onchange('entity_id')
    def onchange_entity_id(self):
        if self.entity_id:
            self.office_type_id = self.course_id = self.group_id = self.batch_id = self.package_id = None

    @api.onchange('office_type_id')
    def onchange_office_type_id(self):
        if self.office_type_id:
            self.course_id = self.group_id = self.batch_id = self.package_id = None

    @api.onchange('course_id')
    def onchange_course_id(self):
        if self.course_id:
            self.group_id = self.batch_id = self.package_id = None

    @api.onchange('group_id')
    def onchange_group_id(self):
        if self.group_id:
            self.batch_id = self.package_id = None

    @api.onchange('batch_id')
    def onchange_batch_id(self):
        if self.batch_id:
            self.package_id = None


class CpMaterialSet(models.Model):
    _name = 'cp.material.set'
    _rec_name = 'material_set_id'

    course_package_id = fields.Many2one('pappaya.course.package', string='Course Package', ondelete="cascade")
    material_set_id = fields.Many2one('material.set', string='Material Set Name', ondelete="cascade")
    material_set_price = fields.Float(string='Material Set Price')

    @api.onchange('material_set_id')
    def onchange_material_price(self):
        if self.material_set_id:
            self.material_set_price = self.material_set_id.total_material_price

class AdmissionMaterialLine(models.Model):
    _name = "admission.material.line"

    course_package_id = fields.Many2one('pappaya.course.package', string='Course', ondelete="cascade")
    sequence = fields.Integer(string='Sequence')
    from_material_set = fields.Selection([('yes','Yes'),('no','No')],string='From Material Set', default='no')
    product_id = fields.Many2one('product.product', string='Material', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict')
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure')
    price_unit = fields.Float('Per Unit Price', related='product_id.lst_price', digits=dp.get_precision('Material Price'))
    price_subtotal = fields.Float(string='Subtotal', compute='compute_price')

    @api.depends('product_uom_qty','price_unit')
    def compute_price(self):
        for rec in self:
            rec.price_subtotal = rec.product_uom_qty * rec.price_unit