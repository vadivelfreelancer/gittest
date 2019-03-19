from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

month_list = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),(5, 'May'), (6, 'June'), (7, 'July'),
              (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]

class VehicleTypeEntry(models.Model):
    _name = 'vehicle.type'

    name = fields.Char(string='Vehicle Name', required=True)
    description = fields.Char(string='Description')


class VehicleFuelType(models.Model):
    _name = 'fuel.type'

    name = fields.Char(string='Fuel Type', required=True)
    description = fields.Char(string='Description')


class VehicleMake(models.Model):
    _name = 'vehicle.make'

    name = fields.Char(string='Vehicle Maker', required=True)
    description = fields.Char(string='Description')


class VehicleColor(models.Model):
    _name = 'vehicle.color'

    name = fields.Char(string='Vehicle Color', required=True)
    description = fields.Char(string='Description')


class InsuranceCompany(models.Model):
    _name = 'insurance.company'

    name = fields.Char(string='Company Name', required=True)
    address1 = fields.Text(string='Address1')
    address2 = fields.Text(string='Address2')
    phone = fields.Char(string='Phone Number')
    mobile = fields.Char(string='Mobile Number')


class VehicleUsagePurpose(models.Model):
    _name = 'vehicle.usage'

    name = fields.Char(string='Usage Type', required=True)
    description = fields.Char(string='Description')


