from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re

class BuildingAdvanceSecurityDeposit(models.Model):
    _name = 'building.advance.security.deposit'
    _description = 'Building Advance Security Deposit'
  
    name = fields.Char(size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch",domain=[('type','=','branch')])
    building_id = fields.Many2one('pappaya.building', string="Building")
    date = fields.Date(string='Date')
    owner_id = fields.Many2one("pappaya.owner", string='Owner Name')
    building_advance_id = fields.Many2one('building.advance',string='Building Advance')
    advance_transfer_amount = fields.Float(string='Transfer Amount')
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved')], readonly=True, default='draft')

    @api.multi
    def act_proposal(self):
        self.state = 'proposed'

    @api.multi
    def act_approval(self):
        self.state = 'approved'
        new_sequence_code = 'building.advance.security.deposit'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        self.building_advance_id.security_deposit_transfer = self.advance_transfer_amount
        self.building_advance_id.available_advance = self.building_advance_id.advance_amount + self.building_advance_id.in_advance - self.building_advance_id.out_advance - self.building_advance_id.arrear_advance - self.building_advance_id.security_deposit_transfer
        deposit_obj = self.env['security.deposit']
        to_deposit = deposit_obj.search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('owner_id','=',self.owner_id.id)])
        if to_deposit:
            to_deposit.advance_transfer_amount += self.advance_transfer_amount
            to_deposit.available_amount = to_deposit.deposit_amount + to_deposit.in_amount - to_deposit.out_amount - to_deposit.arrear_amount + to_deposit.advance_transfer_amount
        else:
            vals = {
                'name': 'Draft Deposit',
                'branch_id':self.to_branch_id.id,
                'building_id':self.to_building_id.id,
                'owner_id':self.to_owner_id.id,
                'deposit_amount':0.0,
                'in_amount':0.0,
                'advance_transfer_amount':self.advance_transfer_amount,
                'advance_amount':0.0,
                'out_amount':0.0,
                'arrear_amount':0.0,
                'available_amount':self.security_deposit_amount,
                'state':'draft',
                 }
            deposit_obj.create(vals)
        
    @api.multi
    def act_advance(self):
        self.deposit_type = 'convert_to_advance'

    @api.onchange('building_advance_id')
    def _onchange_building_advance(self):
        if self.building_advance_id:
            if self.building_advance_id.available_advance < 1.0:
                raise ValidationError(_("No Available advance to be transfer"))
            self.advance_transfer_amount = self.building_advance_id.available_advance

