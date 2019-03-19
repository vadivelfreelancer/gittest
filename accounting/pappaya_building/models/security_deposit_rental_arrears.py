from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re

class SecurityDepositRentalArrears(models.Model):
    _name = 'security.deposit.rental.arrears'
    _description = 'Security Deposit Rental Arrears'

    name = fields.Char(size=40)
    apex_id = fields.Many2one('operating.unit', string="Apex",domain=[('type','=','entity')])
    branch_id = fields.Many2one('operating.unit', string="Branch",domain=[('type','=','branch')])
    building_id = fields.Many2one('pappaya.building', string="Buidling")
    date = fields.Date(string='Date')
    security_deposit_id = fields.Many2one('security.deposit',string='Security Deposit')
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved')], readonly=True, default='draft')
    owner_id = fields.Many2one("pappaya.owner", string='Owner Name')
    arrear_amount = fields.Float()

    @api.multi
    def act_proposal(self):
        self.state = 'proposed'

    @api.multi
    def act_approval(self):
        self.state = 'approved'
        new_sequence_code = 'security.deposit.rental.arrears'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        self.security_deposit_id.arrear_amount = self.arrear_amount
        self.security_deposit_id.available_amount = self.security_deposit_id.deposit_amount + self.security_deposit_id.in_amount - self.security_deposit_id.out_amount - self.security_deposit_id.arrear_amount + self.security_deposit_id.advance_transfer_amount
        self.owner_id.arrear_amount = self.owner_id.arrear_amount - self.arrear_amount
  
    @api.multi
    def act_advance(self):
        self.deposit_type = 'convert_to_advance'


    @api.onchange('apex_id')
    def _onchange_apex(self):
        if self.apex_id:
            return {'domain': {'branch_id_id': [('parent_id', '=', self.apex_id.id)]}}
        else:
            return {}
        
    @api.onchange('owner_id')
    def _onchange_owner(self):
        if self.owner_id:
            self.arrear_amount = self.owner_id.arrear_amount
