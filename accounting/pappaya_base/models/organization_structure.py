# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from datetime import datetime
import re
import base64,os

class operating_unit_type(models.Model):
    _name='operating.unit.type'
    
    name=fields.Char('Type Name',size=50)
    code = fields.Char('Code',size=50)
    parent_id = fields.Many2one('operating.unit.type','Parent Type')
    description=fields.Text('Description',size=200)
    
    _sql_constraints = [
        ('name_code_unique', 'unique (name,code)',
         'Name and code should be unique!')
    ]    
    
class OperatingUnitInherit(models.Model):
    _inherit = 'operating.unit'
    _order = "name asc"

    @api.constrains('fine_amount', 'is_transport')
    def _check_fine_amount(self):
        if self.is_transport and self.fine_amount < 0.0:
            raise ValidationError('Fine Amount should not be negative!')

    def _get_logo(self):
        return base64.b64encode(open(os.path.join(tools.config['root_path'], 'addons', 'base', 'res', 'res_company_logo.png'), 'rb') .read())
    
    logo = fields.Binary(related='partner_id.image', default=_get_logo, string="Company Logo")
    type_id = fields.Many2one('operating.unit.type', 'Operating Unit Type')
    type = fields.Selection([('entity','Entity'),('branch','Branch'),('building','Building')], 'Organization Type', default='branch')
    code = fields.Char(size=10, string='Code')
    active_academic_year_id = fields.Many2one('academic.year','Active Academic Year')
    active_next_academic_year_id = fields.Many2one('academic.year','Next Active Academic Year')
    record_id = fields.Integer('ID')
    emp_no_ref = fields.Char('Created Employee ID', size=9)
    currency_id = fields.Many2one('res.currency', string='Currency Name', default=lambda self: self.env.user.company_id.currency_id)
    name = fields.Char('Name', size=64)
    mobile_country_code = fields.Char('', size=10)
    phone = fields.Char('Phone', size=12)
    mobile = fields.Char('Mobile', size=10)
    fax_id = fields.Char('Fax ID', size=12)
    zip = fields.Char('Pin Code',size=6)
    email = fields.Char('Email', size=64)    
    state_id = fields.Many2one('res.country.state', string="Branch State",domain=[('country_id.is_active','=',True)])
    region_id = fields.Many2one('pappaya.region', string="Branch Region")
    district_id = fields.Many2one('state.district', string="Branch District")
    
    country_id = fields.Many2one('res.country', string="Country")
    # Address fields
    tem_street = fields.Char('Address', size=30)
    tem_street2 = fields.Char('Address 2', size=30)
    tem_district_id = fields.Many2one('state.district', string="District")
    tem_city_id = fields.Many2one('pappaya.city','City')
    tem_state_id = fields.Many2one('res.country.state', string="State", domain=[('country_id.is_active', '=', True)])
    tem_country_id = fields.Many2one('res.country', string="Country", default=lambda self:self.env['res.country'].sudo().search([('code', '=', 'IN'), ('is_active', '=', True)], limit=1).id, domain=[('is_active', '=', True)])
    tem_zip = fields.Char('Zip', size=6)
    pappaya_division_id = fields.Many2one('pappaya.division', string='Division')
    state_district_id = fields.Many2one('state.district', string='District')
    zone_id = fields.Many2one('pappaya.zone',string='Zone')
    agm_id = fields.Many2one('hr.employee', string ="AGM", domain=[('id','!=',1)])
    dgm_id = fields.Many2one('hr.employee', string="DGM", domain=[('id','!=',1)])
    gm_id = fields.Many2one('hr.employee', string="GM", domain=[('id','!=',1)])
    ao_id = fields.Many2one('hr.employee', string="AO", domain=[('id','!=',1)])
    dean_id = fields.Many2one('hr.employee', string="Dean", domain=[('id','!=',1)])
    principal_id = fields.Many2one('hr.employee', string="Principal", domain=[('id','!=',1)])
    incharge_id = fields.Many2one('hr.employee', string="Branch Incharge", domain=[('id','!=',1)])

    branch_type = fields.Selection([('school','School'),('college','College')], 'Branch Type')
    residential_type_ids = fields.Many2many(comodel_name='residential.type', string='Student Residential Type')
    student_type = fields.Selection([('day','Day'),('semi_residential','Semi Residential'),('hostel','Hostel'),('both','All')],'Student Type')
    gender = fields.Selection([('boys', 'Boys'),('girls','Girls'),('co_education','Co-Education')], 'Branch Type')
    medium_ids = fields.Many2many('pappaya.master', string='Medium')
    is_transport = fields.Boolean('Is Transport Applicable?')
    is_nslate = fields.Boolean('Is Nslate Applicable?')
    is_caution_deposit = fields.Boolean('Is Caution Deposit Applicable?')
    course_config_ids = fields.One2many('pappaya.branch.ay.course.config', 'operating_unit_id',string="Course Configuration")
    segment_cource_mapping_ids = fields.One2many('branch.segment.course.mapping', 'operating_unit_id',string="Segment Course Mapping")
    dhobi_provider_ids = fields.Many2many('pappaya.dhobi.provider', string='Dhobi Provider')
    cash_mode_limit = fields.Integer('Cash Mode Limit', default=1)
    is_show_cash_mode = fields.Boolean('Show Cash Pay Mode?')
    is_tax_applicable = fields.Boolean('Is tax applicable?')
    is_esi_applicable   = fields.Boolean('Is ESI Applicable?')
    
    branch_wise_job_vacancy = fields.One2many('branch.wise.job.vecancy', 'branch_id',string="Job Vacancy") 
    
    # Working Days
    days_monday = fields.Boolean('Monday', default=True)
    days_tuesday = fields.Boolean('Tuesday',default=True)
    days_wednesday = fields.Boolean('Wednesday',default=True)
    days_thursday = fields.Boolean('Thursday',default=True)
    days_friday = fields.Boolean('Friday',default=True)
    days_saturday = fields.Boolean('Saturday',default=True)
    days_sunday = fields.Boolean('Sunday')
    worked_hours_line = fields.One2many('pappaya.branch.worked.hours.line','branch_id', string='Worked Hours')
    branch_workhours_line = fields.One2many('branch.officetype.workhours.line','branch_id', string='Worked Hours')

    # legal_entity_id = fields.Many2one('pappaya.legal.entity', string="Legal Entry")
    stream_ids = fields.Many2many('pappaya.stream', string='Stream')
    office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    is_student_details_applied = fields.Boolean(related='office_type_id.is_student_details_applied', string='Is Student Details Applied?')
    programme_type_ids = fields.Many2many('pappaya.programme', string="Programme")
    segment_type_ids = fields.Many2many('pappaya.segment', string="Segment")
    rfid_device_ip = fields.Text('UHFID Configuration IPs',size=200)


    entity_description = fields.Char('Entity Description', size=100)
    organization_sequence_id = fields.Char(string='Organization Series', size=40)
    entity_sequence_id = fields.Char(string='Entity Series', size=40)
    branch_sequence_id = fields.Char(string='Branch Series', size=40)
    document_followup = fields.Integer(string='Document Follow Up', size=40)
    last_execution_date = fields.Date(string='Last Execution Date')
    website = fields.Char('Website', size=40)
    
    # Transaction Related Fields
    paymode_ids = fields.Many2many('pappaya.paymode', string='Paymode')
    is_library_fee = fields.Boolean('Library Fee')
    library_fee_amount = fields.Float('Library Fee Amount')
    # Paymode Configuration fields
    bank_machine_id = fields.Many2one('bank.machine', string='Bank Machine')
    bank_machine_type_id = fields.Many2one('pappaya.master', string='Machine Type',related='bank_machine_id.bank_machine_type_id')
    mid_number = fields.Char(string='M.I.D.No(last 6 digits)', size=6)
    tid_number = fields.Char(string='T.I.D.No', size=15)
    bank_account_mapping_ids = fields.One2many('branch.bank.account.mapping', 'operating_unit_id', string='Bank Account Mapping')
    transport_installment_ids = fields.One2many('transport.installment.config', 'branch_id', string='Transport Installment')
    transport_config_ids = fields.One2many('pappaya.minimum.transport.config', 'branch_id',string="Transport Minimum Percentage")
    fine_type = fields.Selection([('day', 'Day'), ('week', 'Week'), ('month', 'Month')], string='Fine Type')
    fine_amount = fields.Float(string='Fine Amount')

    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')
    start_duration = fields.Selection([('am', 'AM'), ('pm', 'PM')], string='Start Duration', default='am')
    end_duration = fields.Selection([('am', 'AM'), ('pm', 'PM')], string='End Duration', default='pm')

    old_adm_branch_name = fields.Char('Old Admission Branch Name')
    old_hr_branch_name = fields.Char('Old HR Branch Name')

    credit_account_id = fields.Many2one('account.account', 'Credit Account')
    debit_account_id = fields.Many2one('account.account', 'Debit Account')
    co_credit_account_id = fields.Many2one('account.account', 'CO Credit Account')
    co_debit_account_id = fields.Many2one('account.account', 'CO Debit Account')

    
    
    
    @api.constrains('start_time', 'end_time')
    def check_branch_start_end_time(self):
        for record in self:
            if record.start_time and record.start_time > 12.0:
                raise ValidationError("Please enter valid Start Time.")
            if record.end_time and record.end_time > 12.0:
                raise ValidationError("Please enter valid End Time.")

    @api.one
    @api.constrains('document_followup')
    def check_document_followup(self):
        if self.document_followup:
            if self.document_followup < 0:
                raise ValidationError('Please enter the valid Count..!')

    is_gst_applicable = fields.Boolean('GST Applicable?')
