# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import  ValidationError


class PappayaBranchWiseService(models.Model):
    _name = 'pappaya.branch.wise.service'
    _description = 'Pappaya Branch wise Service'

    @api.constrains('name', 'school_id')
    def check_name(self):
        if self.name:
            if len(self.search([('school_id', '=', self.school_id.id), ('name', '=', self.name)])) > 1:
                raise ValidationError("Name already exists.")

    name = fields.Char(string='Name', size=40)
    description = fields.Text(string='Description', size=100)
    school_id = fields.Many2one('operating.unit', 'Branch')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    vehicle_id = fields.Many2one('pappaya.vehicle', 'Vehicle')
    transport_incharge_ids = fields.Many2many(related='vehicle_id.transport_incharge_ids', relation='hr.employee',
                                              string='Transport In charge')

    @api.onchange('school_id')
    def onchange_branch_id(self):
        if self.school_id:
           self.vehicle_id = None

    @api.multi
    @api.depends('vehicle_id', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.vehicle_id:
                name = str(rec.name) + ' - ' + str(rec.vehicle_id.name)
            else:
                name = ''
            result.append((rec.id, name))
        return result