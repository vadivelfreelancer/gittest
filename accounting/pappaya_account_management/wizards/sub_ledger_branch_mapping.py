from odoo import api, fields, models


class SubLedgerBranchLink(models.TransientModel):
    _name = 'subledger.branch.wizard'

    financial_year = fields.Many2one('financial.year', string='Financial Year')
    branches = fields.Many2many("operating.unit", string="Branches", )
    sub_ledgers = fields.Many2one("account.account", string="Sub Ledgers", )

    @api.onchange('financial_year', 'sub_ledgers')
    def update_sub_ledgers(self):
        for record in self:
            if record.financial_year and record.sub_ledgers:
                for item in record.sub_ledgers.fy_branches:
                    if record.financial_year == item.financial_year:
                        record.branches = item.branches

                # record.sub_ledgers = record.financial_year.branch_financial

    @api.model
    def create(self, values):
        if values.get('financial_year') and values.get('branches'):
            fy = self.env['financial.year'].browse(values.get('financial_year'))
            sub_ledger = self.env['account.account'].browse(values.get('sub_ledgers'))
            in_sub_ledger = False
            for item in sub_ledger.fy_branches:
                if item.financial_year == fy:
                    item.branches = values.get('branches')
                    in_sub_ledger = True
            if in_sub_ledger == False:
                sub_ledger.fy_branches.create({
                    'financial_year': values.get('financial_year'),
                    'branches': values.get('branches'),
                    'sub_ledger_id': sub_ledger.id
                })
        return super(SubLedgerBranchLink, self).create(values)
