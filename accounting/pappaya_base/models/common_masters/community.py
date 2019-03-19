from odoo import api, fields, models
from odoo.exceptions import except_orm, ValidationError

class PappayaCommunity(models.Model):
    _name = 'pappaya.community'
    
    name = fields.Char(string='Name')
    community_code = fields.Char(string='Code')

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaCommunity, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaCommunity, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.multi
    def _check_community(self):
        exiting_ids = self.search([('name', '=', self.name)])
        if len(exiting_ids) > 1:
            return False
        return True

    @api.multi
    def _check_community_code(self):
        exiting_ids = self.search([('community_code', '=', self.community_code)])
        if len(exiting_ids) > 1:
            return False
        return True

    _constraints = [(_check_community, 'Community name already exists', ['name']),
                    (_check_community_code, 'Community Code already exists', ['community_code'])]
