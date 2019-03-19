# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HRDepartmentName(models.Model):
    _name = 'hr.department.name'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'

    name = fields.Char('Department Name' ,size=150)
    description = fields.Text(string='Description', size=100)

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            department = self.env['hr.department'].search([('department_master_id','=',self.id)])
            if department:
                department.name = vals['name']
            return super(HRDepartmentName, self).write(vals)