#     @api.onchange('type_id','parent_id')
#     def onchange_type_id(self):
#         domain = {};domain['parent_id']=[('id','in',[])]
#         if self.type_id and type_id.parent_id:
    
    
    @api.onchange('parent_id')
    def onchnage_parent_id(self):
        for record in self:
            if record.type == 'branch':
                record.office_type_id = None
                if record.parent_id:
                    return {'domain':{'office_type_id':[('entity_id','=',record.parent_id.id)]}}
                else:
                    return {'domain':{'office_type_id':[('id','=',[])]}}
    
    
    @api.onchange('office_type_id')
    def onchange_office_type_id(self):
        if self.office_type_id:
            self.branch_workhours_line = False
            work_lines = []
            for work_hours in self.env['work.hours.officetype'].search([('office_type_id','=',self.office_type_id.id)]):
                for work in work_hours.work_hours_line:                    
                    work_lines.append(
                        (0, 0, {
                            'branch_id': self.id,
                            'employee_type':work_hours.employee_type.id,
                            'start_time': work_hours.start_time,
                            'start_duration': work_hours.start_duration,
                            'end_time':work_hours.end_time,
                            'end_duration': work_hours.end_duration,
                            'status_type': work.status_type,
                            'min_work_hours': work.min_work_hours,
                            'max_work_hours': work.max_work_hours,

                        })
                    )
            self.branch_workhours_line = work_lines

    @api.onchange('name')
    def onchange_name(self):
        if self.name and self.name.strip():
            self.name = str(self.name.strip()).upper()

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            self.district_id = self.pappaya_division_id = self.pappaya_mandal_id = None
    
    @api.onchange('state_district_id')
    def _onchange_state_district_id(self):
        if self.state_district_id:
            self.pappaya_division_id = False; self.pappaya_mandal_id = False
            division_ids = []
            for div_obj in self.env['pappaya.division'].search([]):
                if div_obj.district_ids_m2m.ids and self.state_district_id.id in div_obj.district_ids_m2m.ids:
                    division_ids.append(div_obj.id)
            return {'domain': {'pappaya_division_id': [('id', 'in', division_ids)]}}
    
    @api.onchange('pappaya_division_id')
    def _onchange_pappaya_division_id(self):
        self.pappaya_mandal_id = False
        if self.pappaya_division_id:
            print('self.pappaya_division_id.mandal_ids_m2m.ids : ', self.pappaya_division_id.mandal_ids_m2m)
