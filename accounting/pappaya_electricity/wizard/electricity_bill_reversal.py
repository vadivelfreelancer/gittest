from odoo import models, fields, api

month_list = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),(5, 'May'), (6, 'June'), (7, 'July'),
              (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
year_list = [(2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), ]


class BillReversal(models.Model):
    _name = 'bill.reversal'

    electricity_communication = fields.Selection([('electricity', 'Electricity'), ('communication', 'Communication')],
                                                string='Electricity Or Communication', required=True,default='electricity')
    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    service_number = fields.Many2one('electricity.details', string='Service Number', required=True,
                                     domain="[('branch_id', '=', branch_id), ('state', '=', 'approved')]")
    month = fields.Selection(month_list, string='Month')
    year = fields.Selection(year_list, string='Year')
    financial_year = fields.Char(string='Financial Year', required=True)
    bill_no = fields.Char(string='Bill Number', readonly=True)
    bill_date = fields.Char(string='Bill Date', readonly=True)
    bill_due_date = fields.Char(string='Bill Due Date', readonly=True)
    bill_amount = fields.Float(string='Bill Amount', readonly=True)
    discount_amt = fields.Float(string='Discount Amount', readonly=True)
    after_discount_amt = fields.Float(string='After Discount Amount', readonly=True)
    st_amt = fields.Float(string='ST Amount', readonly=True)
    sd_amt = fields.Float(string='SD Amount', readonly=True)
    miss_amt = fields.Float(string='Miscellaneous Amount', readonly=True)
    bill_total_amt = fields.Float(string='Bill Total Amount', readonly=True)
    tds_amt = fields.Char(string='TDS Amount', readonly=True)
    net_due_amount = fields.Float(string='Net Due Amount', readonly=True)
    paid_amount = fields.Float(string='Paid Amount', readonly=True)
    balance_amount = fields.Float(string='Balance Amount', readonly=True)
    approve_date = fields.Char(string='Approve Date', readonly=True)
    narration = fields.Text(string='Narration', readonly=True)
    date = fields.Date(string='Date', required=True)
    description = fields.Text(string='Narration', required=True)
    module_ledger = fields.Selection([('only_module', 'Only Module'), ('both_module_ledger', 'Both Module And Ledger')],
                                                 required=True)
    state = fields.Selection([('draft', 'Draft'), ('reversed', 'Reversed')],default="draft", string="State", track_visibility='onchange')
    
    @api.onchange('service_number')
    def onchange_service_number(self):
        if self.service_number:
            bill = self.env['electricity.bill'].search([('service_number','=',self.service_number.id),('branch_id','=',self.branch_id.id),('month','=',self.month),('year','=',self.year),('state','=','confirm')])
            if bill:
                self.bill_no = bill.bill_number
                self.bill_date = bill.bill_date
                self.bill_due_date = bill.bill_due_date
                self.bill_total_amt = bill.net_amount
                self.balance_amount = self.bill_total_amt - self.paid_amount
                self.date = bill.trans_date
                
    @api.multi
    def button_reversed(self):
        self.write({'state': 'reversed'})
        bill = self.env['electricity.bill'].search([('service_number','=',self.service_number.id),('branch_id','=',self.branch_id.id),('month','=',self.month),('year','=',self.year),('state','=','confirm')])
        bill.write({'state': 'reversed'})

