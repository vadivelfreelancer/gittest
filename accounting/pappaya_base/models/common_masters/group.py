# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PappayaGroup(models.Model):
    _name = 'pappaya.group'

    name = fields.Char('Group Name', size=124)
    academic_year = fields.Many2one('academic.year','Academic Year',default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    zone_id = fields.Many2one('operating.unit','Zone')
    branch_id = fields.Many2one('operating.unit','Branch')
    # office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    description = fields.Text('Description', size=100)
    course_id = fields.Many2one('pappaya.course',string='Course')

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaGroup, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaGroup, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

#     @api.onchange('office_type_id')
#     def onchange_office_type_id(self):
#         if self.office_type_id:
#             self.course_id = None

    @api.constrains('name')
    def validate_of_name(self):
        if self.name:
            if len(self.sudo().search([('name', '=', self.name.strip())])) > 1:
                raise ValidationError("Group is already exists!")

    @api.multi
    @api.depends('name', 'course_id')
    def name_get(self):
        result = []
        for gp in self:
            try:
                if gp.name and gp.course_id:
                    name = str(gp.name) + ' (' + str(gp.course_id.name) + ') '
                else:
                    name = gp.name
                result.append((gp.id, name))
            except:
                result.append((gp.name, name))
        return result
