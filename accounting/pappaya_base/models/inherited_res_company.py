# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, except_orm,  UserError
import re
from datetime import date, timedelta as td
from email import encoders
from email.charset import Charset
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formataddr, formatdate, getaddresses, make_msgid
import logging
import re
import smtplib
import threading
from odoo.tools import ustr, pycompat

_logger = logging.getLogger(__name__)
_test_logger = logging.getLogger('odoo.tests')

SMTP_TIMEOUT = 60

class BranchBankAccountMapping(models.Model):
    _name = "branch.bank.account.mapping"
    _rec_name = 'bank_id'
    
    operating_unit_id = fields.Many2one('operating.unit','Operating Unit')
    
    branch_id = fields.Many2one('operating.unit','Branch', ondelete="cascade")

    bank_id = fields.Many2one('res.bank','Bank')
    account_no_id = fields.Many2one('res.partner.bank','Bank Account No')
    type = fields.Selection([('deposit','DEPOSIT'), ('entity','WITH DRAWAL')], "Bank Type")
    is_local_bank = fields.Boolean(string='Is Local Bank?')
    bank_account_branch_id = fields.Many2one('bank.account.branch','Bank Account Branch')
    
    is_card = fields.Boolean(string='Is card?')
    # Paymode Configuration fields
    bank_machine_id = fields.Many2one('bank.machine', string='Bank Machine')
    bank_machine_type_id = fields.Many2one('pappaya.master', string='Machine Type',related='bank_machine_id.bank_machine_type_id')
    mid_number = fields.Char(string='M.I.D.No(last 6 digits)', size=6)
    tid_number = fields.Char(string='T.I.D.No',)
    credit_account_id = fields.Many2one('account.account', 'Credit Account')
    debit_account_id = fields.Many2one('account.account', 'Debit Account')
    
    @api.onchange('is_card')
    def onchange_is_card(self):
        if not self.is_card:
            self.bank_machine_id = None; self.bank_machine_type_id = None; self.mid_number = None; self.tid_number = None;
            
    @api.onchange('bank_id')
    def onchange_bank_id(self):
        if self.bank_id:
            self.account_no_id = None; self.bank_account_branch_id = None
            self.bank_account_branch_id = self.account_no_id.bank_acc_branch_id.id
            return {'domain': {'account_no_id': [('bank_id', '=', self.bank_id.id)]}}
    
    @api.onchange('account_no_id')
    def onchange_account_no_id(self):
        if self.account_no_id:
            self.bank_account_branch_id = None
            self.bank_account_branch_id = self.account_no_id.bank_acc_branch_id.id
            return {'domain': {'bank_account_branch_id': [('id', '=', self.account_no_id.bank_acc_branch_id.id)]}}
        
