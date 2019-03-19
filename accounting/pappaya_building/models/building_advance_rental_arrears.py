from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re

class BuildingAdvanceRentalArrears(models.Model):
    _name = 'building.advance.rental.arrears'
    _description = 'Building Advance Rental Arrears'

    name = fields.Char(size=40)
    apex_id = fields.Many2one('operating.unit', string="Apex",domain=[('type','=','entity')])
    branch_id = fields.Many2one('operating.unit', string="Branch",domain=[('type','=','branch')])
    building_id = fields.Many2one('pappaya.building', string="Buidling")
    owner_id = fields.Many2one("pappaya.owner", string='Owner Name')
    date = fields.Date(string='Date')
    building_advance_id = fields.Many2one('building.advance',string='Building Advance')
    state = fields.Selection([('draft', 'Draft'), ('proposed', 'Proposed'), ('approved', 'Approved')], readonly=True, default='draft')
    arrear_advance = fields.Float()

    @api.multi
    def act_proposal(self):
        self.state = 'proposed'

    @api.multi
    def act_approval(self):
        self.state = 'approved'
        new_sequence_code = 'building.advance.rental.arrears'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        self.building_advance_id.arrear_advance = self.arrear_advance
        self.building_advance_id.available_advance = self.building_advance_id.advance_amount + self.building_advance_id.in_advance - self.building_advance_id.out_advance - self.building_advance_id.arrear_advance - self.building_advance_id.security_deposit_transfer
        self.owner_id.arrear_amount = self.owner_id.arrear_amount - self.arrear_advance
     
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
            self.arrear_advance = self.owner_id.arrear_amount