#             mandal_ids = []
#             for man in self.pappaya_division_id.mandal_ids_m2m:
#                 mandal_ids.append(mandal_obj.id)
            return {'domain': {'pappaya_mandal_id': [('id', 'in', self.pappaya_division_id.mandal_ids_m2m.ids)]}}
    
    @api.onchange('pappaya_mandal_id')
    def _onchange_pappaya_mandal_id(self):
        if self.pappaya_mandal_id:
            self.pappaya_division_id = self.pappaya_mandal_id.pappaya_division_id.id
            self.state_district_id = self.pappaya_mandal_id.state_district_id.id
            self.state_id = self.pappaya_mandal_id.state_id.id
#             self.parent_id = self.search([('id','=',1)]).id    
    
    @api.depends('state_id','tem_state_id')
    def depends_state_id(self):
        if self.tem_state_id:
            self.state_id = self.tem_state_id.id
        if self.state_id:
            self.write({'tem_state_id':self.state_id.id})
    
    @api.onchange('tem_city_id','tem_state_id')
    def _onchange_tem_state_id(self):
        if self.tem_state_id or self.tem_city_id or self.tem_country_id:
            self.city = self.tem_city_id.id
            self.state_id = self.tem_state_id.id
            # self.tem_country_id = self.tem_state_id.country_id.id
            self.country_id = self.tem_country_id.id

    @api.onchange('tem_city_id')
    def _onchange_city(self):
        domain = []
        if self.tem_city_id:
            city_obj = self.env['pappaya.city'].search([('id', '=', self.tem_city_id.id)])
            for obj in city_obj:
                domain.append(obj.state_id.id)
            return {'domain': {'tem_state_id': [('id', 'in', domain)]}}
            
    @api.model
    def default_get(self, fields):
        res = super(OperatingUnitInherit, self).default_get(fields)
        res['type'] = self._context.get('type') or False
        return res
    @api.one
    def copy(self, default=None):
        raise ValidationError('You are not allowed to Duplicate')
    
    @api.onchange('residential_type_ids')
    def onchange_residential_type_ids(self):
        is_transport = False
        for residential_type_id in self.residential_type_ids:
            if residential_type_id.code in ['day','semi']:
                is_transport = True
                break;
        self.is_transport = is_transport

    ''' Start : Common Functions '''
    def change_date_format(self, your_date):
        date_year = your_date[:4]
        date_month = your_date[5:7]
        date_date = your_date[8:11]
        result = str(date_date) + '-' + str(date_month) + '-' + str(date_year) 
        return result

    # Returning date range list using from date and end date.
    def get_date_range(self, date_from, date_to):
        date_from_year = date_from[:4]
        date_from_month = date_from[5:7]
        date_from_date = date_from[8:11]
        
        date_to_year = date_to[:4]
        date_to_month = date_to[5:7]
        date_to_date = date_to[8:11]
        
        d1 = date(int(date_from_year), int(date_from_month), int(date_from_date))
        d2 = date(int(date_to_year), int(date_to_month), int(date_to_date))
        delta = d2 - d1
        date_range_list = []
        for i in range(delta.days + 1):
            r_date = d1 + td(days=i)
            date_range_list.append(str(r_date))
        return date_range_list
    
    def _validate_name(self, name):
        if name.strip():
            update_name = name.strip()