class ResCompany(models.Model):
    _inherit = "res.company"
    _order = "name asc"

    type = fields.Selection([('organization','Organization'), ('entity','Entity'), ('branch','Branch')], default=lambda self: self._context.get('type'))
    parent_company = fields.Boolean('Parent Company')
    code = fields.Char(size=10, string='Code')
    active_academic_year_id = fields.Many2one('academic.year',string='Active Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    active_next_academic_year_id = fields.Many2one('academic.year','Next Active Academic Year')
    record_id = fields.Integer('ID')
    emp_no_ref = fields.Char('Created Employee ID', size=9)
    currency_id = fields.Many2one('res.currency', string='Currency Name', default=lambda self: self.env.user.company_id.currency_id)
    mobile_country_code = fields.Char('')
    name = fields.Char(size=35, string='Organization Name')
    phone = fields.Char('Phone', size=15)
    mobile = fields.Char('Mobile', size=10)
    email = fields.Char('Email', size=64)    
    fax_id = fields.Char('Fax ID')
    zip = fields.Char('Pin Code',size=6)
    state_id = fields.Many2one('res.country.state', string="State")
    country_id = fields.Many2one('res.country', string="Country")
    # Address fields
    tem_street = fields.Char('Address 1')
    tem_street2 = fields.Char('Address 2')
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
    student_type = fields.Selection([('day','Day'),('hostel','Hostel'),('both','Both')],'Student Type')
    gender = fields.Selection([('boys', 'Boys'),('girls','Girls'),('co_education','Co-Education')], 'Branch Type')
    medium_ids = fields.Many2many('pappaya.master', string='Medium')
    is_transport = fields.Boolean('Is Transport Applicable?')
    is_nslate = fields.Boolean('Is Nslate Applicable?')
    is_caution_deposit = fields.Boolean('Is Caution Deposit Applicable?')
    course_config_ids = fields.One2many('pappaya.branch.ay.course.config', 'operating_unit_id',string="Course Configuration")
    segment_cource_mapping_ids = fields.One2many('branch.segment.course.mapping', 'branch_id',string="Segment Course Mapping")
    parent_id = fields.Many2one('res.company')
    dhobi_provider_ids = fields.Many2many('pappaya.dhobi.provider', string='Dhobi Provider')

    # Working Days
    days_monday = fields.Boolean('Monday', default=True)
    days_tuesday = fields.Boolean('Tuesday',default=True)
    days_wednesday = fields.Boolean('Wednesday',default=True)
    days_thursday = fields.Boolean('Thursday',default=True)
    days_friday = fields.Boolean('Friday',default=True)
    days_saturday = fields.Boolean('Saturday')
    days_sunday = fields.Boolean('Sunday')
    # ~ worked_hours_line = fields.One2many('pappaya.branch.worked.hours.line','branch_id', string='Worked Hours')

    # legal_entity_id = fields.Many2one('pappaya.legal.entity', string="Legal Entity")
    stream_ids = fields.Many2many('pappaya.stream', 'res_company_stream_rel', 'branch_id', 'stream_id', string='Stream')
    office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    programme_type_ids = fields.Many2many('pappaya.programme', string="Programme")
    segment_type_ids = fields.Many2many('pappaya.segment', string="Segment")
    rfid_device_ip = fields.Text('UHFID Configuration IPs',size=200)

    branch_count = fields.Integer(string='Branch Count', compute='_branch_count')
    entity_description = fields.Char('Entity Description', size=100)
    organization_sequence_id = fields.Char(string='Organization Series')
    entity_sequence_id = fields.Char(string='Entity Series')
    branch_sequence_id = fields.Char(string='Branch Series')
    document_followup = fields.Integer(string='Document Follow Up')
    last_execution_date = fields.Date(string='Last Execution Date')
    
    # Transaction Related Fields
    paymode_ids = fields.Many2many('pappaya.paymode', string='Paymode')
    is_library_fee = fields.Boolean('Library Fee')
    library_fee_amount = fields.Float('Library Fee Amount')
    # Paymode Configuration fields
    bank_machine_id = fields.Many2one('bank.machine', string='Bank Machine')
    bank_machine_type_id = fields.Many2one('pappaya.master', string='Bank Machine Type', related='bank_machine_id.bank_machine_type_id')
    mid_no = fields.Integer(string='M.I.D.No(last 6 digits)')
    tid_no = fields.Integer(string='T.I.D.No')
    bank_account_mapping_ids = fields.One2many('branch.bank.account.mapping', 'branch_id', string='Bank Account Mapping')
    paytm_institute_name = fields.Char('Paytm Institue Name', default='NARAYANA')
    
    @api.multi
    @api.depends('branch_count')
    def _branch_count(self):
        branch_list = []
        for rec in self:
            for obj in self.search([('type','=','branch'),('parent_id','=',rec.id)]):
                branch_list.append(obj.id)
            rec.branch_count = len(branch_list)

    @api.one
    @api.constrains('document_followup')
    def check_document_followup(self):
        if self.document_followup:
            if self.document_followup < 0:
                raise ValidationError('Please enter the valid Count..!')

    @api.multi
    def action_branch_view(self):
        self.ensure_one()
        tree_view_id = self.env.ref('pappaya_base.view_pappaya_branch_tree').id
        form_view_id = self.env.ref('pappaya_base.view_pappaya_branch_form').id
        form_search_id = self.env.ref('pappaya_base.view_pappaya_branch_search').id
        return {
            'name': _('Branch'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [[tree_view_id, 'tree'], [form_view_id, 'form'], [form_search_id, 'search']],
            'target': 'current',
            'res_model': 'res.company',
            'domain': [('type','=','branch'),('parent_id','=',self.id)],
        }
    
    @api.onchange('name')
    def onchange_name(self):
        if self.name and self.name.strip():
            self.name = str(self.name.strip()).upper()

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            self.state_district_id = False; self.pappaya_division_id = False; self.pappaya_mandal_id = False
    
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
    
#     @api.onchange('branch_type')
#     def _onchange_branch_type(self):
#         if self.branch_type:
#             self.parent_id = self.search([('parent_company','=',True)]).id
    
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

    @api.one
    def copy(self, default=None):
        raise ValidationError('You are not allowed to Duplicate')

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
            match_zip_code = re.match('^[0-9]*$', zip_code)
            if zip_code in invalid_pincode_list:
                raise ValidationError("Please enter a valid 6 digit Zipcode.")
            if not match_zip_code or len(zip_code) != 6:
                raise ValidationError("Please enter a valid 6 digit Zipcode.")
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
            if self.search([('email','=', vals.get('email'))]).id:
                raise ValidationError("The given Email Address already exists.")
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
        self._validate_vals(vals)
        if 'name' in vals.keys() and vals.get('name'):
            vals.update({'name': str(vals.get('name').strip()).upper()})
        res = super(ResCompany, self.sudo()).create(vals)
        
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
        
#         if res:
#             if res.type == 'school':
#                 for user_obj in self.env['res.users'].search([('type','in',['corporate', 'society'])]):
#                     self._cr.execute('insert into res_company_users_rel (user_id,cid) values(%s,%s)',(user_obj.id,res.id))
        return res

    @api.multi
    def write(self, vals):
        self._validate_vals(vals)
        if 'name' in vals.keys() and vals.get('name'):
            vals.update({'name': str(vals.get('name').strip()).upper()})
        return super(ResCompany, self.sudo()).write(vals)
    
    ''' Purpose: Restricting users to not to delete 'Pappaya company' record. '''
    @api.multi
    def unlink(self):
        for company in self:
            if company.parent_company or company.id ==1:
                raise ValidationError(_("This record is considered as master record.\nYou are not allowed to delete it."))
        return super(ResCompany, self).unlink()
    
    ''' 
        Purpose: Displaying company records based on context given in many2one fields (based on current login user's company)
                 1) "get_school_list" : It will load only required school list 
                 2) "get_corporate_list" : Used to load only corporate list
                 3) "get_society_list" : Used to load only Branch list.
        Example :    <field name="school_id" context="{'get_school_list':1}"    options="{'no_open':True, 'no_create':True}"/>
    '''
#     @api.model
#     def name_search(self, name, args=None, operator='ilike', limit=100):
#         user_id = self.env['res.users'].sudo().browse(self.env.uid)
#         if self.env.context.get('get_school_list', False):
#             search_domain = [('type', '=', 'school')]
#             if user_id.company_id.parent_company:
#                 pass
#             elif user_id.company_id.type in ['corporate', 'society']:
#                 search_domain.append(('parent_id','=', user_id.company_id.id))
#             elif user_id.company_id.type == 'school':
#                 search_domain.append(('id','=', user_id.company_id.id))
#             records = self.search(search_domain)
#             return records.name_get()
# #         if self.env.context.get('get_corporate_and_school_list', False):
# #             search_domain = [('type', 'in', ['corporate','school']),('id', '!=', self.search([('parent_company','=',True)]).id)]
# #             records = self.search(search_domain)
# #             return records.name_get()
#         return super(ResCompany, self).name_search(name, args, operator=operator, limit=limit)
    
#     @api.multi
#     @api.depends('name', 'type', 'code')
#     def name_get(self):
#         result = []
#         for company in self:
#             if company.name and company.code and company.type:
#                 name = str(company.code)+ ' ' + str(company.name) + ' ' + str(company.type).title()
#             else:
#                 name = company.name
#             result.append((company.id, name))
#         return result









class MailTemplateInherit(models.Model):
    _inherit = 'mail.template'

    # def _get_default_email_from(self):
    #     outgoing_email = self.env['ir.mail_server'].search([('id','=',1)])
    #     if outgoing_email:
    #         email_from = outgoing_email.smtp_user
    #         return email_from
    #     return

    @api.multi
    def compute_email_from(self):
        for record in self:
            outgoing_email = self.env['ir.mail_server'].search([('id', '=', 1)])
            if outgoing_email:
                email_from = outgoing_email.smtp_user
                record.email_from = email_from
                record.reply_to = email_from
        return

    email_from = fields.Char('From', compute='compute_email_from', help="Sender address (placeholders may be used here). If not set, the default "
                                  "value will be the author's email alias if configured, or email address.", readonly=False)

    reply_to = fields.Char('Reply-To', compute='compute_email_from', help="Preferred response address (placeholders may be used here)")





class MailDeliveryException(except_orm):
    """Specific exception subclass for mail delivery errors"""
    def __init__(self, name, value):
        super(MailDeliveryException, self).__init__(name, value)

# Python 3: patch SMTP's internal printer/debugger
def _print_debug(self, *args):
    _logger.debug(' '.join(str(a) for a in args))
smtplib.SMTP._print_debug = _print_debug

# Python 2: replace smtplib's stderr
class WriteToLogger(object):
    def write(self, s):
        _logger.debug(s)
smtplib.stderr = WriteToLogger()

def is_ascii(s):
    return all(ord(cp) < 128 for cp in s)

def encode_header(header_text):
    if not header_text:
        return ""
    header_text = ustr(header_text) # FIXME: require unicode higher up?
    if is_ascii(header_text):
        return pycompat.to_native(header_text)
    return Header(header_text, 'utf-8')

def encode_header_param(param_text):
    if not param_text:
        return ""
    param_text = ustr(param_text) # FIXME: require unicode higher up?
    if is_ascii(param_text):
        return pycompat.to_native(param_text) # TODO: is that actually necessary?
    return Charset("utf-8").header_encode(param_text)

address_pattern = re.compile(r'([^ ,<@]+@[^> ,]+)')

def extract_rfc2822_addresses(text):
    """Returns a list of valid RFC2822 addresses
       that can be found in ``source``, ignoring
       malformed ones and non-ASCII ones.
    """
    if not text:
        return []
    candidates = address_pattern.findall(ustr(text))
    return [c for c in candidates if is_ascii(c)]


def encode_rfc2822_address_header(header_text):
    def encode_addr(addr):
        name = Header(pycompat.to_text(name)).encode()
        return formataddr((name, email))

    addresses = getaddresses([pycompat.to_native(ustr(header_text))])
    return COMMASPACE.join(encode_addr(a) for a in addresses)



class IrMailServerInherit(models.Model):
    _inherit = "ir.mail_server"


    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False,
                   smtp_session=None):
        smtp_from = message['From'] or message['Return-Path'] or self._get_default_bounce_address()
        assert smtp_from, "The Return-Path or From header is required for any outbound email"

        from_rfc2822 = extract_rfc2822_addresses(smtp_from)
        assert from_rfc2822, ("Malformed 'Return-Path' or 'From' address: %r - "
                              "It should contain one valid plain ASCII email") % smtp_from

        smtp_from = from_rfc2822[-1]
        email_to = message['To']
        email_cc = message['Cc']
        email_bcc = message['Bcc']
        del message['Bcc']

        smtp_to_list = [
            address
            for base in [email_to, email_cc, email_bcc]
            for address in extract_rfc2822_addresses(base)
            if address
        ]
        assert smtp_to_list, self.NO_VALID_RECIPIENT

        x_forge_to = message['X-Forge-To']
        if x_forge_to:
            # `To:` header forged, e.g. for posting on mail.channels, to avoid confusion
            del message['X-Forge-To']
            del message['To']  # avoid multiple To: headers!
            message['To'] = x_forge_to

        # Do not actually send emails in testing mode!
        if getattr(threading.currentThread(), 'testing', False) or self.env.registry.in_test_mode():
            _test_logger.info("skip sending email in test mode")
            return message['Message-Id']

        try:
            message_id = message['Message-Id']
            smtp = smtp_session
            try:
                smtp = smtp or self.connect(
                    smtp_server, smtp_port, smtp_user, smtp_password,
                    smtp_encryption, smtp_debug, mail_server_id=mail_server_id)
                smtp.sendmail(smtp_from, smtp_to_list, message.as_string())
            finally:
                # do not quit() a pre-established smtp_session
                if smtp is not None and not smtp_session:
                    smtp.quit()
        except Exception as e:
            params = (ustr(smtp_server), e.__class__.__name__, ustr(e))
            msg = _("Mail delivery failed via SMTP server '%s'.\n%s: %s") % params
            _logger.info(msg)
            raise MailDeliveryException(_("Mail Delivery Failed"), msg)
        return message_id
