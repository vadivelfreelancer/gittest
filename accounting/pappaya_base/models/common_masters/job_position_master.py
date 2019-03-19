# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HRJobPositionName(models.Model):
    _name = 'hr.job.name'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'

    name = fields.Char('Designation',size=50)
    description = fields.Text(string='Description', size=100)

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Designation already exists")

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            job = self.env['hr.job'].search([('job_master_id','=',self.id)])
            if job:
                job.name = vals['name']
        return super(HRJobPositionName, self).write(vals)