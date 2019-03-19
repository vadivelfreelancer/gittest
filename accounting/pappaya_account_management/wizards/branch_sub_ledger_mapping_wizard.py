from odoo import api, fields, models


class BranchFyLink(models.TransientModel):
    _name = 'branch.subledger.wizard'

    financial_year = fields.Many2one('financial.year', string='Financial Year')
    branches = fields.Many2one("operating.unit", string="Branches", )
    sub_ledgers = fields.Many2many("account.account", string="Sub Ledgers", )

    @api.onchange('financial_year', 'branches')
    def update_sub_ledgers(self):
        for record in self:
            if record.financial_year and record.branches:
                for item in record.branches.fy_subledgers:
                    if record.financial_year == item.financial_year:
                        record.sub_ledgers = item.sub_ledger

    @api.model
    def create(self, values):
        if values.get('financial_year') and values.get('branches'):
            fy = self.env['financial.year'].browse(values.get('financial_year'))
            branch = self.env['operating.unit'].browse(values.get('branches'))
            in_branch = False
            for item in branch.fy_subledgers:
                if item.financial_year == fy:
                    item.sub_ledger = values.get('sub_ledgers')
                    in_branch = True
            if not in_branch:
                branch.fy_subledgers.create({
                    'financial_year': values.get('financial_year'),
                    'sub_ledger': values.get('sub_ledgers'),
                    'branch_id': branch.id
                })
        return super(BranchFyLink, self).create(values)
