from odoo import fields, models, api

class PappayaBuildingEnhancement(models.Model):
    _name = 'pappaya.building.enhancement'
    _description = 'Pappaya Building Enhancement'
    _rec_name = 'building_id'

    name = fields.Char('Name', size=40)
    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_id = fields.Many2one('pappaya.building', string='Building')
    present_building_rent = fields.Float('Present Building Rent')
    building_new_rent = fields.Float(string='Building New Rent')
    present_building_maintenance = fields.Float(string='Present Building Maintenance')
    building_new_maintenance = fields.Float(string='Building New Maintenance')
    effect_month = fields.Selection([(1, '01 January'), (2, '02 Febuary'), (3, '03 March'), (4, '04 April'), (5, '05 May'),
                                     (6, '06 June'),(7, '07 July'), (8, '08 August'), (9, '09 September'), (10, '10 October'),
                                     (11, '11 November'),(12, '12 December')], string='Month')
    date = fields.Date('Date')
    proposed_by = fields.Char('Proposed By',size=100)

    @api.multi
    @api.onchange('building_id')
    def onchange_rent(self):
        self.present_building_rent = self.building_id.rent
        self.present_building_maintenance = self.building_id.maintenance_amount

    @api.model
    def create(self, vals):
        if 'building_id' in vals:
            building_id = self.env['pappaya.building'].search([('id', '=', vals['building_id'])])
            if building_id and 'building_new_rent' in vals :
                building_id.write({'rent':vals['building_new_rent']})
            if building_id and 'building_new_maintenance' in vals:
                building_id.write({'maintenance_amount':vals['building_new_maintenance']})
        return super(PappayaBuildingEnhancement, self).create(vals)

    @api.multi
    def write(self, vals):
        if self.building_id and self.building_new_rent:
            self.building_id.write({'rent': vals['building_new_rent']})
        if self.building_id and self.building_new_maintenance:
            self.building_id.write({'maintenance_amount': vals['building_new_maintenance']})
        return super(PappayaBuildingEnhancement, self).write(vals)


