from odoo import models, fields, api


month_list = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),(5, 'May'), (6, 'June'), (7, 'July'),
              (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
year_list = [(2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), ]


class MaterialUser(models.Model):
    _name = 'material.user'

    name = fields.Char(string='Material User', required=True)


class ConnectionType(models.Model):
    _name = 'connection.type'

    name = fields.Char(string='Connection Type', required=True)


class ServiceProvider(models.Model):
    _name = 'service.provider'

    name = fields.Char(string='Service Provider', required=True)


class CommunicationDetails(models.Model):
    _name = 'communication.details'
    _rec_name = 'communication_no'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    building_id = fields.Many2one('pappaya.building', string='Building Name', domain="[('branch_id', '=', branch_id)]",
                                  required=True)
    floor_id = fields.Many2one('pappaya.floor', string='Floor', domain="[('building_id', '=', building_id)]", required=True)
    owner_name = fields.Many2one("pappaya.owner", string='Owner Name')
    communication_no = fields.Char(string='Communication Number', required=True)
    connection_type = fields.Many2one('connection.type', string='Connection Type', required=True)
    billing_duration = fields.Selection(
        [('monthly', 'Monthly'), ('bi_monthly', 'Bi Monthly'), ('quarterly', 'Quarterly'),
         ('half_yearly', 'Half Yearly')
            , ('yearly', 'Yearly')],
        string='Billing Duration')
    bill_due_gap = fields.Char(string='Bill due gap[Days]', required=True)
    service_provider = fields.Many2one('service.provider', string='Service Provider', required=True)
    state = fields.Selection([('draft', 'Draft'), ('zonal_approval', 'Zonal Approval'), ('rfo_approval', 'RFO Approval'),
                              ('approved', 'Approved'), ('cancel', 'Cancelled'),
                              ('rejected', 'Rejected')], default="draft", string="State")
    tds_amount = fields.Float(string='TDS Amount', required=True)
    active = fields.Boolean(string='Archive', default=True)
    transfer_branch = fields.Many2one('operating.unit', string='Transfer From Branch')
    transfer_date = fields.Date(string='Transfer Date')

    @api.multi
    def communication_button_submit(self):
        self.write({'state': 'zonal_approval'})

    @api.multi
    def communication_approval_by_zonal(self):
        self.write({'state': 'rfo_approval'})

    @api.multi
    def communication_approval_by_rfo(self):
        self.write({'state': 'approved'})

    @api.multi
    def communication_button_reject(self):
        self.write({'state': 'rejected'})

    @api.multi
    def communication_button_cancel(self):
        self.write({'state': 'cancel'})


class CommunicationSecurity(models.Model):
    _name = 'communication.security'
    _inherit = ['mail.thread']
    _rec_name = 'communication_number'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    communication_number = fields.Many2one('communication.details', string='Communication Number', required=True,
                                           domain="[('branch_id', '=', branch_id), ('state', '=', 'approved')]")
    building_id = fields.Many2one('pappaya.building', string='Building Name', required=True,
                                  domain="[('branch_id', '=', branch_id)]")
    floor_id = fields.Many2one('pappaya.floor', string='Floor', domain="[('building_id', '=', building_id)]", required=True)
    deposit_amount = fields.Float(string=' Security Deposit Amount', required=True)
    today_date = fields.Date(string='Date', required=True)
    branch_number_id = fields.Many2one('branch.number', string='Branch File Number', required=True)
    description = fields.Text(string='Description', required=True)
    state = fields.Selection([('draft', 'Draft'), ('co_approval', 'Co Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancel', 'Cancelled')], default="draft", string="State", track_visibility='onchange')

    @api.multi
    @api.onchange('communication_number')
    def onchange_service_number(self):
        if self.communication_number:
            self.building_id = self.communication_number.building_id.id
            self.floor_id = self.communication_number.floor_id.id

    @api.multi
    def communication_approval_by_co(self):
        self.write({'state': 'co_approval'})

    @api.multi
    def communication_security_button_done(self):
        self.write({'state': 'approved'})

    @api.multi
    def communication_security_button_reject(self):
        self.write({'state': 'rejected'})

    @api.multi
    def communication_security_button_cancel(self):
        self.write({'state': 'cancel'})


class CommunicationBillEntry(models.Model):
    _name = 'communication.bill'
    _inherit = ['mail.thread']
    _rec_name = 'bill_number'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    connection_type = fields.Many2one('connection.type', string='Connection Type', required=True)
    communication_number = fields.Many2one('communication.details', string='Communication Number', required=True,
                                     domain="[('branch_id', '=', branch_id), ('state', '=', 'approved')]")
    owner_name = fields.Many2one("pappaya.owner", string='Owner Name')
    month = fields.Selection(month_list, string='Month')
    year = fields.Selection(year_list, string='Year')
    trans_date = fields.Date(string='Trans Date', required=True)
    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    bill_date = fields.Date(string='Bill Date', required=True)
    bill_due_date = fields.Date(string='Bill Due Date', required=True)
    bill_number = fields.Char(string='Bill Number', required=True)
    branch_number_id = fields.Many2one('branch.number', string='Branch File Number', required=True)
    bill_upload = fields.Binary(string='Communication Bill Upload')
    bill_amount = fields.Float(string='Bill Amount',  store=True)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type',default="amt")
    discount_amount = fields.Float(string='Discount Amount',  store=True)
    bill_amount_after_discount = fields.Float(string='Bill Amount After Discount',
                                              compute='compute_communication_discount_amount',
                                              readonly=True, store=True)
    st_sbc_kkc = fields.Float(string='ST + SBC + KKC  ', store=True)
    total_bill_amount = fields.Float(string='Total Bill Amount', compute='compute_total_bill_amount', readonly=True,  store=True)
    tds = fields.Float(string='TDS', store=True)
    mis_amount = fields.Float(string='Miscellenius Amount', store=True)
    net_amount = fields.Float(string='Net Due Amount', compute='compute_net_due_amount', store=True)
    state = fields.Selection([('draft', 'Draft'), ('bill_created', 'Bill Created')], default="draft", string="State", track_visibility='onchange')

    @api.multi
    @api.onchange('communication_number')
    def onchange_communication_number_bill(self):
        if self.communication_number:
            self.owner_name = self.communication_number.owner_name.id

    @api.multi
    def bill_created(self):
        self.write({'state': 'bill_created'})
        
    @api.depends('bill_amount', 'discount_type', 'discount_amount')
    def compute_communication_discount_amount(self):
        if self.discount_type == 'amt':
            self.bill_amount_after_discount = self.bill_amount - self.discount_amount
        if self.discount_type == '%':
            self.bill_amount_after_discount = self.bill_amount - self.bill_amount * (self.discount_amount / 100)

    @api.depends('bill_amount_after_discount', 'tds', 'st_sbc_kkc', 'mis_amount')
    def compute_total_bill_amount(self):
        if self.bill_amount_after_discount:
            self.total_bill_amount = self.bill_amount_after_discount + self.st_sbc_kkc

    @api.depends('bill_amount_after_discount', 'tds', 'st_sbc_kkc', 'mis_amount')
    def compute_net_due_amount(self):
        if self.total_bill_amount:
            self.net_amount = self.total_bill_amount + self.tds + self.mis_amount


class CommunicationDepositCheckPreparation(models.Model):
    _name = 'communication.deposit.cheque'
    _inherit = ['mail.thread']

    bank = fields.Char(string='Bank')
    trans_date = fields.Date(string='Trans Date')
    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    bank_balance = fields.Float(string='Bank Balance')
    cheque_lot = fields.Char(string='Cheque Lot')
    cheque_date = fields.Date(string='Cheque Date')
    dd_bank_cheque = fields.Selection([('dd_cheques', 'DD Cheques'), ('bank_cheques', 'Bank Cheques'),
                                       ('imul_pay', 'iMulPay')], required=True)
    cheque_no = fields.Char(string='Cheque Number')
    payee_name = fields.Char(string='Payee Name')
    amount = fields.Float(string='Amount')
    month = fields.Selection(month_list, string='Month')
    year = fields.Selection(year_list, string='Year')
    centrex_non_centrex = fields.Selection([('centrex_numbers', 'Centrex Numbers'),
                                            ('non_centrex_numbers', 'Non Centrex Numbers')],
                                           string='Centrex or Non Centrex', required=True)
    centrex = fields.Char(string='Centrex')


class CommunicationGroupNumbersMapping(models.Model):
    _name = 'communication.mapping'
    _inherit = ['mail.thread']

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    group_mapping_ids = fields.One2many('group.mapping', 'mapping_id')
    communication = fields.Char(string='Communication')
    payroll_branch = fields.Many2one('operating.unit', string='Payroll Branch')
    employee = fields.Char(string='Employee')
    type = fields.Char(string='Payment Type')
    payment = fields.Char(string='Payment Amount')
    state = fields.Selection([('draft', 'Draft'), ('mapped', 'Group Mapped')], default="draft", string="State", track_visibility='onchange')

    @api.multi
    def group_communication_mapping(self):
        if self.group_mapping_ids:
            self.state = 'mapped'
            for line in self.group_mapping_ids:
                line.employee_name.alternate_mobile = line.communication_number.communication_no

class GroupNumbersMapping(models.Model):
    _name = 'group.mapping'

    mapping_id = fields.Many2one('communication.mapping')
    sl_no = fields.Char(string='Sl No')
    communication_number = fields.Many2one('communication.details', string='Communication Number', required=True)
    employee_name = fields.Many2one('hr.employee',string='Employee Name')
    mobile_payment_type = fields.Char(string='Mobile Payment Type')
    payment_amount = fields.Float(string='Payment Amount')