#             if not re.match('^[a-zA-Z\d\s]*$', name):
#                 raise ValidationError('Please enter a valid Name.')
#             else:
            name1 = ' '.join((update_name.strip()).split())
            name2 = name1[0].capitalize()
            update_name = name2 + name1[1:]
            return update_name
        else:
            return False
    
    def validate_zip(self, zip_code):
        invalid_pincode_list = ['000000','111111','222222','333333','444444','555555','666666','777777',
                        '888888','999999']
        if zip_code:
            match_zip_code = re.match('^[\d]*$', zip_code)
            if zip_code in invalid_pincode_list:
                raise ValidationError("Please enter a valid 6 digit Pin Code.")
            if not match_zip_code or len(zip_code) != 6:
                raise ValidationError("Please enter a valid 6 digit Pin Code.")
#            commented this based on mr.nivas's command by lokesh.
#             if not (zip_code.isdigit() and 100000 <= int(zip_code) <= 999999 and len(list(filter(lambda x: x[0] == x[1], [(zip_code[i], zip_code[i+2]) for i in range(3)]))) <= 1):
#                 raise ValidationError("Please enter a valid 6 digit Pin Code.")
            return True
        else:
            return False
    
    def validate_phone(self, phone_no):
        if phone_no:
            match_phone_no = re.match('^[\d-]*$', phone_no)
            if not match_phone_no or len(phone_no) != 12:
                raise ValidationError('Please enter a valid Phone number.')
            return True
        else:
            return False

    def validate_fax_id(self, fax_id):
        if fax_id:
            match_fax_no = re.match('^[\d-]*$', fax_id)
            if not match_fax_no or len(fax_id) != 12:
                raise ValidationError('Please enter a valid Fax number.')
            return True
        else:
            return False

    @api.onchange('mid_number')
    def onchange_mid_number(self):
        if self.mid_number:
            match_zip_code = re.match('^[\d]*$', self.mid_number)
            if not match_zip_code or len(self.mid_number) != 6:
                raise ValidationError("Please enter a valid 6 digit M.I.D.No")

    @api.onchange('tid_number')
    def onchange_tid_number(self):
        if self.tid_number:
            match_tid_number = re.match('^[\d]*$', self.tid_number)
            if not match_tid_number:
                raise ValidationError("Please enter a valid T.I.D.No")

    def validate_unique_id(self, unique_id):
        if unique_id:
            match_unique_id = re.match('^[\d]*$', unique_id)
            if not match_unique_id or len(unique_id) < 8:
                raise ValidationError('Please enter a valid Biometric ID.')
            return True
        else:
            return False

