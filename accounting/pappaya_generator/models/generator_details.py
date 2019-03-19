from odoo import models, fields, api


class GeneratorCompanyDetails(models.Model):
    _name = 'generator.company.details'

    name = fields.Char(string='Company Name', required=True)
    address1 = fields.Text(string='Address1', required=True)
    address2 = fields.Text(string='Address2', required=True)


class GeneratorCapacityDetails(models.Model):
    _name = 'generator.capacity.details'

    name = fields.Char(string='Capacity', required=True)
    capacity = fields.Char(string='Description', required=True)


class GeneratorModelDetails(models.Model):
    _name = 'generator.model.details'
    _rec_name = 'generator_name'

    generator_name = fields.Char(string='Name', required=True)
    capacity = fields.Many2one('generator.capacity.details',string='Capacity', required=True)
    fuel_capacity = fields.Char(string='Fuel Tank Capacity', required=True)
    description = fields.Char(string='Description', required=True)


class PetroCards(models.Model):
    _name = 'petro.cards'
    _rec_name = 'card_id'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    generator_name_id = fields.Many2one('generator.model.details', string='Generator', required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True,
                                domain="[('supplier', '=', True)]")
    card_id = fields.Char(string='Card Id', required=True)


class GeneratorBillEntryDetails(models.Model):
    _name = 'generator.bill.details'
    _rec_name = 'company'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    building_id = fields.Many2one('pappaya.building', string='Building Name', required=True,
                                  domain="[('branch_id', '=', branch_id)]")
    company = fields.Many2one('generator.company.details', string='Company', required=True)
    capacity_id = fields.Many2one('generator.capacity.details', string='Capacity', required=True)
    model_id = fields.Many2one('generator.model.details', string='Model', required=True)
    fuel_capacity = fields.Char(string='Fuel Tank Capacity', required=True)
    fuel_type = fields.Selection([('petrol', 'Petrol'), ('diesel', 'Diesel')],
                                 string='Fuel Type', required=True)
    year_purchase = fields.Char(string='Year Of Purchase', required=True)
    consumption = fields.Char(string='Consumption Per Hour', required=True)
    is_rent = fields.Boolean(string='Is Rent', required=True)
    rent_base = fields.Selection([('daily', 'Daily'), ('month', 'Month'), ('yearly', 'Yearly')],
                                 string='Rent Base')
    rent = fields.Float(string='Rent')
    engine_no = fields.Char(string='Engine Number', required=True)
    alternative_no = fields.Char(string='Alternative Number', required=True)
    description = fields.Text(string='Description', required=True)
    state = fields.Selection([('draft', 'Draft'), ('approval', 'Approval'),('approved', 'Approved')],default="draft",
                              string="State", track_visibility='onchange')

    @api.multi
    def button_submit(self):
        self.write({'state': 'approval'})

    @api.multi
    def approval(self):
        self.write({'state': 'approved'})

class FuelBillTransaction(models.Model):
    _name = 'fuel.bill.transaction'
    _rec_name = 'bill_no'

    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    vendor = fields.Many2one('res.partner', string='Vendor', required=True,  domain="[('supplier', '=', True)]")
    generator_name_id = fields.Many2one('generator.model.details', string='Generator', required=True)
    fuel_type = fields.Selection([('petrol', 'Petrol'), ('diesel', 'Diesel')],
                                 string='Fuel Type', required=True)
    no_litters = fields.Char(string='No Of Litters', required=True)
    bill_amount = fields.Float(string='Bill Amount', required=True)
    bill_no = fields.Char(string='Bill Number', required=True)
    bill_date = fields.Date(string='Bill Date', required=True)
    bill_due_date = fields.Date(string='Bill Due Date', required=True)
    cash_credit = fields.Selection([('cash', 'Cash'), ('credit', 'Credit')],
                                 string='Cash Or Credit', required=True)
    narration = fields.Text(string='Narration', required=True)
    state = fields.Selection([('draft', 'Draft'), ('approval', 'Approval'),('approved', 'Approved')],default="draft",
                              string="State", track_visibility='onchange')

    @api.multi
    def button_submit(self):
        self.write({'state': 'approval'})

    @api.multi
    def approval(self):
        self.write({'state': 'approved'})