class VehicleEntryDetails(models.Model):
    _name = 'vehicle.details'
    _rec_name = 'registration_no'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    old_new = fields.Selection([('old', 'Old'), ('new', 'New')],
                                 string='Old/New', required=True)
    fuel_type_id = fields.Many2one('fuel.type', string='Fuel Type', required=True)
    usage_type_id = fields.Many2one('vehicle.usage', string='Usage Type', required=True)
    vehicle_type_id = fields.Many2one('vehicle.type', string='Vehicle Type', required=True)
    maker_id = fields.Many2one('vehicle.make', string='Maker(Brand)', required=True)
    color_id = fields.Many2one('vehicle.color', string='Vehicle Color', required=True)
    vehicle_owner = fields.Char(string='Vehicle Owner', required=True)
    seating_capacity = fields.Char(string='Seating Capacity', required=True)
    engine_number = fields.Char(string='Engine Number', required=True)
    registration_no = fields.Char(string='Register Number', required=True)
    chassis_no = fields.Char(string='Chassis Number', required=True)
    vehicle_model = fields.Char(string='Vehicle Model', required=True)
    year_made = fields.Char(string='Year Of Manufacture', required=True)
    date_made = fields.Date(string='Date Of Manufacturing', required=True)
    registration_date = fields.Date(string='Registration Date', required=True)
    warranty = fields.Char(string='Warranty Period(In Months)')
    cubic_capacity = fields.Char(string='Cubic Capacity(cc)', required=True)
    horse_power = fields.Char(string='Horse Power(hp)', required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approved'), ('cancel', 'Cancelled')], default="draft", string="State")
    active = fields.Boolean(default=True)
    type = fields.Selection([('rent', 'Rent'),('lease', 'Lease'),('own', 'Own')], 'Type',default='own')
    vendor = fields.Many2one('res.partner', string='Vendor', domain="[('supplier', '=', True)]")
    emi_start_month = fields.Selection(month_list, string='EMI Start Month')
    rent_amt = fields.Float(string='Rent Amount')
    tuner = fields.Char(string='Tuner')
    loan_amt = fields.Char(string='Loan Amount')
    tds_amount = fields.Char(string='TDS Amount')
    emi_amt = fields.Char(string='EMI Amount')
    hfd_by = fields.Char(string='HFD By')
    pay_amt = fields.Char(string='Payable Amount')
    hfd_year = fields.Char(string='HFD Year')

    @api.multi
    def approval_button(self):
        self.write({'state': 'approved'})

    @api.multi
    def cancel_button(self):
        self.write({'state': 'cancel'})


class FuelBillTransaction(models.Model):
    _name = 'driver.mapping'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    driver_assistant = fields.Selection([('driver', 'Driver'), ('helper_asst', 'Helper/Asst.Driver')], required=True,default='driver')
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Vehicle Registration Number', required=True,domain="[('branch_id', '=', branch_id)]")
    driver_helper_emp_no = fields.Char(string='Driver/Helper Emp Number', required=True)
    name = fields.Char(string='Name', required=True)
    salary = fields.Char(string='Salary', required=True)
    dob = fields.Date(string='DOB', required=True)
    designation = fields.Char(string='Designation', required=True)
    driving_licence = fields.Char(string='Driving Licence Number', required=True)
    expiry_date = fields.Date(string='Driving Licence Expiry Date', required=True)


class VehicleRegistrationNumberEdit(models.Model):
    _name = 'edit.registration.number'
    _rec_name = 'vehicle_reg_no_id'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Registration Number', required=True,domain="[('branch_id', '=', branch_id)]")
    old_registration = fields.Char(string='Old Registration Number', required=True)
    new_registration = fields.Char(string='New Registration Number', required=True)
    state = fields.Selection([('draft', 'Draft'), ('updated', 'Number Updated')], default="draft", string="State", track_visibility='onchange')
 
    @api.onchange('vehicle_reg_no_id')
    def onchange_vehicle_reg_no(self):
        if self.vehicle_reg_no_id:
            self.old_registration = self.vehicle_reg_no_id.registration_no
            
    @api.multi
    def vehicle_number_uodate(self):
        self.vehicle_reg_no_id.registration_no = self.new_registration
        self.write({'state': 'updated'})

class VehicleDeactivation(models.Model):
    _name = 'vehicle.deactivation'
    _rec_name = 'vehicle_reg_no_id'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Vehicle Registration Number', required=True,domain="[('branch_id', '=', branch_id)]")
    state = fields.Selection([('draft', 'Draft'), ('deactivate', 'Deactivated')], default="draft", string="State", track_visibility='onchange')

    @api.multi
    def vehicle_deactivation(self):
        self.vehicle_reg_no_id.active = False
        self.write({'state': 'deactivate'})


class VehiclePetroCardMapping(models.Model):
    _name = 'petro.mapping'
    _rec_name = 'petro_vendor'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Vehicle Registration Number', required=True, domain="[('branch_id', '=', branch_id)]")
    petro_vendor = fields.Many2one('res.partner', string='Vendor', required=True, domain="[('supplier', '=', True)]")
    card_no = fields.Char(string='Card Number', required=True)


class VehicleBranchUpdate(models.Model):
    _name = 'vehicle.branch.update'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Vehicle Registration Number', required=True, domain="[('branch_id', '=', branch_id)]")
    new_branch = fields.Many2one('operating.unit', string='New Branch', required=True)
    state = fields.Selection([('draft', 'Draft'), ('updated', 'Updated')], default="draft", string="State", track_visibility='onchange')

    @api.multi
    def branch_update(self):
        self.vehicle_reg_no_id.branch_id = self.new_branch.id
        self.write({'state': 'updated'})

class VehicleFuelDetails(models.Model):
    _name = 'fuel.details'
    _rec_name = 'bill_no'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Vehicle Registration Number', required=True, domain="[('branch_id', '=', branch_id)]")
    vehicle_type_id = fields.Many2one('vehicle.type', string='Vehicle Type', required=True)
    maker_id = fields.Many2one('vehicle.make', string='Maker(Brand)', required=True)
    fuel_type_id = fields.Many2one('fuel.type', string='Fuel Type', required=True)
    no_litters = fields.Float(string='No Of Litres', required=True)
    fuel_vendor = fields.Many2one('res.partner', string='Vendor', required=True, domain="[('supplier', '=', True),('vehicle_vendor', '=', True)]")
    bill_amount = fields.Float(string='Bill Amount', required=True)
    bill_no = fields.Char(string='Bill Number', required=True)
    bill_date = fields.Date(string='Bill Date', required=True)
    bill_due_date = fields.Date(string='Bill Due Date', required=True)
    cash_credit = fields.Selection([('cash', 'Cash'), ('credit', 'Credit')],
                                 string='Cash Or Credit', required=True)
    narration = fields.Text(string='Narration', required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approved'), ('unapproved', 'Un Approved')], default="draft", string="State")
    last_fuel_details = fields.One2many('last.fuel.details', 'fuel_id')

    @api.multi
    def fuel_approval_button(self):
        self.write({'state': 'approved'})

    @api.multi
    def un_approve_button(self):
        self.write({'state': 'unapproved'})

    @api.onchange('vehicle_reg_no_id')
    def onchange_vehicle_reg_no(self):
        if self.vehicle_reg_no_id:
            self.fuel_type_id = self.vehicle_reg_no_id.fuel_type_id.id
            fuel_details = self.env['fuel.details'].search([('branch_id','=',self.branch_id.id),('vehicle_reg_no_id','=',self.vehicle_reg_no_id.id)], order="id desc",limit=5)
            vals = [(0, 0, {
                        'vehicle_reg_no_id':self.vehicle_reg_no_id.id,
                        'sl_no':index+1,
                        'state':line.state,
                        'bill_date':line.bill_date,
                        'fuel_type_id':line.fuel_type_id.id,
                        'no_of_liters':line.no_litters,
                        'total_amount':line.bill_amount,
                    }) for index, line in enumerate(fuel_details)]
            self.last_fuel_details = vals


class LastFuelDetails(models.Model):
    _name = 'last.fuel.details'

    fuel_id = fields.Many2one('fuel.details')
    sl_no = fields.Char(string='Sl No')
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Reg. No.',domain="[('branch_id', '=', branch_id)]")
    bill_date = fields.Date()
    fuel_type_id = fields.Many2one('fuel.type', string='Fuel Type')
    no_of_liters = fields.Float()
    total_amount = fields.Float()
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approved'), ('unapproved', 'Un Approved')], default="draft", string="State")
    
class VehicleMeterReadingEntry(models.Model):
    _name = 'meter.reading.entry'
    _rec_name = 'maker_id'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Vehicle Registration Number', required=True, domain="[('branch_id', '=', branch_id)]")
    vehicle_type_id = fields.Many2one('vehicle.type', string='Vehicle Type', required=True)
    maker_id = fields.Many2one('vehicle.make', string='Maker(Brand)', required=True)
    date = fields.Date(string='Reading Date', required=True)
    present_reading = fields.Integer(string='Present Reading', required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submitted')], default="draft", string="State")
    last_meter_details = fields.One2many('last.meter.details', 'meter_id')
    initial_reading = fields.Integer()
    corrected_reading = fields.Integer()

    @api.model
    def create(self, vals):
        if 'present_reading' and 'branch_id' and 'date'in vals:
            existing_meter = self.env['meter.reading.entry'].search([('branch_id','=',vals['branch_id']),('vehicle_reg_no_id','=',vals['vehicle_reg_no_id']),('date','=',vals['date']),('state','=','submit')])
            if not existing_meter:
                vals['initial_reading'] = vals['present_reading']
            else:
                raise ValidationError(_("Already Created"))
        res = super(VehicleMeterReadingEntry, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if 'present_reading' in vals:
            existing_meter = self.env['meter.reading.entry'].search([('branch_id','=',self.branch_id.id),('vehicle_reg_no_id','=',self.vehicle_reg_no_id.id),('date','=',self.date),('state','=','submit')])
            if not existing_meter:
                vals['initial_reading'] = vals['present_reading']
            else:
                raise ValidationError(_("Already Created"))
        return super(VehicleMeterReadingEntry, self).write(vals)

    @api.multi
    def submit_reading(self):
        self.write({'state': 'submit'})

    @api.onchange('vehicle_reg_no_id')
    def onchange_vehicle_reg_no(self):
        if self.vehicle_reg_no_id:
            self.vehicle_type_id = self.vehicle_reg_no_id.vehicle_type_id.id
            self.maker_id = self.vehicle_reg_no_id.maker_id.id
            meter_details = self.env['meter.reading.entry'].search([('branch_id','=',self.branch_id.id),('vehicle_reg_no_id','=',self.vehicle_reg_no_id.id),('state','=','submit')], order="id desc",limit=5)
            vals = [(0, 0, {
                        'vehicle_reg_no_id':self.vehicle_reg_no_id.id,
                        'sl_no':index+1,
                        'reading_date':line.date,
                        'old_reading':line.present_reading,
                        'corrected_reading':line.corrected_reading,
                        'no_of_km':line.corrected_reading - line.present_reading,
                    }) for index, line in enumerate(meter_details)]
            self.last_meter_details = vals

class LastMeterDetails(models.Model):
    _name = 'last.meter.details'

    meter_id = fields.Many2one('meter.reading.entry')
    sl_no = fields.Char(string='Sl No')
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Reg. No.',domain="[('branch_id', '=', branch_id)]")
    reading_date = fields.Date()
    old_reading = fields.Integer(string='O.R')
    corrected_reading = fields.Integer(string='C.R')
    no_of_km = fields.Integer(string='No.KM')
   
class MeterReadingUpdate(models.Model):
    _name = 'meter.reading.update' 
    _rec_name = 'vehicle_reg_no_id'
    
    
    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Vehicle Registration Number', required=True, domain="[('branch_id', '=', branch_id)]")
    vehicle_type_id = fields.Many2one('vehicle.type', string='Vehicle Type', required=True)
    maker_id = fields.Many2one('vehicle.make', string='Maker(Brand)', required=True)
    date = fields.Date(string='Reading Date', required=True)
    present_reading = fields.Integer(string='Present Reading', required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submitted')], default="draft", string="State")

    @api.multi
    def search_reading(self):
        vehicles = self.env['meter.reading.entry'].search([('branch_id','=',self.branch_id.id),('vehicle_reg_no_id','=',self.vehicle_reg_no_id.id),('state','=','submit'),('date','=',self.date)],limit=1)
        if vehicles:
            self.present_reading = vehicles.initial_reading
        
    @api.multi
    def submit_reading(self):
        vehicles = self.env['meter.reading.entry'].search([('branch_id','=',self.branch_id.id),('vehicle_reg_no_id','=',self.vehicle_reg_no_id.id),('state','=','submit'),('date','=',self.date)],limit=1)
        if vehicles:
            vehicles.corrected_reading = self.present_reading
            vehicles.no_of_km = vehicles.corrected_reading - vehicles.present_reading
       
    @api.onchange('vehicle_reg_no_id')
    def onchange_vehicle_reg_no(self):
        if self.vehicle_reg_no_id:
            self.vehicle_type_id = self.vehicle_reg_no_id.vehicle_type_id.id
            self.maker_id = self.vehicle_reg_no_id.maker_id.id 
        
        
class RepairMaintenance(models.Model):
    _name = 'repair.maintenance'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    building_id = fields.Many2one('pappaya.building', string='Building Name', required=True,
                                  domain="[('branch_id', '=', branch_id)]")
    invoice_bill_no = fields.Char(string='Invoice Bill Number', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    invoice_date = fields.Date(string='Invoice Bill Date', required=True)
    vendor = fields.Many2one('res.partner', string='Vendor', required=True, domain="[('supplier', '=', True)]")
    vendor_supply_state = fields.Many2one('res.country.state', string='Vendor Supply State', required=True)
    gst_in = fields.Char(string='GSTIN')
    bill_due_date = fields.Date(string='Bill Due Date', required=True)
    service_category = fields.Many2one('product.category', string='Service Category', required=True)
    month = fields.Selection(month_list, string='Month',required=True)
    vehicle_type_id = fields.Many2one('vehicle.type', string='Vehicle', required=True)
    service_item = fields.One2many('vehicle.service.item', 'service_id')
    service_details = fields.One2many('vehicle.service.details.item', 'service_id')
    bill_amount = fields.Float(string='Bill Amount', store=True)
    discount_amount = fields.Float(string='Discount Amount', store=True)
    bill_amount_after_discount = fields.Float(string='Bill Amount After Discount', store=True)
    igst_amount = fields.Float(string='IGST Amount', store=True)
    cgst_amount = fields.Float(string='CGST Amount', store=True)
    sgst_amount = fields.Float(string='SGST Amount', store=True)
    total_bill_amount = fields.Float(string='Total Bill Amount', store=True)
    tds = fields.Float(string='TDS', store=True)
    net_due_amount = fields.Float(string='Net Due Amount', store=True)
    igst_pay = fields.Float(string='IGST Pay', store=True)
    cgst_pay = fields.Float(string='CGST Pay', store=True)
    sgst_pay = fields.Float(string='SGST Pay', store=True)
    invoice_raised = fields.Float(string='Invoice Raised By', store=True)
    is_repair = fields.Boolean()
    
    @api.onchange('cgst_amount')
    def onchange_cgst_amount(self):
        if self.cgst_amount:
            self.sgst_amount = self.cgst_amount

    @api.onchange('sgst_amount')
    def onchange_sgst_amount(self):
        if self.sgst_amount:
            self.cgst_amount = self.sgst_amount

    @api.onchange('bill_amount','discount_amount','igst_amount','cgst_amount','sgst_amount')
    def onchange_bill_amount(self):
        if self.bill_amount or self.discount_amount or self.igst_amount or self.sgst_amount or self.cgst_amount:
            self.bill_amount_after_discount = self.bill_amount - self.discount_amount
            self.total_bill_amount = self.bill_amount - self.discount_amount + self.cgst_amount + self.sgst_amount + self.igst_amount

    @api.onchange('vendor')
    def onchange_vendor(self):
        if self.vendor:
            self.vendor_supply_state = self.vendor.state_id.id or False

    @api.onchange('service_item','service_details')
    def onchange_service_item(self):
        if self.service_item or self.service_details:
            amount =0.0
            discount = 0.0
            cgst_amount = 0.0
            sgst_amount = 0.0
            igst_amount = 0.0
            for line in self.service_item:
                amount += line.amount
                discount += line.discount_amount
                if line.hs_rates.tax_group_id.name == 'SGST' or line.hs_rates.tax_group_id.name == 'CGST':          
                    cgst_amount += line.amount * (line.hs_rates.amount / 100)
                    sgst_amount += line.amount * (line.hs_rates.amount / 100)
                elif line.hs_rates.tax_group_id.name == 'IGST':          
                    igst_amount += line.amount * (line.hs_rates.amount / 100)
            for det in self.service_details:
                amount += det.amount
                discount += det.discount_amount
                if det.sas_rates.tax_group_id.name == 'SGST' or det.sas_rates.tax_group_id.name == 'CGST':          
                    cgst_amount += det.amount * (det.sas_rates.amount / 100)
                    sgst_amount += det.amount * (det.sas_rates.amount / 100)
                elif det.sas_rates.tax_group_id.name == 'IGST':          
                    igst_amount += det.amount * (det.sas_rates.amount / 100)
            self.bill_amount = amount
            self.discount_amount = discount
            self.igst_amount = igst_amount
            self.cgst_amount = cgst_amount
            self.sgst_amount = sgst_amount
        else:
            self.bill_amount = 0.0
            self.discount_amount = 0.0

class ServiceItem(models.Model):
    _name = 'vehicle.service.item'

    service_id = fields.Many2one('repair.maintenance')
    item = fields.Many2one('product.product', string='Item', required=True)
    hs_code = fields.Char(string='HSN Code', required=True)
    hs_rates = fields.Many2one('account.tax',string='HSN Rates', required=True)
    sub_ledger = fields.Many2one('account.account',string='Subledger', required=True)
    price = fields.Float(string='Price', required=True)
    qty = fields.Float(string='Quantity', required=True)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type',default="amt")
    amount = fields.Float(string='Amount', required=True)
    discount_amount = fields.Float(string='Discount Amount/%', store=True)

    @api.onchange('item')
    def onchange_item(self):
        if self.item:
            self.hs_code = self.item.l10n_in_hsn_code or ''
            self.price = self.item.standard_price or 0.0
        else:
            self.hs_code = ''
            self.price = 0.0
        if self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code == 'AP':
            local_group = self.env['account.tax.group'].search(['|',('name','=','SGST'),('name','=','CGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'hs_rates': [('id', 'in', taxes.ids)]}}
        elif self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code != 'AP':
            local_group = self.env['account.tax.group'].search([('name','=','IGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'hs_rates': [('id', 'in', taxes.ids)]}}

    @api.onchange('qty')
    def onchange_qty(self):
        if self.qty:
            self.amount = self.qty * self.price - self.discount_amount   

class ServiceDetails(models.Model):
    _name = 'vehicle.service.details.item'

    service_id = fields.Many2one('repair.maintenance')
    service = fields.Many2one('product.product', string='Service', required=True)
    sub_ledger = fields.Many2one('account.account',string='Subledger', required=True)
    sas_code = fields.Char(string='SAS Code', required=True)
    sas_rates = fields.Many2one('account.tax', string='SAS Rates', required=True)
    amount = fields.Float(string='Amount', required=True)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type',default="amt")
    discount_amount = fields.Float(string='Discount Amount/%', store=True)

    @api.onchange('service')
    def onchange_service(self):
        if self.service:
            self.sas_code = self.service.l10n_in_hsn_code or ''
        if self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code == 'AP':
            local_group = self.env['account.tax.group'].search(['|',('name','=','SGST'),('name','=','CGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'sas_rates': [('id', 'in', taxes.ids)]}}
        elif self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code != 'AP':
            local_group = self.env['account.tax.group'].search([('name','=','IGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'sas_rates': [('id', 'in', taxes.ids)]}}
   
class InsurancePayment(models.Model):
    _name = 'insurance.payment'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    building_id = fields.Many2one('pappaya.building', string='Building Name', required=True,
                                  domain="[('branch_id', '=', branch_id)]")
    invoice_bill_no = fields.Char(string='Invoice Bill Number', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    invoice_date = fields.Date(string='Invoice Bill Date', required=True)
    vendor = fields.Many2one('res.partner', string='Vendor', required=True, domain="[('supplier', '=', True)]")
    vendor_supply_state = fields.Many2one('res.country.state', string='Vendor Supply State', required=True)
    gst_in = fields.Char(string='GSTIN')
    bill_due_date = fields.Date(string='Bill Due Date', required=True)
    service_category = fields.Many2one('product.category', string='Service Category', required=True)
    month = fields.Selection(month_list, string='Month',required=True)
    vehicle_type_id = fields.Many2one('vehicle.type', string='Vehicle', required=True)
    service_item = fields.One2many('insurance.service', 'service_id')
    service_details = fields.One2many('insurance.details', 'service_id')
    bill_amount = fields.Float(string='Bill Amount', store=True)
    discount_amount = fields.Float(string='Discount Amount', store=True)
    bill_amount_after_discount = fields.Float(string='Bill Amount After Discount', store=True)
    igst_amount = fields.Float(string='IGST Amount', store=True)
    cgst_amount = fields.Float(string='CGST Amount', store=True)
    sgst_amount = fields.Float(string='SGST Amount', store=True)
    total_bill_amount = fields.Float(string='Total Bill Amount', store=True)
    tds = fields.Float(string='TDS', store=True)
    net_due_amount = fields.Float(string='Net Due Amount', store=True)
    igst_pay = fields.Float(string='IGST Pay', store=True)
    cgst_pay = fields.Float(string='CGST Pay', store=True)
    sgst_pay = fields.Float(string='SGST Pay', store=True)
    invoice_raised = fields.Float(string='Invoice Raised By', store=True)
    is_repair = fields.Boolean()
    
    @api.onchange('cgst_amount')
    def onchange_cgst_amount(self):
        if self.cgst_amount:
            self.sgst_amount = self.cgst_amount

    @api.onchange('sgst_amount')
    def onchange_sgst_amount(self):
        if self.sgst_amount:
            self.cgst_amount = self.sgst_amount

    @api.onchange('bill_amount','discount_amount','igst_amount','cgst_amount','sgst_amount')
    def onchange_bill_amount(self):
        if self.bill_amount or self.discount_amount or self.igst_amount or self.sgst_amount or self.cgst_amount:
            self.bill_amount_after_discount = self.bill_amount - self.discount_amount
            self.total_bill_amount = self.bill_amount - self.discount_amount + self.cgst_amount + self.sgst_amount + self.igst_amount

    @api.onchange('vendor')
    def onchange_vendor(self):
        if self.vendor:
            self.vendor_supply_state = self.vendor.state_id.id or False

    @api.onchange('service_item','service_details')
    def onchange_service_item(self):
        if self.service_item or self.service_details:
            amount =0.0
            discount = 0.0
            cgst_amount = 0.0
            sgst_amount = 0.0
            igst_amount = 0.0
            for line in self.service_item:
                amount += line.amount
                discount += line.discount_amount
                if line.hs_rates.tax_group_id.name == 'SGST' or line.hs_rates.tax_group_id.name == 'CGST':          
                    cgst_amount += line.amount * (line.hs_rates.amount / 100)
                    sgst_amount += line.amount * (line.hs_rates.amount / 100)
                elif line.hs_rates.tax_group_id.name == 'IGST':          
                    igst_amount += line.amount * (line.hs_rates.amount / 100)
            for det in self.service_details:
                amount += det.amount
                discount += det.discount_amount
                if det.sas_rates.tax_group_id.name == 'SGST' or det.sas_rates.tax_group_id.name == 'CGST':          
                    cgst_amount += det.amount * (det.sas_rates.amount / 100)
                    sgst_amount += det.amount * (det.sas_rates.amount / 100)
                elif det.sas_rates.tax_group_id.name == 'IGST':          
                    igst_amount += det.amount * (det.sas_rates.amount / 100)
            self.bill_amount = amount
            self.discount_amount = discount
            self.igst_amount = igst_amount
            self.cgst_amount = cgst_amount
            self.sgst_amount = sgst_amount
        else:
            self.bill_amount = 0.0
            self.discount_amount = 0.0
            self.igst_amount = 0.0
            self.cgst_amount = 0.0
            self.sgst_amount = 0.0


class InsuranceService(models.Model):
    _name = 'insurance.service'

    service_id = fields.Many2one('insurance.payment')
    item = fields.Many2one('product.product', string='Item', required=True)
    hs_code = fields.Char(string='HSN Code', required=True)
    hs_rates = fields.Many2one('account.tax',string='HSN Rates', required=True)
    sub_ledger = fields.Many2one('account.account',string='Subledger', required=True)
    price = fields.Float(string='Price', required=True)
    qty = fields.Float(string='Quantity', required=True)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type',default="amt")
    amount = fields.Float(string='Amount', required=True)
    discount_amount = fields.Float(string='Discount Amount/%', store=True)

    @api.onchange('item')
    def onchange_item(self):
        if self.item:
            self.hs_code = self.item.l10n_in_hsn_code or ''
            self.price = self.item.standard_price or 0.0
        else:
            self.hs_code = ''
            self.price = 0.0
        if self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code == 'AP':
            local_group = self.env['account.tax.group'].search(['|',('name','=','SGST'),('name','=','CGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'hs_rates': [('id', 'in', taxes.ids)]}}
        elif self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code != 'AP':
            local_group = self.env['account.tax.group'].search([('name','=','IGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'hs_rates': [('id', 'in', taxes.ids)]}}

    @api.onchange('qty')
    def onchange_qty(self):
        if self.qty:
            self.amount = self.qty * self.price - self.discount_amount   


class InsuranceDetails(models.Model):
    _name = 'insurance.details'

    service_id = fields.Many2one('insurance.payment')
    service = fields.Many2one('product.product', string='Service', required=True)
    sub_ledger = fields.Many2one('account.account',string='Subledger', required=True)
    sas_code = fields.Char(string='SAS Code', required=True)
    sas_rates = fields.Many2one('account.tax', string='SAS Rates', required=True)
    amount = fields.Float(string='Amount', required=True)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type',default="amt")
    discount_amount = fields.Float(string='Discount Amount/%', store=True)

    @api.onchange('service')
    def onchange_service(self):
        if self.service:
            self.sas_code = self.service.l10n_in_hsn_code or ''
        if self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code == 'AP':
            local_group = self.env['account.tax.group'].search(['|',('name','=','SGST'),('name','=','CGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'sas_rates': [('id', 'in', taxes.ids)]}}
        elif self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code != 'AP':
            local_group = self.env['account.tax.group'].search([('name','=','IGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'sas_rates': [('id', 'in', taxes.ids)]}}


class LeasedVehicle(models.Model):
    _name = 'leased.vehicle'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    building_id = fields.Many2one('pappaya.building', string='Building Name', required=True,
                                  domain="[('branch_id', '=', branch_id)]")
    invoice_bill_no = fields.Char(string='Invoice Bill Number', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    invoice_date = fields.Date(string='Invoice Bill Date', required=True)
    vendor = fields.Many2one('res.partner', string='Vendor', required=True, domain="[('supplier', '=', True)]")
    vendor_supply_state = fields.Many2one('operating.unit', string='Vendor Supply State', required=True)
    gst_in = fields.Char(string='GSTIN')
    bill_due_date = fields.Date(string='Bill Due Date', required=True)
    service_category = fields.Many2one('product.category', string='Service Category', required=True)
    month = fields.Char(string='Month', required=True )
    service_item = fields.One2many('leased.service', 'service_id')
    service_details = fields.One2many('leased.details', 'service_id')
    bill_amount = fields.Float(string='Bill Amount', store=True)
    discount_amount = fields.Float(string='Discount Amount', store=True)
    bill_amount_after_discount = fields.Float(string='Bill Amount After Discount', store=True)
    igst_amount = fields.Float(string='IGST Amount', store=True)
    cgst_amount = fields.Float(string='CGST Amount', store=True)
    sgst_amount = fields.Float(string='SGST Amount', store=True)
    total_bill_amount = fields.Float(string='Total Bill Amount', store=True)
    tds = fields.Float(string='TDS', store=True)
    net_due_amount = fields.Float(string='Net Due Amount', store=True)
    igst_pay = fields.Float(string='IGST Pay', store=True)
    cgst_pay = fields.Float(string='CGST Pay', store=True)
    sgst_pay = fields.Float(string='SGST Pay', store=True)
    invoice_raised = fields.Float(string='Invoice Raised By', store=True)

class LeasedService(models.Model):
    _name = 'leased.service'

    service_id = fields.Many2one('leased.vehicle')
    item = fields.Many2one('product.template', string='Item', required=True)
    hs_code = fields.Many2one('product.template', string='HS Code', required=True)
    hs_rates = fields.Many2one('product.template', string='HS Rates', required=True)
    sub_ledger = fields.Char(string='Subledger', required=True)
    price = fields.Float(string='Price', required=True)
    qty = fields.Char(string='Quantity', required=True)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type')
    discount_amount = fields.Float(string='Discount Amount/%', store=True)


class LeasedDetails(models.Model):
    _name = 'leased.details'

    service_id = fields.Many2one('leased.vehicle')
    service = fields.Many2one('product.template', string='Service', required=True)
    sub_ledger = fields.Char(string='Subledger', required=True)
    sas_code = fields.Many2one('product.template', string='SAS Code', required=True)
    sas_rates = fields.Many2one('product.template', string='SAS Rates', required=True)
    amount = fields.Float(string='Amount', required=True)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type')
    discount_amount = fields.Float(string='Discount Amount/%', store=True)


class TaxChequePreparation(models.Model):
    _name = 'tax.cheque.preparation'

    cash_cheque = fields.Selection([('cash', 'Cash'), ('cheque', 'Cheque')], string='Cash/Cheque')
    bank = fields.Char(string='Bank')
    branch_id = fields.Many2one('operating.unit', string='Branch')
    cheque_lot = fields.Many2one('cheque.lot', string='Cheque Lot')
    trans_date = fields.Date(string='Trans Date')
    bank_balance = fields.Float(string='Bank Balance')
    cheque_date = fields.Date(string='Cheque Date')
    bank_dd = fields.Selection([('bank_cheque', 'Bank Cheque'), ('dd_cheque', 'DD Cheque')],
                               string='Bank Cheque/DD Cheque')
    cheque_no = fields.Char(string='Cheque Number')
    payee_name = fields.Char(string='Payee Name')
    branch = fields.Many2one('operating.unit', string='Branch')
    vehicle = fields.Many2one('vehicle.type',string='Vehicle')
    amount = fields.Char(string='Amount')
    tax_type = fields.Many2one('account.tax', string='Tax Type')
    tax_amount = fields.Float(string='Tax Amount')
    narration = fields.Text(string='Narration')
    trans_date1 = fields.Date(string='Trans Date')
    branch_id1 = fields.Many2one('operating.unit', string='Branch')
    bank_balance1 = fields.Float(string='Bank Balance')
    vehicle1 = fields.Many2one('vehicle.type', string='Vehicle')
    tax_type1 = fields.Many2one('account.tax', string='Tax Type')
    tax_amount1 = fields.Float(string='Tax Amount')
    narration1 = fields.Text(string='Narration')


class LeasedVehicleBranchUpdate(models.Model):
    _name = 'leased.branch.update'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    vehicle_reg_no_id = fields.Many2one('vehicle.details', string='Vehicle Registration Number', required=True,domain="[('branch_id', '=', branch_id),('type', '=', 'lease')]")
    new_branch_id = fields.Many2one('operating.unit', string='New Branch', required=True)
    vendor = fields.Many2one('res.partner', string='Vendor', domain="[('supplier', '=', True)]")
    reg_no = fields.Char(string='Registration Number')
    emi_start_month = fields.Char(string='EMI Start Month')
    rent_amt = fields.Float(string='Rent Amount')
    tuner = fields.Char(string='Tuner')
    loan_amt = fields.Char(string='Loan Amount')
    tds_amount = fields.Char(string='TDS Amount')
    emi_amt = fields.Char(string='EMI Amount')
    hfd_by = fields.Char(string='HFD By')
    seating_capacity = fields.Char(string='Seating Capacity')
    pay_amt = fields.Char(string='Payable Amount')
    hfd_year = fields.Char(string='HFD Year')
    state = fields.Selection(
        [('draft', 'Draft'), ('updated', 'Updated')], default="draft", string="State")

    @api.onchange('vehicle_reg_no_id')
    def onchange_vehicle_reg_no(self):
        if self.vehicle_reg_no_id:
            self.vendor = self.vehicle_reg_no_id.vendor.id
            self.reg_no = self.vehicle_reg_no_id.registration_no
            self.emi_start_month = self.vehicle_reg_no_id.emi_start_month
            self.rent_amt = self.vehicle_reg_no_id.rent_amt
            self.tuner = self.vehicle_reg_no_id.tuner
            self.loan_amt = self.vehicle_reg_no_id.loan_amt
            self.tds_amount = self.vehicle_reg_no_id.tds_amount
            self.emi_amt = self.vehicle_reg_no_id.emi_amt
            self.hfd_by = self.vehicle_reg_no_id.hfd_by
            self.seating_capacity = self.vehicle_reg_no_id.seating_capacity
            self.pay_amt = self.vehicle_reg_no_id.pay_amt
            self.hfd_year = self.vehicle_reg_no_id.hfd_year
            
    @api.multi
    def update_branch(self):
        vehicles = self.env['vehicle.details'].search([('branch_id','=',self.branch_id.id),('registration_no','=',self.vehicle_reg_no_id.registration_no),('state','=','approved'),('type','=','lease')],limit=1)
        if vehicles:
            vehicles.branch_id = self.new_branch_id.id
            vehicles.vendor = self.vendor.id or False
            self.write({'state':'updated'})
            
class FuelBillUpload(models.Model):
    _name = 'bill.upload'

    description = fields.Text(string='Description')
    bill_upload = fields.Binary(string='Bill Upload')


class LeasedVehicleInvoice(models.Model):
    _name = 'leased.vehicle.invoice'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    building_id = fields.Many2one('pappaya.building', string='Building Name', required=True,
                                  domain="[('branch_id', '=', branch_id)]")
    invoice_bill_no = fields.Char(string='Invoice Bill Number', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    invoice_date = fields.Date(string='Invoice Bill Date', required=True)
    vendor = fields.Many2one('res.partner', string='Vendor', required=True, domain="[('supplier', '=', True)]")
    vendor_supply_state = fields.Many2one('res.country.state', string='Vendor Supply State', required=True)
    gst_in = fields.Char(string='GSTIN')
    bill_due_date = fields.Date(string='Bill Due Date', required=True)
    service_category = fields.Many2one('product.category', string='Service Category', required=True)
    month = fields.Selection(month_list, string='Month',required=True)
    service_details = fields.One2many('leased.details.invoice', 'service_id')
    bill_amount = fields.Float(string='Bill Amount', store=True)
    discount_amount = fields.Float(string='Discount Amount', store=True)
    bill_amount_after_discount = fields.Float(string='Bill Amount After Discount', store=True)
    igst_amount = fields.Float(string='IGST Amount', store=True)
    cgst_amount = fields.Float(string='CGST Amount', store=True)
    sgst_amount = fields.Float(string='SGST Amount', store=True)
    total_bill_amount = fields.Float(string='Total Bill Amount', store=True)
    tds = fields.Float(string='TDS', store=True)
    net_due_amount = fields.Float(string='Net Due Amount', store=True)
    igst_pay = fields.Float(string='IGST Pay', store=True)
    cgst_pay = fields.Float(string='CGST Pay', store=True)
    sgst_pay = fields.Float(string='SGST Pay', store=True)
    invoice_raised = fields.Float(string='Invoice Raised By', store=True)
    is_repair = fields.Boolean()
    
    @api.onchange('cgst_amount')
    def onchange_cgst_amount(self):
        if self.cgst_amount:
            self.sgst_amount = self.cgst_amount

    @api.onchange('sgst_amount')
    def onchange_sgst_amount(self):
        if self.sgst_amount:
            self.cgst_amount = self.sgst_amount

    @api.onchange('bill_amount','discount_amount','igst_amount','cgst_amount','sgst_amount')
    def onchange_bill_amount(self):
        if self.bill_amount or self.discount_amount or self.igst_amount or self.sgst_amount or self.cgst_amount:
            self.bill_amount_after_discount = self.bill_amount - self.discount_amount
            self.total_bill_amount = self.bill_amount - self.discount_amount + self.cgst_amount + self.sgst_amount + self.igst_amount

    @api.onchange('vendor')
    def onchange_vendor(self):
        if self.vendor:
            self.vendor_supply_state = self.vendor.state_id.id or False

    @api.onchange('service_details')
    def onchange_service_item(self):
        if self.service_details:
            amount =0.0
            discount = 0.0
            cgst_amount = 0.0
            sgst_amount = 0.0
            igst_amount = 0.0
            for det in self.service_details:
                amount += det.amount
                discount += det.discount_amount
                if det.sas_rates.tax_group_id.name == 'SGST' or det.sas_rates.tax_group_id.name == 'CGST':          
                    cgst_amount += det.amount * (det.sas_rates.amount / 100)
                    sgst_amount += det.amount * (det.sas_rates.amount / 100)
                elif det.sas_rates.tax_group_id.name == 'IGST':          
                    igst_amount += det.amount * (det.sas_rates.amount / 100)
            self.bill_amount = amount
            self.discount_amount = discount
            self.igst_amount = igst_amount
            self.cgst_amount = cgst_amount
            self.sgst_amount = sgst_amount
        else:
            self.bill_amount = 0.0
            self.discount_amount = 0.0
            self.igst_amount = 0.0
            self.cgst_amount = 0.0
            self.sgst_amount = 0.0

class LeasedDetailsInvoice(models.Model):
    _name = 'leased.details.invoice'

    service_id = fields.Many2one('leased.vehicle.invoice')
    service = fields.Many2one('product.product', string='Service', required=True)
    sub_ledger = fields.Many2one('account.account',string='Subledger', required=True)
    sas_code = fields.Char(string='SAS Code', required=True)
    sas_rates = fields.Many2one('account.tax', string='SAS Rates', required=True)
    amount = fields.Float(string='Amount', required=True)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type',default="amt")
    discount_amount = fields.Float(string='Discount Amount/%', store=True)
    

    @api.onchange('service')
    def onchange_service(self):
        if self.service:
            self.sas_code = self.service.l10n_in_hsn_code or ''
        if self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code == 'AP':
            local_group = self.env['account.tax.group'].search(['|',('name','=','SGST'),('name','=','CGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'sas_rates': [('id', 'in', taxes.ids)]}}
        elif self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code != 'AP':
            local_group = self.env['account.tax.group'].search([('name','=','IGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'sas_rates': [('id', 'in', taxes.ids)]}}

class ChequeLot(models.Model):
    _name = 'cheque.lot'

    name = fields.Char(string='Name')