#     def validate_phone_country_code(self, phone_country_code):
#         if phone_country_code:
#             match_phone_country_code = re.match('^[\d]*$', phone_country_code)
#             if not match_phone_country_code or len(phone_country_code) < 3:
#                 raise ValidationError('Please enter a valid 3 digit STD code.')
#             return True
#         else:
#             return False
    
    def validate_mobile(self, mobile):
        if mobile:
            invalid_mobile_numbers = ['0000000000','1111111111','2222222222','3333333333','4444444444','5555555555','6666666666',
                                      '7777777777','8888888888','9999999999']
            match_mobile = re.match('^[\d]*$', mobile)
            if not match_mobile or len(mobile) != 10:
                raise ValidationError('Please enter a valid 10 digit mobile number.')
            if mobile in invalid_mobile_numbers:
                raise ValidationError('Please enter a valid 10 digit mobile number.')
            return True
        else:
            return False
        
    def validate_email(self, email):
        match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
        if match == None:
            raise ValidationError(_('Please enter a valid E-mail Address.'))
        return True
    
    def validation_student_aadhaar_no(self, aadhaar_no):
        if aadhaar_no:
            match_aadhaar_no = re.match('^[\d]*$', aadhaar_no)
            if not match_aadhaar_no or len(aadhaar_no) < 12:
                raise ValidationError( _("Please enter a valid 12 digit Aadhaar number"))
    ''' End : Common Functions '''
            
    @api.onchange('phone')
    def _onchange_phone(self):
        if self.phone:
            self.validate_phone(self.phone)

    @api.onchange('fax_id')
    def _onchange_fax_id(self):
        if self.fax_id:
            self.validate_fax_id(self.fax_id)

