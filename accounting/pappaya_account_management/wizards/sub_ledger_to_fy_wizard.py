from odoo import api, fields, models


class SubLedgerFyLink(models.TransientModel):
    _name = 'subledger.fy.wizard'

    financial_year = fields.Many2one('financial.year', string='Financial Year')
    sub_ledgers = fields.Many2many("account.account", string="Sub Ledgers", )

    @api.onchange('financial_year')
    def update_sub_ledgers(self):
        for record in self:
            if record.financial_year:
                record.sub_ledgers = record.financial_year.ledger_financial

    @api.model
    def create(self, values):
        if values.get('financial_year'):
            fy = self.env['financial.year'].browse(values.get('financial_year'))
            fy.ledger_financial = values.get('sub_ledgers')
        return super(SubLedgerFyLink, self).create(values)
