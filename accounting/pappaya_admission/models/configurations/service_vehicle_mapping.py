# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import  ValidationError


class PappayaServiceVehicleMapping(models.Model):
    _name = 'pappaya.service.vehicle.mapping'
    _description = 'Pappaya Service Vehicle Mapping'

    @api.constrains('vehicle_id', 'branch_id', 'service_id')
    def check_name(self):
        if self.vehicle_id and self.service_id:
            if len(self.search([('branch_id', '=', self.branch_id.id),
                                ('vehicle_id', '=', self.vehicle_id.id),
                                ('service_id', '=', self.service_id.id)])) > 1:
                raise ValidationError("Service already mapped to current Vehicle..!")

    description = fields.Char(string='Description')
    branch_id = fields.Many2one('operating.unit', 'Branch')
    vehicle_id = fields.Many2one('pappaya.vehicle', 'Vehicle')
    service_id = fields.Many2one('pappaya.branch.wise.service', 'Service')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))

    @api.multi
    @api.depends('vehicle_id', 'service_id')
    def name_get(self):
        result = []
        for rec in self:
            if rec.service_id and rec.vehicle_id:
                name = str(rec.service_id.name) + ' - ' + str(rec.vehicle_id.name)
            else:
                name = ''
            result.append((rec.id, name))
        return result

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        if self.branch_id:
            self.service_id = self.vehicle_id = None