#     @api.onchange('phone_country_code')
#     def _onchange_phone_country_code(self):
#         if self.phone_country_code:
#             self.validate_phone_country_code(self.phone_country_code)

    @api.onchange('mobile')
    def _onchange_mobile(self):
        if self.mobile:
            self.validate_mobile(self.mobile)
    
    @api.onchange('email')
    def _onchange_email(self):
        if self.email:
            self.validate_email(self.email)
            
    @api.onchange('tem_zip')
    def _onchange_zip(self):
        if self.tem_zip:
            self.validate_zip(self.tem_zip)
            self.zip = self.tem_zip
    
    def _validate_vals(self, vals):
        if 'email' in vals.keys() and vals.get('email'):
#             if self.search([('email','=', vals.get('email'))]).id:
#                 raise ValidationError("The given Email Address already exists.")
            self.validate_email(vals.get('email'))
        if 'phone' in vals.keys() and vals.get('phone'):
            self.validate_phone(vals.get('phone'))
        if 'fax_id' in vals.keys() and vals.get('fax_id'):
            self.validate_fax_id(vals.get('fax_id'))
        if 'unique_id' in vals.keys() and vals.get('unique_id'):
            self.validate_unique_id(vals.get('unique_id'))
#         if 'phone_country_code' in vals.keys() and vals.get('phone_country_code'):
#             self.validate_phone_country_code(vals.get('phone_country_code'))
        if 'mobile' in vals.keys() and vals.get('mobile'):
            self.validate_mobile(vals.get('mobile'))
        if 'tem_zip' in vals.keys() and vals.get('tem_zip'):
            self.validate_zip(vals.get('zip'))
        return True
    
    @api.model
    def create(self, vals):
        if 'mid_number' in vals.keys() and vals.get('mid_number'):
            match_number = re.match('^[\d]*$', vals.get('mid_number'))
            if not match_number or len(vals.get('mid_number')) != 6:
                raise ValidationError('Please enter a valid 6 digit M.I.D.No')
            vals.update({'mid_number': vals.get('mid_number').strip()})
        if 'tid_umber' in vals.keys() and vals.get('tid_umber'):
            match_tid_number = re.match('^[\d]*$', vals.get('tid_umber'))
            if not match_tid_number:
                raise ValidationError('Please enter a valid 6 digit T.I.D.No')
            vals.update({'tid_number': vals.get('tid_number').strip()})
        self.sudo()._validate_vals(vals)
        if 'name' in vals.keys() and vals.get('name'):
            vals.update({'name': str(vals.get('name').strip()).upper()})        
        res = super(OperatingUnitInherit, self.sudo()).create(vals)
        
        if res.type == 'organization':
            entity_sequence =self.env['meta.data.master'].search([('name','=','organization')])
            if not entity_sequence:
                raise ValidationError(_("Please Configure Organization Sequence"))
            res['organization_sequence_id'] = self.env['ir.sequence'].next_by_code('pappaya.organization') or _('New')
            
        if res.type == 'entity':
            entity_sequence =self.env['meta.data.master'].search([('name','=','entity')])
            if not entity_sequence:
                raise ValidationError(_("Please Configure Entities Sequence"))
            res['entity_sequence_id'] = self.env['ir.sequence'].next_by_code('pappaya.entity') or _('New')
        if res.type == 'branch':
            branch_sequence =self.env['meta.data.master'].search([('name','=','branch')])
            if not branch_sequence:
                raise ValidationError(_("Please Configure Branch Sequence"))
            res['branch_sequence_id'] = self.env['ir.sequence'].next_by_code('pappaya.branch') or _('New')
        
        return res

    @api.multi
    def write(self, vals):
        if 'mid_number' in vals.keys() and vals.get('mid_number'):
            match_number = re.match('^[\d]*$', vals.get('mid_number'))
            if not match_number or len(vals.get('mid_number')) != 6:
                raise ValidationError('Please enter a valid 6 digit M.I.D.No')
            vals.update({'mid_number': vals.get('mid_number').strip()})
        if 'tid_umber' in vals.keys() and vals.get('tid_umber'):
            match_tid_number = re.match('^[\d]*$', vals.get('tid_umber'))
            if not match_tid_number:
                raise ValidationError('Please enter a valid 6 digit T.I.D.No')
            vals.update({'tid_number': vals.get('tid_number').strip()})
        self.sudo()._validate_vals(vals)
        if 'name' in vals.keys() and vals.get('name'):
            vals.update({'name': str(vals.get('name').strip()).upper()})
        return super(OperatingUnitInherit, self.sudo()).write(vals)

    @api.onchange('start_time','end_time')
    def onchange_time(self):
        if self.start_time < 0 or self.end_time < 0:
            raise ValidationError('Please enter the valid time..!')            

    @api.onchange('library_fee_amount')
    def onchange_library_fee_amount(self):
        if self.library_fee_amount < 0:
            raise ValidationError('Please enter the valid Library Fee Amount..!')  
        
    @api.onchange('cash_mode_limit')
    def onchange_cash_mode_limit(self):
        if self.cash_mode_limit < 0:
            raise ValidationError('Please enter the valid Cash Mode Limit..!') 

    @api.onchange('fine_amount','document_followup','record_id')
    def onchange_fine_amount(self):
        if self.fine_amount < 0 or self.document_followup < 0 or self.record_id <0:
            raise ValidationError('Please enter the valid Number..!')  
        
