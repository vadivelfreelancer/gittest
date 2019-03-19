from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re

class SecurityDeposit(models.Model):
    _name = 'security.deposit'
    _description = 'Security Deposit'
    # ~ _rec_name = 'deposit_amount'
    
    name = fields.Char(size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string="Buidling Name")
    deposit_type = fields.Selection([('security_deposit','Security Deposit'),('convert_to_advance','Convert to Advance')],'Deposit Type',default="security_deposit",readonly="1")
    date = fields.Date(string='Date')
    owner_id = fields.Many2one("pappaya.owner", string='Owner Name')
    rent = fields.Float(string='Rent ')
    deposit_amount = fields.Float(string='Deposit Amount')
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved')], readonly=True, default='draft')
    in_amount = fields.Float(string='Transferred-In Amount')
    out_amount = fields.Float(string='Transferred-Out Amount')
    available_amount = fields.Float(string='Available Amount')  
    repayment_amount = fields.Float(string='Repayment Amount')
    arrear_amount = fields.Float(string='Arrear Amount')
    advance_transfer_amount = fields.Float('Transferred from Advance')

    @api.multi
    def act_proposal(self):
        self.state = 'proposed'

    @api.multi
    def act_approval(self):
        self.state = 'approved'
        new_sequence_code = 'security.deposit'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        
    @api.onchange('branch_id')
    def _onchange_branch(self):
        if self.branch_id:
            return {'domain': {'building_id': [('branch_id', 'in', [self.branch_id.id])]}}
        else:
            return {}

    @api.onchange('deposit_amount')
    def _onchange_deposit_amount(self):
        if self.deposit_amount:
            self.available_amount = self.deposit_amount        

    @api.onchange('owner_id')
    def _onchange_owner(self):
        if self.owner_id:
            existing_deposit = self.search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('owner_id','=',self.owner_id.id),('state','=','approved')])
            if existing_deposit:
                raise ValidationError(_("Security Deposit is already created"))
            self.rent = self.owner_id.rent

