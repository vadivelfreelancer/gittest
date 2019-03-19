from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

class RentalAgreement(models.Model):
    _name = 'rental.agreement'
    _rec_name = 'branch_id'

    branch_id = fields.Many2one('operating.unit', string="Branch")
    rental_line_ids = fields.One2many('rental.agreement.line', 'agreement_id', string='Rental Agreement')

    @api.onchange('branch_id')
    def onchange_rental(self):
        rent_list = []
        building_obj = self.env['pappaya.building'].search([('branch_id','=',self.branch_id.id)])
        for obj in building_obj:
            rent_list.append((0, 0, {
                                    'agreement_id': self.id,
                                    'branch_id': obj.branch_id.id,
                                    'building_id': obj.id,
                                    'total_area': obj.building_total_area,
                                    'rent': obj.rent,
                                    'expiry_date': obj.rent_agrm_expiry_date}))
        self.rental_line_ids = rent_list
        if self.branch_id and len(self.rental_line_ids) < 1:
            raise ValidationError(_("No Record Found"))

class RentalAgreementLine(models.Model):
    _name = 'rental.agreement.line'

    agreement_id = fields.Many2one('rental.agreement', string='Rental Agreement')
    branch_id = fields.Many2one('operating.unit', string='Branch', related='agreement_id.branch_id')
    building_id = fields.Many2one('pappaya.building', string='Building')
    total_area = fields.Float(string='Total Area')
    rent = fields.Float(string='Rent')
    expiry_date = fields.Date(string='Expiry Date')
    filename = fields.Char(string='Filename',size=100)
    attachment = fields.Binary(string='Agreement Attachment', attachment=True)