class PappayaBranchWorkedHoursLine(models.Model):
    _name = 'pappaya.branch.worked.hours.line'
    _rec_name = 'work_type'

    branch_id = fields.Many2one('operating.unit',string='Branch',domain=[('type','=','branch')])
    work_type = fields.Char('Type')
    total_work_hours = fields.Integer(string='Total Working Hours')
    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')
    start_duration = fields.Selection([('am','AM'),('pm','PM')], string='Start Duration', default='am')
    end_duration = fields.Selection([('am','AM'),('pm','PM')], string='End Duration', default='am')
    is_any_9hours = fields.Boolean('Is Any Hours', default=False)

    @api.constrains('total_work_hours')
    def check_total_work_hours(self):
        if self.total_work_hours < 8:
            raise ValidationError("Total Work should be more than 8 Hours")


class TransportInstallmentConfig(models.Model):
    _name = 'transport.installment.config'
    _description = 'Transport Installment Config'

    @api.constrains('due_date')
    def _check_due_date(self):
        if self.due_date and self.due_date < self.academic_year_id.start_date\
                or self.due_date > self.academic_year_id.end_date:
            raise ValidationError('Due Date should be within the academic year..!')

    branch_id = fields.Many2one('operating.unit', string='Branch')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year',
                            default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    due_date = fields.Date(string='Due Date')


class PappayaMinimumTransportConfig(models.Model):
    _name = 'pappaya.minimum.transport.config'

    @api.one
    @api.constrains('min_percentage', 'academic_year_id', 'branch_id')
    def check_valid_min_percentage(self):
        if self.min_percentage:
            if self.min_percentage < 0.0 or self.min_percentage > 100:
                raise ValidationError('Please enter the valid Percentage')
        if self.academic_year_id:
            if len(self.search([('branch_id', '=', self.branch_id.id),
                                ('academic_year_id', '=', self.academic_year_id.id)])) > 1:
                raise ValidationError('Academic Year is already exists for current branch..!')

    branch_id = fields.Many2one('operating.unit', 'Branch')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year',
                                       default=lambda self: self.env['academic.year'].search(
                                           [('is_active', '=', True)]))
    min_percentage = fields.Float('Minimum Percentage')

