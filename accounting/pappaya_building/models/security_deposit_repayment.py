from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re

class SecurityDepositRepayment(models.Model):
    _name = 'security.deposit.repayment'
    _description = 'Security Deposit Repayment'

    name = fields.Char(size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch",domain=[('type','=','branch')])
    building_id = fields.Many2one('pappaya.building', string="Building")
    owner_id = fields.Many2one("pappaya.owner", string='Owner Name')
    os_deposit_amount = fields.Float(string='OS Deposit Amount')
    repayment_amount = fields.Float(string='Repayment Amount')
    tds_amount = fields.Float(string='TDS Amount')
    payment_mode_id = fields.Many2one('pappaya.paymode', 'Payment Mode')
    cheque_dd = fields.Char('Cheque/DD No',size=30)
    bank_name = fields.Many2one('res.bank','Bank Name')
    cheque_dd_date = fields.Date('Cheque/DD Date')
    transaction_date = fields.Date('Transaction Date')
    remarks = fields.Char('Remarks',size=128)
    with_voucher = fields.Boolean('With Voucher')
    without_voucher = fields.Boolean('Without Voucher',default=True)
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved')], readonly=True, default='draft')
    is_cheque = fields.Boolean()

    @api.onchange('cheque_dd')
    def onchange_cheque_dd(self):
        for rec in self:
            if rec.cheque_dd:
                cheque_dd = re.match('^[\d]*$', rec.cheque_dd)
                if not cheque_dd:
                    raise ValidationError(_("Please enter a valid Cheque/DD Number"))

    @api.multi
    def act_proposal(self):
        self.state = 'proposed'

    @api.multi
    def act_approval(self):
        self.state = 'approved'
        deposit = self.env['security.deposit'].search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('owner_id','=',self.owner_id.id)])
        if deposit:
            deposit.repayment_amount += self.repayment_amount
            new_sequence_code = 'security.deposit.transfer.repayment'
            self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        else:
            raise ValidationError(_("Security Deposit doest not exists"))

    @api.multi
    def act_advance(self):
        self.deposit_type = 'convert_to_advance'


    @api.onchange('with_voucher','without_voucher')
    def _onchange_with_voucher(self):
        if self.with_voucher==True:
            self.without_voucher=False
        if self.without_voucher==True:
            self.without_voucher=True
            
    @api.onchange('owner_id')
    def onchange_owner_id(self):
        if self.owner_id:
            deposit = self.env['security.deposit'].search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('owner_id','=',self.owner_id.id)])
            if deposit:
                self.os_deposit_amount = deposit.available_amount - deposit.repayment_amount - deposit.arrear_amount + + deposit.advance_transfer_amount  

    @api.onchange('payment_mode_id')
    def onchange_payment_mode(self):
        if self.payment_mode_id and self.payment_mode_id.is_cheque:
            self.is_cheque = True
        else:
            self.is_cheque = False
