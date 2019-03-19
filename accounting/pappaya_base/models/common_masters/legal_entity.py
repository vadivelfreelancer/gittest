# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class PappayaLegalEntity(models.Model):
    _name = 'pappaya.legal.entity'
    
    school_id = fields.Many2one('operating.unit', 'School', default=lambda self : self.env.user.default_operating_unit_id)
    name = fields.Char(required=1, string='Name', size=40)
    code = fields.Char(string='Code', size=5)
    description = fields.Text(string='Description', size=100)
    legal_entity_squence = fields.Char(string='Series')

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")
        
    @api.model
    def create(self, vals):
        res = super(PappayaLegalEntity, self).create(vals)
        sequence_config =self.env['meta.data.master'].search([('name','=','legal_entity')])
        if not sequence_config:
            raise ValidationError(_("Please Configure Legal Entity Sequence"))
        res['legal_entity_squence'] = self.env['ir.sequence'].next_by_code('pappaya.legal.entity') or _('New')
        return res