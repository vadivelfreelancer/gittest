from odoo import api, fields, models


class BranchFyLink(models.TransientModel):
    _name = 'branch.fy.wizard'

    financial_year = fields.Many2one('financial.year', string='Financial Year')
    branches = fields.Many2many("operating.unit", string="Branches", )

    @api.onchange('financial_year')
    def update_sub_ledgers(self):
        for record in self:
            if record.financial_year:
                record.branches = record.financial_year.branch_financial

    @api.model
    def create(self, values):
        if values.get('financial_year'):
            fy = self.env['financial.year'].browse(values.get('financial_year'))
            fy.branch_financial = values.get('branches')
        return super(BranchFyLink, self).create(values)
