from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re

class BuildingAdvanceTransfer(models.Model):
    _name = 'building.advance.transfer'
    _description = 'Building Advance Transfer'

    name = fields.Char(size=40)
    apex_id = fields.Many2one('operating.unit', string="Apex",domain=[('type','=','entity')])
    from_branch_id = fields.Many2one('operating.unit', string="From Branch",domain=[('type','=','branch')])
    from_building_id = fields.Many2one('pappaya.building', string="From Buidling")
    to_branch_id = fields.Many2one('operating.unit', string="To Branch",domain=[('type','=','branch')])
    to_building_id = fields.Many2one('pappaya.building', string="To Buidling")
    date = fields.Date(string='Date')
    from_building_advance_id = fields.Many2one('building.advance',string='From Advance')
    building_advance_amount = fields.Float(string='Transfer Amount')
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved')], readonly=True, default='draft')
    from_owner_id = fields.Many2one("pappaya.owner", string='From Owner')
    to_owner_id = fields.Many2one("pappaya.owner", string='To Owner')
    to_building_advance_id = fields.Many2one('building.advance',string='To Advance')


    @api.multi
    def act_proposal(self):
        self.state = 'proposed'

    @api.multi
    def act_approval(self):
        self.state = 'approved'
        new_sequence_code = 'building.advance.transfer'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        advance_obj = self.env['building.advance']
        from_advance = advance_obj.search([('building_id','=',self.from_building_id.id),('branch_id','=',self.from_branch_id.id),('owner_id','=',self.from_owner_id.id)])
        if from_advance:
            from_advance.out_advance += (self.building_advance_amount)
            from_advance.available_advance = from_advance.advance_amount + from_advance.in_advance - from_advance.out_advance - from_advance.arrear_advance - from_advance.security_deposit_transfer
        to_advance = advance_obj.search([('building_id','=',self.to_building_id.id),('branch_id','=',self.to_branch_id.id),('owner_id','=',self.to_owner_id.id)])
        if to_advance:
            to_advance.in_advance += self.building_advance_amount
            to_advance.available_advance = to_advance.advance_amount + to_advance.in_advance - to_advance.out_advance - to_advance.arrear_advance - to_advance.security_deposit_transfer
        else:
            vals = {
                'name': 'Draft Advance Transfer',
                'branch_id':self.to_branch_id.id,
                'building_id':self.to_building_id.id,
                'advance_amount':0.0,
                'in_advance':self.building_advance_amount,
                'out_advance':0.0,
                'arrear_advance':0.0,
                'available_advance':self.building_advance_amount,
                'date':self.date,
                'tds_amount':0.0,
                'security_deposit_transfer':0.0,
                'rent': self.to_building_id.rent,
                'state':'draft',
                'owner_id':self.to_owner_id.id
                 }
            advance_obj.create(vals)
        
    @api.multi
    def act_advance(self):
        self.deposit_type = 'convert_to_advance'


    @api.onchange('apex_id')
    def _onchange_apex(self):
        if self.apex_id:
            return {'domain': {'from_branch_id_id': [('parent_id', '=', self.apex_id.id)],'to_branch_id_id': [('parent_id', '=', self.apex_id.id)]}}
        else:
            return {}
            
    @api.onchange('building_advance_id')
    def _onchange_building_advance(self):
        if self.building_advance_id:
            self.building_advance_amount = self.building_advance_id.available_advance or 0.0