class pappaya_branch_ay_course_config(models.Model):
    _name = 'pappaya.branch.ay.course.config'
    
    operating_unit_id = fields.Many2one('operating.unit','Operating Unit')
    school_id = fields.Many2one('res.company', "Branch")
    academic_year_id = fields.Many2one('academic.year','Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    course_package_ids = fields.Many2many('pappaya.course.package', string="Course Package")
    reservation_min_percentage = fields.Float('Minimum Admission Percentage')
    active = fields.Boolean('Active',default=True)

    @api.one
    @api.constrains('reservation_min_percentage')
    def check_valid_min_percentage(self):
        if self.reservation_min_percentage:
            if self.reservation_min_percentage < 0.0 or self.reservation_min_percentage > 100:
                raise ValidationError('Please enter the valid Percentage')

    @api.onchange('reservation_min_percentage')
    def onchange_reservation_min_percentage(self):
        self.check_valid_min_percentage()

    @api.one
    @api.constrains('school_id', 'academic_year_id')
    def check_name_exists(self):
        if self.school_id.id and self.academic_year_id.id:
            if len(self.search([('school_id', '=', self.school_id.id),('academic_year_id', '=', self.academic_year_id.id)])) > 1:
                raise ValidationError('Course Configuration : \n Academic Year is already exists for current branch.\n You can edit the particular record and add Course Package instead of creating new record.')
            
            
            
class branch_segment_course_mapping(models.Model):
    _name = 'branch.segment.course.mapping'
    
    operating_unit_id = fields.Many2one('operating.unit','Operating Unit')
    branch_id = fields.Many2one('res.company', "Branch")
    fiscal_year_id = fields.Many2one('fiscal.year','Fiscal Year')
    programme_id = fields.Many2one('pappaya.programme', string="Programme")
    segment_id = fields.Many2one('pappaya.segment', string="Segment")
    course_package_ids = fields.Many2many('pappaya.course.package', string="Course Package")
    course_package_id = fields.Many2one('pappaya.course.package', string="Course Package")
    active = fields.Boolean('Active',default=True)
    
    @api.constrains('course_package_id')
    def check_name_course_package_id(self):
        if self.course_package_id.id :
            if len(self.search([('fiscal_year_id','=',self.fiscal_year_id.id),('operating_unit_id','=',self.operating_unit_id.id),('course_package_id', '=', self.course_package_id.id)])) > 1:
                raise ValidationError('The selected course package is already alloted')
    
    @api.onchange('course_package_id')
    def course_package_id_onchange(self):
        for record in self:
            if record.course_package_id:
                
                cgb_program         = self.env['pappaya.course.program'].search([('course_id','=',record.course_package_id.course_id.id),
                                                                         ('group_id','=',record.course_package_id.group_id.id),
                                                                         ('batch_id','=',record.course_package_id.batch_id.id)],limit=1)
                if cgb_program:
                    record.programme_id = cgb_program.program_id.id
                    record.segment_id   = cgb_program.course_id.segment_id.id
                else:
                    record.programme_id = None
                    record.segment_id   = None
                if record.course_package_id:
                    if len(self.search([('fiscal_year_id','=',record.fiscal_year_id.id),('operating_unit_id','=',record.operating_unit_id.id),('course_package_id', '=', record.course_package_id.id)])) > 1:
                        raise ValidationError('The selected course package is already alloted')
                    
                    
class branch_wise_job_vacancy(models.Model):
    _name = 'branch.wise.job.vecancy'
    
    branch_id       = fields.Many2one('operating.unit',domain=[('type','=','branch')])
    job_id          = fields.Many2one('hr.job')
    existing_count  = fields.Float()
    new_count       = fields.Float()
    


    
