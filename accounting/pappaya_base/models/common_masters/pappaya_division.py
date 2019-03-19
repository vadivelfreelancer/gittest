# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PappayaDivision(models.Model):
    _name = 'pappaya.division'
    _description='Division'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    

    name = fields.Char('Division Name',size=50)
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    district_ids_m2m = fields.Many2many('state.district', string='Districts')
    cluster_id = fields.Many2one('pappaya.cluster', string='Cluster')
    description = fields.Text('Description', size=200)
    emp_slno = fields.Char("Emp Sl No.",size=20)
    user_slno = fields.Char("User Sl No.",size=20)
    unique_no = fields.Char("Unique no",size=20)
    ic_name = fields.Char("IC Name",size=50)
    email = fields.Char("Email",size=50)
    mobile_no = fields.Char("Mobile no",size=10)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name','academic_year_id')
    def check_name(self):
        if len(self.sudo().search([('name', '=', self.name),('academic_year_id','=',self.academic_year_id.id)]).ids) > 1:
            raise ValidationError("Division already exists")

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaDivision, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaDivision, self).write(vals)


            
