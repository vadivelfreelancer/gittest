from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

class PappayaRoomUsage(models.Model):
    _name = 'pappaya.room.usage'
    _description = 'Pappaya Room Usage'

    name = fields.Char('Name', size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    
    @api.constrains('name')
    def check_block_name(self):
        if self.name:
            if len(self.search([('name', '=', (self.name).strip()),('branch_id', '=', self.branch_id.id)])) > 1:
                raise ValidationError("Name already exists.")
