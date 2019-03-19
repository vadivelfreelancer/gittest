from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

month_list = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),(5, 'May'), (6, 'June'), (7, 'July'),
              (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
year_list = [(2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), ]

class ServiceNumberConfirmation(models.Model):
    _name = 'service.confirmation'
    _rec_name = 'division_id'

    branch_id = fields.Many2one('operating.unit', string='Branch')
    division_id = fields.Many2one('electricity.division', string='Electricity Division')
    month = fields.Selection(month_list, string='Month')
    year = fields.Selection(year_list, string='Year')
    confirmation_details = fields.One2many('confirmation.details', 'confirmation_id')

    @api.onchange('division_id')
    def onchange_division(self):
        if self.division_id:
            existing_details = self.search([('branch_id','=',self.branch_id.id),('division_id','=',self.division_id.id),('year','=',self.year),('month','=',self.month)])
            if existing_details:
                raise ValidationError(_("Already Exists"))
            electricity_details = self.env['electricity.details'].search([('division_id','=',self.division_id.id),('branch_id','=',self.branch_id.id)])  
            vals = [(0, 0, {
                    'branch_id':self.branch_id.id,
                    'confirmation_id':self.id,
                    'is_paid':False,
                    'service_number':rec.id,
                    'building_id':rec.building_id.id,
                }) for rec in electricity_details]
            self.confirmation_details = vals
            
class MeterReadingLo(models.Model):
    _name = 'confirmation.details'

    building_id = fields.Many2one('pappaya.building', string='Building Name')
    service_number = fields.Many2one('electricity.details', string='Service Number')
    is_paid = fields.Boolean(string='Is Paid')
    confirmation_id = fields.Many2one('service.confirmation')
    branch_id = fields.Many2one('operating.unit', string='Branch')

