from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError


month_list = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),(5, 'May'), (6, 'June'), (7, 'July'),
              (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
year_list = [(2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), ]

class ServiceUser(models.Model):
    _name = 'service.user'

    name = fields.Char(string='Service User', required=True)


class ElectricityDetails(models.Model):
    _name = 'electricity.details'
    _inherit = ['mail.thread']
    _rec_name = 'service_number'

    branch_id = fields.Many2one('operating.unit', string='Branch')
    building_id = fields.Many2one('pappaya.building', string='Building Name')
    floor_id = fields.Many2one('pappaya.floor', string='Floor')
    owner_id = fields.Many2one('pappaya.owner',string='Owner',)
    block_id = fields.Many2one('pappaya.block','Block')
    service_number = fields.Char(string='Service Number', required=True)
    billing_duration = fields.Selection([('monthly', 'Monthly'), ('bi_monthly', 'Bi Monthly'), ('quarterly', 'Quarterly'),
                                         ('half_yearly', 'Half Yearly')
                                         , ('yearly', 'Yearly')], string='Billing Duration', required=True)
    bill_due_gap = fields.Char(string='Bill due gap[Days]', required=True)
    service_user = fields.Many2one('service.user', string='Service User', required=True)
    state = fields.Selection([('draft', 'Draft'), ('zonal_approval', 'Zonal Approval'), ('rfo_approval', 'RFO Approval'),
                              ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancel', 'Cancelled')],
                             default="draft", string="State", track_visibility='onchange')
    active = fields.Boolean(string='Archive', default=True)
    ero = fields.Many2one('ero.details',string='ERO')
    division_id = fields.Many2one('electricity.division', string='Electricity Division')

    @api.multi
    def button_submit(self):
        self.write({'state': 'zonal_approval'})

    @api.multi
    def approval_by_zonal(self):
        self.write({'state': 'rfo_approval'})

    @api.multi
    def approval_by_rfo(self):
        self.write({'state': 'approved'})

    @api.multi
    def button_reject(self):
        self.write({'state': 'rejected'})

    @api.multi
    def button_cancel(self):
        self.write({'state': 'cancel'})

class ERODetails(models.Model):
    _name = 'ero.details'

    name = fields.Char()

class BranchFileNumber(models.Model):
    _name = 'branch.number'

    name = fields.Char(string='Branch File Number', required=True)


class SecurityDepositElectricity(models.Model):
    _name = 'security.deposit.electricity'
    _inherit = ['mail.thread']
    _rec_name = 'service_number'

    branch_id = fields.Many2one('operating.unit', string='Branch')
    service_number = fields.Many2one('electricity.details', string='Service Number')
    security_acd = fields.Selection([('security_deposit', 'Security Deposit'), ('acd', 'ACD')], string='ACD/Security Deposit Details',default ='security_deposit')
    building_id = fields.Many2one('pappaya.building', string='Building Name',)
    floor_id = fields.Many2one('pappaya.floor', string='Floor')
    deposit_amount = fields.Float(string='Deposit Amount')
    today_date = fields.Date(string='Date')
    branch_number_id = fields.Many2one('branch.number', string='Branch File Number')
    description = fields.Text(string='Description')
    state = fields.Selection([('draft', 'Draft'), ('co_approval', 'Co Approval'), ('approved', 'Approved'),
                              ('rejected', 'Rejected'), ('cancel', 'Cancelled')],
                             default="draft", string="State", track_visibility='onchange')

    @api.multi
    @api.onchange('service_number')
    def onchange_service_number(self):
        if self.service_number:
            existing_deposit = self.search([('branch_id','=',self.branch_id.id),('service_number','=',self.service_number.id),('security_acd','=',self.security_acd),('state','=','approved')])
            if existing_deposit:
                raise ValidationError(_("Security Deposit already Created"))
            self.building_id = self.service_number.building_id.id
            self.floor_id = self.service_number.floor_id.id

    @api.multi
    def approval_by_co(self):
        self.write({'state': 'co_approval'})

    @api.multi
    def security_button_done(self):
        self.write({'state': 'approved'})

    @api.multi
    def security_button_reject(self):
        self.write({'state': 'rejected'})

    @api.multi
    def security_button_cancel(self):
        self.write({'state': 'cancel'})


class ElectricityBillEntry(models.Model):
    _name = 'electricity.bill'
    _inherit = ['mail.thread']
    _rec_name = 'bill_number'

    branch_id = fields.Many2one('operating.unit', string='Branch')
    service_number = fields.Many2one('electricity.details', string='Service Number')
    owner_id = fields.Many2one('pappaya.owner',string='Owner Name')
    month = fields.Selection(month_list, string='Month')
    year = fields.Selection(year_list, string='Year')
    trans_date = fields.Date(string='Trans Date')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    bill_date = fields.Date(string='Bill Date')
    bill_due_date = fields.Date(string='Bill Due Date')
    bill_number = fields.Char(string='Bill Number')
    present_reading = fields.Float(string='Present Reading')
    previous_reading = fields.Float(string='Previous Reading')
    no_units = fields.Float(string='No Units', compute='compute_units')
    branch_number_id = fields.Many2one('branch.number', string='Branch File Number')
    bill_upload = fields.Binary(string='Electricity Bill Upload')
    bill_amount = fields.Float(string='Bill Amount',  store=True)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type',default='amt')
    discount_amount = fields.Float(string='Discount Amount',  store=True)
    acd = fields.Float(string='Additional Consumption Amount', store=True)
    bill_amount_after_discount = fields.Float(string='Bill Amount After Discount', compute='compute_discount_amount', readonly=True,  store=True)
    mis_amount = fields.Float(string='Miscellenius Amount', store=True)
    net_amount = fields.Float(string='Net Amount', compute='compute_net_amount', store=True)
    building_id = fields.Many2one('pappaya.building', string='Building')
    floor_id = fields.Many2one('pappaya.floor', string='Floor')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),('reversed', 'Reversed')],default="draft", string="State")

    @api.multi
    @api.onchange('service_number')
    def onchange_service_number_bill(self):
        if self.service_number:
            self.owner_id = self.service_number.owner_id
            self.building_id = self.service_number.building_id.id

    @api.depends('present_reading', 'previous_reading')
    def compute_units(self):
        for rec in self:
            rec.no_units = rec.present_reading - rec.previous_reading
            rec.bill_amount = rec.no_units

    @api.depends('bill_amount', 'discount_type', 'discount_amount')
    def compute_discount_amount(self):
        if self.discount_type == 'amt':
            self.bill_amount_after_discount = self.bill_amount - self.discount_amount
        if self.discount_type == '%':
            self.bill_amount_after_discount = self.bill_amount - self.bill_amount * (self.discount_amount/100)

    @api.depends('bill_amount_after_discount', 'acd', 'mis_amount')
    def compute_net_amount(self):
        if self.bill_amount_after_discount:
            self.net_amount = self.bill_amount_after_discount + self.acd + self.mis_amount

    @api.model
    def create(self, vals):
        if 'acd' in vals:
            deposit_obj = self.env['security.deposit.electricity']
            existing_deposit = deposit_obj.search([('branch_id','=',self.branch_id.id),('service_number','=',self.service_number.id),('security_acd','=','acd')])
            if existing_deposit:
                existing_deposit.deposit_amount += vals.get('acd',0.0)
            else:
                floor = self.env['pappaya.floor'].browse(vals.get('floor_id',False))
                value = {
                    'branch_id':vals.get('branch_id',False),
                    'service_number': vals.get('service_number',False),
                    'security_acd':'acd',
                    'building_id':floor.building_id.id or False,
                    'floor_id':floor.id or False,
                    'deposit_amount':vals.get('acd',0.0),
                    'today_date':vals.get('bill_date',False),
                    'branch_number_id':vals.get('branch_number_id',False),
                    'description':'Additional Consumption Amount',
                    'state':'draft',
                    }
                deposit_obj.create(value)
        return super(ElectricityBillEntry, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'acd' in vals:
            deposit_obj = self.env['security.deposit.electricity']
            existing_deposit = deposit_obj.search([('branch_id','=',self.branch_id.id),('service_number','=',self.service_number.id),('security_acd','=','acd')])
            if existing_deposit:
                existing_deposit.deposit_amount = vals.get('acd',0.0)
            else:
                floor = self.env['pappaya.floor'].browse(vals.get('floor_id',False))
                value = {
                    'branch_id':vals.get('branch_id',False),
                    'service_number': vals.get('service_number',False),
                    'security_acd':'acd',
                    'building_id':floor.building_id.id or False,
                    'floor_id':floor.id or False,
                    'deposit_amount':vals.get('acd',0.0),
                    'today_date':vals.get('bill_date',False),
                    'branch_number_id':vals.get('branch_number_id',False),
                    'description':'Additional Consumption Amount',
                    'state':'draft',
                    }
                deposit_obj.create(value)
        return super(ElectricityBillEntry, self).write(vals)

    @api.multi
    def button_confirm(self):
        self.write({'state': 'confirm'})
        

class ElectricityMeterReading(models.Model):
    _name = 'meter.reading'
    _inherit = ['mail.thread']
    _rec_name = 'service_number'

    branch_id = fields.Many2one('operating.unit', string='Branch')
    building_id = fields.Many2one('pappaya.building', string='Building Name')
    service_number = fields.Many2one('electricity.details', string='Service Number')
    reading_date = fields.Date(string='Date')
    kwh_opening = fields.Integer(string='KWH-Opening')
    kwh_closing = fields.Integer(string='KWH-Closing')
    kwh_units = fields.Integer(string='KWH-Units')
    kvah_opening = fields.Integer(string='KVAH-Opening')
    kvah_closing = fields.Integer(string='KVAH-Closing')
    kvah_units = fields.Integer(string='KVAH-Units')
    state = fields.Selection([('draft', 'Draft'), ('generated', 'generated')],default='draft')
    is_latest = fields.Boolean()

    @api.onchange('kwh_opening','kwh_closing')
    def onchange_kwh(self):
        if self.kwh_opening > 0 or self.kwh_closing > 0:
            self.kwh_units =  self.kwh_closing - self.kwh_opening
        
    @api.onchange('kvah_opening','kvah_closing')
    def onchange_kvah(self):
        if self.kvah_opening > 0 or self.kvah_closing > 0:
            self.kvah_units =  self.kvah_closing - self.kvah_opening

    @api.multi
    def generate_meter(self):
        previous_reading = self.search([('state','=','generated'),('service_number','=',self.service_number.id),('is_latest','=',True)])
        if previous_reading:
            for rec in previous_reading:
                rec.is_latest = False
        self.state = 'generated'
        self.is_latest = True
        
    @api.onchange('service_number')
    def onchange_service_number(self):
        if self.service_number:
            previous_reading = self.search([('state','=','generated'),('service_number','=',self.service_number.id),('is_latest','=',True)], order="id desc",limit=1)
            if previous_reading:
                self.kwh_opening = previous_reading.kwh_closing
                self.kvah_opening = previous_reading.kvah_closing
 

class ElectricityDivision(models.Model):
    _name = 'electricity.division'

    name = fields.Char(string='Electricity Division', required=True)


class BillPosting(models.Model):
    _name = 'bill.posting'
    _inherit = ['mail.thread']
    _rec_name = 'division_id'
 
    branch_id = fields.Many2one('operating.unit', string='Branch')
    division_id = fields.Many2one('electricity.division', string='Electricity Division', required=True)
    month = fields.Selection(month_list, string='Month')
    year = fields.Selection(year_list, string='Year')
    excel_file = fields.Binary(string='Excel File')


class BillPostingLock(models.Model):
    _name = 'bill.posting.lock'
    _inherit = ['mail.thread']

    month = fields.Selection(month_list, string='Month')
    year = fields.Selection(year_list, string='Year')
    locked_electricity_division = fields.One2many('locked.electricity.division', 'bill_id')
    division_id = fields.Many2one('electricity.division', string='Electricity Division', required=True)

    @api.onchange('division_id')
    def onchange_division(self):
        if self.division_id:
            existing_details = self.search([('division_id','=',self.division_id.id),('year','=',self.year),('month','=',self.month)])
            if existing_details:
                raise ValidationError(_("Already Exists"))
            electricity_details = self.env['service.confirmation'].search([('division_id','=',self.division_id.id),('year','=',self.year),('month','=',self.month)])
            paid = electricity_details.mapped('confirmation_details')
            vals = [(0, 0, {
                        'division_id':self.division_id.id,
                        'sl_no':index+1,
                        'status':'Locked',
                        'service_number':line.service_number.id,
                    }) for index, line in enumerate(paid) if line.is_paid]
            self.locked_electricity_division = vals


class LockedElectricityDivision(models.Model):
    _name = 'locked.electricity.division'

    bill_id = fields.Many2one('locked.electricity.division')
    sl_no = fields.Char(string='Sl No')
    division_id = fields.Many2one('electricity.division', string='Electricity Division', required=True)
    status = fields.Char(string='Status')
    service_number = fields.Many2one('electricity.details', string='Service Number')


class AdvancePayment(models.Model):
    _name = 'advance.payment'
    _inherit = ['mail.thread']

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    date = fields.Date(string='Date', default=fields.Date.today)
    proposal_type = fields.Selection([('travelling', 'Travelling'), ('purchase_advance', 'Purchase Advance'),
                                      ('campaigning', 'Campaigning'), ('advance_to_creditor', 'Advance To Creditor')
                                      , ('advance_to_debtor', 'Advance To Debtor'),
                                      ('general_advance', 'General Advance')
                                      , ('electricity_advance', 'Electricity Advance')],
                                                 string='Proposal', required=True,default="electricity_advance")
    amount_redeem = fields.Selection([('amount', 'Amount'), ('redeem_amount', 'Redeem Amount')],
                                                  required=True, default='amount')
    electricity_advance = fields.Many2one('electricity.division', string='Electricity Advance')
    previous_advance = fields.Float(string='Previous Advance Amount')
    amount = fields.Float(string='Amount')
    narration = fields.Text(string='Narration')
 
    @api.onchange('electricity_advance')
    def onchange_electricity_advance(self):
        if self.electricity_advance:
            existing = self.search([('branch_id','=',self.branch_id.id),('proposal_type','=',self.proposal_type),('electricity_advance','=',self.electricity_advance.id)])
            if existing:
                prev_amt = 0.0
                for rec in existing:
                    prev_amt += rec.amount
                self.previous_advance = prev_amt
            else:
                self.previous_advance = 0.0

class DepositCheckPreparation(models.Model):
    _name = 'deposit.cheque'
    _inherit = ['mail.thread']

    cash_bank = fields.Selection([('cash', 'Cash'), ('bank', 'Bank')], required=True)
    bank = fields.Char(string='Bank')
    trans_date = fields.Date(string='Trans Date')
    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    bank_balance = fields.Float(string='Bank Balance')
    cheque_lot = fields.Char(string='Cheque Lot')
    cheque_date = fields.Date(string='Cheque Date')
    dd_bank_cheque = fields.Selection([('dd_cheques', 'DD Cheques'), ('bank_cheques', 'Bank Cheques')], string='Cheque Type', required=True)
    cheque_no = fields.Char(string='Cheque Number')
    payee_name = fields.Char(string='Payee Name')
    amount = fields.Float(string='Amount')
