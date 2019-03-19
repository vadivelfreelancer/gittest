from odoo import fields, models, api,_
from odoo.exceptions import UserError, ValidationError

class RentCreation(models.Model):
    _name = 'rent.creation'
    _description = 'Rent Creation'
    _rec_name = 'building_id'

    name = fields.Char(size=40)
    owner_id = fields.Many2one('pappaya.owner', string='Owner')
    partner_id = fields.Many2one('res.partner', string='Partner', related='owner_id.owner_id', store=True)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string='Building')
    floor_id = fields.Many2one('pappaya.floor', string='Floor')
    block_id = fields.Many2one('pappaya.block', string='Block')
    room_id = fields.Many2one('pappaya.building.room', string='Room')
    building_rent = fields.Float(string='Building Rent')
    building_maintenance_amt = fields.Float(string='Building Maintenance Amount')
    total_amt = fields.Float(string='Amount to be Paid')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('invoiced', 'Invoiced')], default='draft', string='State')
    is_confirm = fields.Boolean(string='Is confirmed', default=False)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    arrear_amount = fields.Float('Arrear Amount')

    @api.multi
    def action_confirm(self):
        new_sequence_code = 'rent.creation'
        self.name = self.env['ir.sequence'].next_by_code(new_sequence_code)
        self.write({'state': 'confirmed', 'is_confirm': True})

    @api.multi
    def create_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'rent.invoice.creation',
            'target': 'new',
            'context': {'active_ids': self.ids}
        }

    @api.onchange('total_amt')
    def onchange_total_amt(self):
        if self.total_amt:
            total = self.building_maintenance_amt + self.building_rent
            if self.total_amt < total:
                self.arrear_amount = self.total_amt
            
    @api.onchange('owner_id')
    def onchange_owner(self):
        if self.owner_id:
            self.building_rent = self.owner_id.rent
            self.building_maintenance_amt = self.owner_id.maintanance_amt
            total = self.building_maintenance_amt + self.building_rent
            existing_rent = self.search([('building_id','=',self.building_id.id),('branch_id','=',self.branch_id.id),('owner_id','=',self.owner_id.id),('state','!=','draft')])
            if existing_rent:
                self.total_amt = total - existing_rent.total_amt
            else:
                self.total_amt = total
