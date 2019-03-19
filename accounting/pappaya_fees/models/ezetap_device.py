# -*- coding: utf-8 -*-
from odoo import api, fields, models,tools, _
from odoo.exceptions import except_orm, ValidationError, UserError

class pappaya_ezetap_device(models.Model):
    _name = 'pappaya.ezetap.device'
    _description = "Ezetap device master"

    name = fields.Char('Device Name')
    device_id = fields.Char('Device ID(given by ezetap)')
    school_ids_m2m = fields.Many2many('operating.unit', string='School(s)')
    description = fields.Char('Description')
    active = fields.Boolean('Active')

