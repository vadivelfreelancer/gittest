# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class PappayaDistanceSlab(models.Model):
    _name = 'pappaya.distance.slab'
    _description = 'Pappaya Distance Slab'

    # @api.constrains('amount')
    # def _check_amount(self):
    #     if self.amount:
    #         if self.amount < 0.0:
    #             raise ValidationError("Amount must be positive")

    @api.constrains('name')
    def check_name(self):
        if self.name:
            if len(self.search([('school_id', '=', self.school_id.id), ('name', '=', self.name)])) > 1:
                raise ValidationError("Name already exists.")

    school_id = fields.Many2one('operating.unit', 'Branch')# default=lambda self: self.env.user.company_id)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char('Name', size=64)
    description = fields.Char('Description')
    amount = fields.Float('Amount')

    @api.multi
    @api.depends('school_id', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.school_id and rec.name:
                name = str(rec.name) + ' ( ' + str(rec.sudo().school_id.name) + ' )'
            else:
                name = ''
            result.append((rec.id, name))
        return result


class PappayaTransportRoute(models.Model):
    _name = 'pappaya.transport.route'
    _description = 'Pappaya Transport Routes'

    @api.constrains('name','service_id')
    def check_name(self):
        if self.name and self.service_id:
            if len(self.search([('school_id', '=', self.school_id.id), ('name', '=', self.name),
                                ('service_id', '=', self.service_id.id)])) > 1:
                raise ValidationError("Name already exists.")

    name = fields.Char(string='Name', size=40)
    pickup_time = fields.Float('Pickup Time')
    drop_time = fields.Float('Drop Time')
    sr_pickup_time = fields.Float('SR Pickup Time')
    sr_drop_time = fields.Float('SR Drop Time')
    is_active = fields.Boolean(string='Active', default=True)
    school_id = fields.Many2one('operating.unit', 'Branch')# default=lambda self: self.env.user.company_id)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    # service_vehicle_id = fields.Many2one('pappaya.service.vehicle.mapping', 'Service')
    service_id = fields.Many2one('pappaya.branch.wise.service', 'Service')
    transport_stop_ids = fields.One2many('pappaya.transport.stop', 'route_id', string='Stop(s)')


class PappayaTransportStop(models.Model):
    _name = 'pappaya.transport.stop'
    _description = 'Pappaya Transport Stop'

    @api.constrains('amount')
    def _check_amount(self):
        if self.amount <= 0.0:
            raise ValidationError("Amount must be positive or greater than zero")

    @api.constrains('name', 'distance_slab_id')
    def check_name(self):
        if self.name:
            if len(self.search([('name', '=', self.name),('route_id', '=', self.route_id.id)])) > 1:
                raise ValidationError("Name already exists.")
        if self.distance_slab_id:
            if len(self.search([('distance_slab_id', '=', self.distance_slab_id.id),('route_id', '=', self.route_id.id)])) > 1:
                raise ValidationError("Transport Slab ready exists.")

    route_id = fields.Many2one('pappaya.transport.route', 'Route')
    school_id = fields.Many2one('operating.unit', 'Branch', related='route_id.school_id', store=True)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(string='Name', size=40)
    amount = fields.Float('Amount')
    distance_slab_id = fields.Many2one('pappaya.distance.slab', string='Transport Slab')
    pickup_time = fields.Float('Pickup Time')
    drop_time = fields.Float('Drop Time')
    sr_pickup_time = fields.Float('SR Pickup Time')
    sr_drop_time = fields.Float('SR Drop Time')

    @api.multi
    @api.depends('distance_slab_id', 'name')
    def name_get(self):
        result = []
        for rec in self:
            if rec.distance_slab_id and rec.name:
                name = str(rec.distance_slab_id.name) + ' - ' + str(rec.name)
            else:
                name = ''
            result.append((rec.id, name))
        return result

    @api.onchange('pickup_time','drop_time','sr_pickup_time','sr_drop_time','amount')
    def onchange_time(self):
        if self.sr_pickup_time < 0 or self.drop_time < 0 or self.pickup_time < 0 or self.sr_drop_time < 0:
            raise ValidationError("Time must be positive or greater than zero")
        if self.amount < 0:
            raise ValidationError("Amount must be positive or greater than zero")
            
    # @api.onchange('distance_slab_id')
    # def onchange_distance_slab_id(self):
    #     if self.distance_slab_id:
    #         self.amount = self.distance_slab_id.amount