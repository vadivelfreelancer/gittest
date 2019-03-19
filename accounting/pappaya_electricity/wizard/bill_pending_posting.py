from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64

month_list = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),(5, 'May'), (6, 'June'), (7, 'July'),
              (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
year_list = [(2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), ]


class BillPendingPosting(models.Model):
    _name = 'bill.pending'

    month = fields.Selection(month_list, string='Month')
    year = fields.Selection(year_list, string='Year')
    division_id = fields.Many2one('electricity.division', string='Electricity Division', required=True)
    pending_bill = fields.One2many('pending.details', 'branch_id')

    @api.onchange('division_id')
    def onchange_division(self):
        if self.division_id:
            existing_details = self.search([('division_id','=',self.division_id.id),('year','=',self.year),('month','=',self.month)])
            if existing_details:
                raise ValidationError(_("Already Exists"))
            electricity_details = self.env['service.confirmation'].search([('division_id','=',self.division_id.id),('year','=',self.year),('month','=',self.month)])
            confirmation_details = electricity_details.mapped('confirmation_details')
            paid_lst = []
            for detail in confirmation_details:
                if detail.is_paid:
                    paid_lst.append(detail.service_number.service_number)
            posting_details = self.env['bill.posting'].search([('division_id','=',self.division_id.id),('year','=',self.year),('month','=',self.month)])
            filename = base64.b64decode(posting_details.excel_file)
            lines = filename.split(b'\n')
            lst = []
            for index, line in enumerate(lines):
                if not index == 0 and not line == b'':
                    lst.append(line.decode('ascii').split(','))
            vals = [(0, 0, {
                    'service_number':rec[0],
                    'opening_units':int(rec[1]),
                    'closing_units' : int(rec[2]),
                    'total_units':int(rec[3]),
                    'bill_amt':int(rec[4]),
                    'arriers_amt':int(rec[5]),
                    'acd_amt':int(rec[6]),
                    'fsa_amt':int(rec[7]),
                    'remarks':'SERVICE NOT FOUND',
                })for rec in lst if not rec[0] in paid_lst]
            self.pending_bill = vals

class BillPendingDetails(models.Model):
    _name = 'pending.details'

    bill_id = fields.Many2one('bill.pending')
    opening_units = fields.Integer(string='Opening Units', required=True)
    closing_units = fields.Integer(string='Closing Units')
    total_units = fields.Integer(string='Total Units')
    bill_amt = fields.Integer(string='Bill Amount')
    arriers_amt = fields.Integer(string='Arriers Amount')
    acd_amt = fields.Integer(string='ACD Amount')
    fsa_amt = fields.Integer(string='FSA Amount')
    remarks = fields.Char(string='Remarks')
    branch_id = fields.Many2one('operating.unit', string='Branch')
    service_number = fields.Char(string='Service Number')