class BillAdvanceProposal(models.Model):
    _name = 'advance.bill.proposal'
    _rec_name = 'vendor'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    category = fields.Selection([('travelling', 'Travelling'), ('purchase_advance', 'Purchase Advance')
                                 , ('campaigning', 'Campaigning'), ('advance_to_creditor', 'Advance To Creditor'),
                                 ('advance_to_Debtor', 'Advance To Debtor')
                                 , ('general_advance', 'General Advance'), ('electricity_advance', 'Electricity Advance')],
                                 string='Categories', required=True,default="advance_to_creditor")
    amount_redeem = fields.Selection([('amount', 'Amount'), ('redeem_amount', 'Redeem Amount')], required=True,default="amount")
    vendor = fields.Many2one('res.partner', string='Vendor', required=True,  domain="[('supplier', '=', True)]")
    date = fields.Date(string='Date')
    pvs_advance_amt = fields.Float(string='Previous Advance Amount', required=True)
    po_number = fields.Many2one('purchase.order', string='PO Number', required=True)
    amount = fields.Float(string='Amount', required=True)

    @api.onchange('vendor')
    def onchange_vendor(self):
        if self.vendor:
            prev_ids = self.search([('vendor','=',self.vendor.id),('branch_id','=',self.branch_id.id),('category','=',self.category)])
            if prev_ids:
                amt = 0.0
                for rec in prev_ids:
                    amt +=rec.amount
                self.pvs_advance_amt = amt
            po_orders = self.env['purchase.order'].search([('partner_id','=',self.vendor.id),('state','=','purchase')])
            return {'domain': {'po_number': [('id', 'in', po_orders.ids)]}}
        

    @api.onchange('po_number')
    def onchange_po_number(self):
        if self.po_number:
            self.amount = self.po_number.amount_total + self.pvs_advance_amt or 0.0
           
class GeneratorConsumption(models.Model):
    _name = 'generator.consumption'
    _rec_name = 'generator_name_id'

    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    generator_name_id = fields.Many2one('generator.model.details', string='Generator', required=True)
    running_date = fields.Date(string='Running Date', required=True)
    starting_time = fields.Float(string='Start Time')
    ending_time = fields.Float(string='Stop Time')


class PaymentDetails(models.Model):
    _name = 'payment.details'
    _rec_name = 'vendor'

    vendor = fields.Many2one('res.partner', string='Vendor', required=True, domain="[('supplier', '=', True)]")
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    bill_amount = fields.Float(string='Bill Amount')
    advance_amount = fields.Float(string='Advance Amount')
    bill_details = fields.One2many('bills.details', 'bill_id')
    state = fields.Selection(
        [('account_verification', 'Account Verification'), ('rfo_verification', 'Rfo Verification'),
         ('advance_adjustment', 'Advance Adjustment'),
         ('forward_treasury', 'Forward To Treasury'), ('done', 'Done'), ('cancel', 'Cancel') ], default="account_verification", string="State", track_visibility='onchange')
    is_service = fields.Boolean()
    

    @api.onchange('vendor')
    def onchange_vendor(self):
        if self.vendor:
            advances = self.env['advance.bill.proposal'].search([('vendor','=',self.vendor.id)])
            amt = 0.0
            bill_amt = 0.0
            for advance in advances:
                amt += advance.amount
            self.advance_amount = amt
            services = self.env['service.details'].search([('vendor','=',self.vendor.id)])
            for rec in services:
                bill_amt += rec.total_bill_amount
            self.bill_amount = bill_amt
            vals = [(0, 0, {
                        'bill_id':self.id,
                        'sl_no':index+1,
                        'branch_id':line.branch_id.id,
                        'invoice_number':line.invoice_bill_no,
                        'bill_no':line.invoice_bill_no,
                        'bill_date':line.invoice_date,
                        'bill_due_date':line.bill_due_date,
                        'bill_amount':line.total_bill_amount,
                    }) for index, line in enumerate(services)]
            self.bill_details = vals      

    @api.multi
    def account_verification_button(self):
        self.write({'state': 'rfo_verification'})


    @api.multi
    def rfo_verification_button(self):
        self.write({'state': 'advance_adjustment'})

    @api.multi
    def advance_adjustment_button(self):
        self.write({'state': 'forward_treasury'})

    @api.multi
    def forward_to_treasury_button(self):
        self.write({'state': 'done'})

    @api.multi
    def button_cancel(self):
        self.write({'state': 'cancel'})


class BillsDetails(models.Model):
    _name = 'bills.details'

    bill_id = fields.Many2one('payment.details')
    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    invoice_number = fields.Char(string='Invoice Number')
    bill_no = fields.Char(string='Bill Number')
    bill_date = fields.Char(string='Bill Date')
    bill_due_date = fields.Date(string='Bill Due Date')
    bill_amount = fields.Float(string='Bill Amount')
    voucher_no = fields.Char(string='Voucher Number')
    sno = fields.Integer()

