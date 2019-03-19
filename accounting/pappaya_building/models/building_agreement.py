from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

class BuildingAgreement(models.Model):
    _name = 'building.agreement'
    _rec_name = 'branch_id'

    branch_id = fields.Many2one('operating.unit', string="Branch")
    building_line_ids = fields.One2many('building.agreement.line', 'agreement_id', string='Building Agreement')
    building_capacity_ids = fields.One2many('building.capacity.line', 'agreement_id', string='Building Agreement')
    type = fields.Selection([('expiry_date', 'Agreement Expiry Date'), ('building_capacity', 'Building Capacity')], default='expiry_date', string='Type')

    @api.onchange('branch_id','type')
    def onchange_building(self):
        expiry_list, capacity_list = [],[]
        building_obj = self.env['pappaya.building'].search([('branch_id','=',self.branch_id.id)])
        if self.branch_id and self.type == 'expiry_date':
            for obj in building_obj:
                expiry_list.append((0, 0, {
                                        'agreement_id': self.id,
                                        'branch_id': obj.branch_id.id,
                                        'building_id': obj.id,
                                        'total_area': obj.building_total_area,
                                        'rent': obj.rent,
                                        'expiry_date': obj.rent_agrm_expiry_date}))
            self.building_line_ids = expiry_list
            if self.branch_id and len(self.building_line_ids) < 1:
                raise ValidationError(_("No Record Found"))
        if self.branch_id and self.type == 'building_capacity':
            for obj in building_obj:
                capacity_list.append((0, 0, {
                                        'agreement_id': self.id,
                                        'branch_id': obj.branch_id.id,
                                        'building_id': obj.id,
                                        'total_area': obj.building_total_area,
                                        'rent': obj.rent,
                                        'capacity': obj.student_capacity,
                                        'occupied': obj.student_occupied}))
            self.building_capacity_ids = capacity_list
            if self.branch_id and len(self.building_line_ids) < 1:
                raise ValidationError(_("No Record Found"))

class BuildingAgreementLine(models.Model):
    _name = 'building.agreement.line'

    agreement_id = fields.Many2one('building.agreement', string='Building Agreement')
    branch_id = fields.Many2one('operating.unit', string='Branch', related='agreement_id.branch_id')
    building_id = fields.Many2one('pappaya.building', string='Building')
    total_area = fields.Float(string='Total Area')
    rent = fields.Float(string='Rent')
    expiry_date = fields.Date(string='Agreement Expiry Date')
    filename = fields.Char(string='Filename',size=100)
    attachment = fields.Binary(string='Agreement Attachment', attachment=True)

class BuildingCapacityLine(models.Model):
    _name = 'building.capacity.line'

    agreement_id = fields.Many2one('building.agreement', string='Building Agreement')
    branch_id = fields.Many2one('operating.unit', string='Branch', related='agreement_id.branch_id')
    building_id = fields.Many2one('pappaya.building', string='Building')
    total_area = fields.Float(string='Total Area')
    rent = fields.Float(string='Rent')
    capacity = fields.Float(string='Capacity')
    occupied = fields.Integer(string='Occupied')
