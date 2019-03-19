# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class PappayaStream(models.Model):
    _name = 'pappaya.stream'
    
    school_id = fields.Many2one('operating.unit', 'School', default=lambda self : self.env.user.default_operating_unit_id)
    name = fields.Char(required=1, string='Name', size=40)
    code = fields.Char(string='Code', size=5)
    description = fields.Text(string='Description', size=100)
    sequence_id = fields.Char('Series')
    
    
    @api.model
    def create(self, vals):
        res = super(PappayaStream, self).create(vals)
        sequence_config =self.env['meta.data.master'].search([('name','=','stream')])
        if not sequence_config:
            raise ValidationError(_("Please Configure Stream Sequence in Employee ID Sequence master"))
        res['sequence_id'] = self.env['ir.sequence'].next_by_code('pappaya.stream') or _('New')
        return res

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")
