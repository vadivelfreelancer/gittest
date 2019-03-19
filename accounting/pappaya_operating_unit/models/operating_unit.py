# Copyright 2015-2017 Eficent
# - Jordi Ballester Alomar
# Copyright 2015-2017 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models


class OperatingUnit(models.Model):

    _name = 'operating.unit'
    _description = 'Operating Unit'

    name = fields.Char('Name', required=True, limit=100)
    code = fields.Char('Code', required=True,size=25)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, default=lambda self:
        self.env['res.company']._company_default_get('account.account'))
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    
    @api.onchange('name')
    def onchange_name(self):
        if self.name and self.name.strip():
            self.name = str(self.name.strip()).upper()
    
    @api.model
    def create(self, vals):
        if not 'partner_id' in vals:
            vals['partner_id'] = self.env['res.partner'].sudo().create({'name':str(vals['name'])+" ("+str(vals['code'])+")"}).id
        return super(OperatingUnit, self).create(vals)

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)',
         'The code of the operating unit must '
         'be unique per company!'),
        ('name_company_uniq', 'unique (name,company_id)',
         'The name of the operating unit must '
         'be unique per company!')
    ]

#     @api.model
#     def name_search(self, name='', args=None, operator='ilike', limit=100):
#         # Make a search with default criteria
#         names1 = super(models.Model, self).name_search(
#             name=name, args=args, operator=operator, limit=limit)
#         # Make the other search
#         names2 = []
#         if name:
#             domain = [('code', '=ilike', name + '%')]
#             names2 = self.search(domain, limit=limit).name_get()
#         # Merge both results
#         return list(set(names1) | set(names2))[:limit]


class OperatingUnitInherit(models.Model):
    _inherit = 'operating.unit'
    parent_id = fields.Many2one('operating.unit', 'Entity')
    child_ids = fields.One2many('operating.unit', 'parent_id', 'Children')
