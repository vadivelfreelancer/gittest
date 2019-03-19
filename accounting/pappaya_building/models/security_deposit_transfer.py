from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re

class SecurityDepositTransfer(models.Model):
    _name = 'security.deposit.transfer'
    _description = 'Security Deposit Transfer'

    name = fields.Char(default='Draft Transfer',size=40)
    apex_id = fields.Many2one('operating.unit', string="Apex",domain=[('type','=','entity')])
    from_branch_id = fields.Many2one('operating.unit', string="From Branch",domain=[('type','=','branch')])
    from_building_id = fields.Many2one('pappaya.building', string="From Buidling")
    to_branch_id = fields.Many2one('operating.unit', string="To Branch",domain=[('type','=','branch')])
    to_building_id = fields.Many2one('pappaya.building', string="To Buidling")
    date = fields.Date(string='Date')
    from_security_deposit_id = fields.Many2one('security.deposit',string='From Security Deposit')
    security_deposit_amount = fields.Float(string='Security Deposit (SD) Amount')
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved')], readonly=True, default='draft')
    from_owner_id = fields.Many2one("pappaya.owner", string='From Owner')
    to_owner_id = fields.Many2one("pappaya.owner", string='To Owner')
    to_security_deposit_id = fields.Many2one('security.deposit',string='To Security Deposit')


    @api.multi
    def act_proposal(self):
        self.state = 'proposed'

    @api.multi
    def act_approval(self):
        self.state = 'approved'
        new_sequence_code = 'security.deposit.transfer'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        deposit_obj = self.env['security.deposit']
        from_deposit = deposit_obj.search([('building_id','=',self.from_building_id.id),('branch_id','=',self.from_branch_id.id),('owner_id','=',self.from_owner_id.id)])
        if from_deposit:
            from_deposit.out_amount += (self.security_deposit_amount)
            from_deposit.available_amount = from_deposit.deposit_amount + from_deposit.in_amount - from_deposit.out_amount - from_deposit.arrear_amount + from_deposit.advance_transfer_amount
        to_deposit = deposit_obj.search([('building_id','=',self.to_building_id.id),('branch_id','=',self.to_branch_id.id),('owner_id','=',self.to_owner_id.id)])
        if to_deposit:
            to_deposit.in_amount += self.security_deposit_amount
            to_deposit.available_amount = to_deposit.deposit_amount + to_deposit.in_amount - to_deposit.out_amount - to_deposit.arrear_amount + to_deposit.advance_transfer_amount
        else:
            vals = {
                'name': 'Draft Deposit',
                'branch_id':self.to_branch_id.id,
                'building_id':self.to_building_id.id,
                'owner_id':self.to_owner_id.id,
                'deposit_amount':0.0,
                'in_amount':self.security_deposit_amount,
                'advance_transfer_amount':0.0,
                'out_amount':0.0,
                'arrear_amount':0.0,
                'available_amount':self.security_deposit_amount,
                'state':'draft',
                 }
            deposit_obj.create(vals)

    @api.multi
    def act_advance(self):
        self.deposit_type = 'convert_to_advance'
        
    @api.onchange('security_deposit_id')
    def onchange_security_deposit(self):
        if self.security_deposit_id:
            self.security_deposit_amount = self.security_deposit_id.available_amount or 0.0
            
    @api.onchange('apex_id')
    def _onchange_apex(self):
        if self.apex_id:
            return {'domain': {'from_branch_id_id': [('parent_id', '=', self.apex_id.id)],'to_branch_id_id': [('parent_id', '=', self.apex_id.id)]}}
        else:
            return {}

