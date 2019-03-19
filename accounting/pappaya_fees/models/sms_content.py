# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PappayaSMSContent(models.Model):
    _name = "pappaya.sms.content"
    _description = "SMS Content"

    description = fields.Text(size=300, string="Description")
    type = fields.Selection(
        [('cash', 'Cash'), ('cheque_dd', 'Cheque/DD'), ('money_withdraw', 'Pocket Money Withdraw')])
    active = fields.Boolean('Active', default=True)

    @api.one
    @api.constrains('type')
    def _check_type(self):
        if self.type:
            if len(self.search([('type', '=', self.type), ('active', '=', True)])) > 1:
                raise ValidationError("Already configured for the given Type..!")

    @api.multi
    @api.depends('type')
    def name_get(self):
        result = []
        for record in self:
            if record.type == 'cash':
                name = 'Paymode: Cash'
            elif record.type == 'cheque_dd':
                name = 'Paymode: Cheque/DD'
            else:
                name = 'Pocket Money Withdraw'
            result.append((record.id, name))
        return result

    @api.one
    def copy(self, default=None):
        raise ValidationError('You are not allowed to Duplicate')
