# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class PappayaAdditionalRegion(models.Model):
    _name = 'pappaya.additional.region'
    
    school_id = fields.Many2one('operating.unit', 'School', default=lambda self : self.env.user.default_operating_unit_id)
    name = fields.Char(string='Name', size=40)
    description = fields.Text(string='Description',size=200)
    office_type_id = fields.Many2one('pappaya.office.type', 'School/College')
    emp_slno = fields.Char('Emp SL No.')
    unique_no = fields.Char('Unique No.')
    ic_name = fields.Char('IC Name')
    mobile = fields.Char('Mobile')
    ip_address = fields.Char('IP Address')
    email = fields.Char('Email')
    day_avg_amt = fields.Float('Day Avg. Amount')
    hos_avg_amt = fields.Float('Hostel Avg. Amount')
    jr_day_avg_amt = fields.Float('JR Day Avg. Amount')
    jr_hos_avg_amt = fields.Float('JR Hostel Avg. Amount')

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name),('office_type_id','=',self.office_type_id.id)])) > 1:
            raise ValidationError("Name already exists")

