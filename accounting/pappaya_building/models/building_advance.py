from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re

class BuildingAdvance(models.Model):
    _name = 'building.advance'
    _description = 'Security Deposit'
    # ~ _rec_name = 'deposit_amount'
    name = fields.Char(size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string="Building Name")
    date = fields.Date(string='Date')
    no_of_floors = fields.Integer('Number of Floors')
    advance_amount = fields.Float(string='Advance Amount')
    tds_amount = fields.Float(string='TDS Amount')
    owner_id = fields.Many2one("pappaya.owner", string='Owner Name')
    rent = fields.Float(string='Rent ')
    proposed_by = fields.Many2one('res.users','Proposed By')
    remarks = fields.Char('Remarks',size=128)
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved')], readonly=True, default='draft')
    in_advance = fields.Float(string='Transferred-In Advance')
    out_advance = fields.Float(string='Transferred-Out Advance')
    available_advance = fields.Float(string='Available Advance')
    repayment_advance = fields.Float(string='Repayment Advance')
    arrear_advance = fields.Float(string='Arrear Advance')
    security_deposit_transfer = fields.Float('SD Transfer')

    @api.multi
    def act_proposal(self):
        self.state = 'proposed'
        self.proposed_by=self.env.user.id

    @api.multi
    def act_approval(self):
        self.state = 'approved'
        new_sequence_code = 'building.advance'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        
    @api.onchange('branch_id')
    def _onchange_branch(self):
        if self.branch_id:
            return {'domain': {'building_id': [('branch_id', 'in', [self.branch_id.id])]}}
        else:
            return {}

    @api.onchange('building_id')
    def _onchange_building(self):
        if self.building_id:
            floors = self.env['pappaya.floor'].search([('building_id','=',self.building_id.id)])
            self.no_of_floors = len(floors)
        else:
            self.rent = 0.0
            self.owner_id = False
            self.no_of_floors = 0

    @api.onchange('advance_amount')
    def _onchange_advance_amount(self):
        if self.advance_amount:
            self.available_advance = self.advance_amount 
            
    @api.onchange('owner_id')
    def _onchange_owner(self):
        if self.owner_id:
            existing_advance = self.search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('owner_id','=',self.owner_id.id),('state','=','approved')])
            if existing_advance:
                raise ValidationError(_("Advance is already created"))
            self.rent = self.owner_id.rent
