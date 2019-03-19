# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import SUPERUSER_ID
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ResUsers(models.Model):
    _inherit = "res.users"
    _order = "id asc"

    # These two fields used for updating company_id in allowed companies based on user selection
    # school_id = fields.Many2one('res.company', 'School Name')
    super_admin = fields.Boolean('Super Admin')
    type = fields.Selection([('corporate', 'Corporate'), ('society', 'Society'), ('school', 'School')])
    phone = fields.Char('Phone', size=15)
    mobile = fields.Char(related='partner_id.mobile', inherited=True, size=10)
    #     phone_country_code = fields.Char()
    mobile_country_code = fields.Char(size=4)
    company_id = fields.Many2one('res.company', 'Company Name')
    image = fields.Binary('Street', related='partner_id.image', inherited=True)
    gender_id = fields.Many2one('pappaya.gender', 'Gender')
    birth_date = fields.Date('Date of Birth')
    street = fields.Char('Address 1', related='partner_id.street', inherited=True)
    street2 = fields.Char('Address 2', related='partner_id.street2', inherited=True)
    zip = fields.Char('Pin Code', size=6, related='partner_id.zip', inherited=True)
    city = fields.Char('City', related='partner_id.city', inherited=True)
    state_id = fields.Many2one("res.country.state", 'State')
    country_id = fields.Many2one("res.country", 'Country', default=lambda self: self.env.user.company_id.country_id)
    # state_id = fields.Many2one("res.country.state", 'State', related='partner_id.state_id', inherited=True)
    # country_id = fields.Many2one("res.country",'Country', related='partner_id.country_id', inherited=True)
    email = fields.Char(related='partner_id.email', inherited=True)
    # company_type = fields.Selection([('person', 'Staff'), ('company', 'School')], related='partner_id.company_type', inherited=True, string='User Type')
    middle_name = fields.Char('Middle Name', size=20)
    last_name = fields.Char('Last Name', size=20)
    date_of_joining = fields.Date('Date of Joining')
    notification_type = fields.Selection([('email', 'Handle by Emails'), ('inbox', 'Handle in Pappaya')],
                                         'Notification Management', required=True, default='email',
                                         help="Policy on how to handle Chatter notifications: - Emails: notifications are sent to your email - Pappaya: notifications appear in your Pappaya Inbox")
    # Access Right Groups
    pro_security_code = fields.Char(string='PRO Security Code')
    mobile_user_login_status = fields.Integer('Mobile User Login Status', default=1)
    yearwise_config_ids_o2m = fields.One2many('academic.yearwise.userconfig', 'user_id', 'Year wise Config')

    employee_id = fields.Many2one('hr.employee', "Employee")
    payroll_branch_id = fields.Many2one('pappaya.payroll.branch', 'Payroll Branch')
    admission_branch_ids_m2m = fields.Many2many('operating.unit', string='Admission Branches')

    """Mobile Offline Sync Status"""
    state_last_sync = fields.Datetime('State Last Sync')
    lead_course_last_sync = fields.Datetime('Lead Course Last Sync')
    lead_school_last_sync = fields.Datetime('Lead School Last Sync')
    district_last_sync = fields.Datetime('District Last Sync')
    city_last_sync = fields.Datetime('City Last Sync')
    ward_last_sync = fields.Datetime('Ward Last Sync')
    ward_area_last_sync = fields.Datetime('Ward Area Last Sync')
    mandal_last_sync = fields.Datetime('Mandal Last Sync')
    village_last_sync = fields.Datetime('Village Last Sync')
    branch_last_sync = fields.Datetime('Branch Last Sync')

    ''' User Group related fields '''
    # Marketing
    pro_user = fields.Boolean('PRO')
    pro_admin = fields.Boolean('PRO ADMIN')

    # HR
    hr_administrator = fields.Boolean('HR Administrator')
    hr_executives = fields.Boolean('HR Executive')
    hr_operations_head = fields.Boolean('HR Operation Head')
    hr_cpo = fields.Boolean('CPO')
    payroll_operation = fields.Boolean('Payroll Operation')
    payroll_head = fields.Boolean('Payroll Head')
    hr_branch_accountants = fields.Boolean('Branch Accountant')
    hr_zonal_accountant = fields.Boolean('Zonal Accountant')
    hr_principal_hod = fields.Boolean('Principal/HOD')
    hr_deans = fields.Boolean('Dean')
    hr_branch_employees = fields.Boolean('Employee')

    # Admission
    admission_administrator = fields.Boolean('Admission Administrator')
    admission_revenue_head = fields.Boolean('Revenue Head')
    admission_revenue_assistant = fields.Boolean('Revenue Assistant')
    admission_revenue_operation_head = fields.Boolean('Revenue Operation Head')
    admission_revenue_operation_assistant = fields.Boolean('Revenue Operation Assistant')
    admission_chamber = fields.Boolean('Chamber')
    ''' End '''

    @api.onchange('admission_branch_ids_m2m', 'payroll_branch_id')
    def onchange_admission_branch_ids_m2m(self):
        domain = {};
        domain['admission_branch_ids_m2m'] = [('id', 'in', [])]
        if self.payroll_branch_id:
            domain['admission_branch_ids_m2m'] = [('id', 'in', self.env['operating.unit'].search(
                [('tem_state_id', '=', self.payroll_branch_id.state_id.id)]).ids)]
        return {'domain': domain}

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if not self.employee_id:
            self.yearwise_config_ids_o2m = False

        vals = {}
        if self.employee_id:
            username = ''
            if self.employee_id.sur_name:
                username = (self.employee_id.sur_name + ' ' + self.employee_id.name).strip()
            else:
                username = self.employee_id.name
            vals.update({
                'street': self.employee_id.work_street,
                'street2': self.employee_id.work_street2,
                'city': self.employee_id.work_city_id.name,
                'state_id': self.employee_id.work_state_id.id,
                'zip': self.employee_id.work_zip,
                'country_id': self.employee_id.work_country_id.id,
                'birth_date': self.employee_id.birthday,
                'gender_id': self.employee_id.gender_id.id,
                'date_of_joining': self.employee_id.date_of_joining,
                'email': self.employee_id.work_email,
                'mobile': self.employee_id.work_mobile,
                'phone': self.employee_id.work_phone,
                'login': self.employee_id.emp_id,
                'name': username,
                'payroll_branch_id': self.employee_id.payroll_branch_id.id,
            })
            self.update(vals)

    @api.model
    def default_get(self, fields):
        res = super(ResUsers, self).default_get(fields)
        #         model, res_id = self.env['ir.model.data'].get_object_reference('base', 'in')
        #         if res_id:
        #             res['country_id'] = res_id
        return res

    @api.one
    @api.constrains('pro_security_code')
    def _check_pro_security_code_size(self):
        if self.pro_security_code and not len(self.pro_security_code) >= 20:
            raise ValidationError("PRO Security code should be minimum of 20 characters.")

    @api.one
    @api.constrains('email')
    def _check_unique_email(self):
        if self.email:
            if len(self.search([('email', '=', self.email)])) > 1:
                raise ValidationError("Email already exists")

    @api.multi
    @api.constrains('birth_date')
    def check_date(self):
        if self.birth_date:
            if datetime.strptime(self.birth_date, DEFAULT_SERVER_DATE_FORMAT).date() >= datetime.now().date():
                raise ValidationError('Please check the entered Date of Birth')

    @api.multi
    @api.constrains('date_of_joining')
    def check_date_of_joining(self):
        if self.date_of_joining:
            if datetime.strptime(self.date_of_joining, DEFAULT_SERVER_DATE_FORMAT).date() > datetime.now().date():
                raise ValidationError('Please enter a valid date of joining')

    @api.onchange('mobile')
    def _onchange_mobile(self):
        if self.mobile:
            self.env['res.company'].validate_mobile(self.mobile)

    @api.onchange('phone')
    def _onchange_phone(self):
        if self.phone:
            self.env['res.company'].validate_phone(self.phone)

    # @api.onchange('email')
    # def _onchange_email(self):
    #     if self.email:
    #         self.env['res.company'].validate_email(self.email)
    #         if self.search([('email','=',self.email)]).id:
    #             raise ValidationError("The given Email Address already exists")

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            self.env['res.company'].validate_zip(self.zip)

    def _validate_vals(self, vals):
        if 'email' in vals.keys() and vals.get('email'):
            if self.search([('email', '=', vals.get('email'))]).id:
                raise ValidationError("The given Email Address already exists")
            self.env['res.company'].validate_email(vals.get('email'))
        if 'mobile' in vals.keys() and vals.get('mobile'):
            self.env['res.company'].validate_mobile(vals.get('mobile'))
        if 'phone' in vals.keys() and vals.get('phone'):
            self.env['res.company'].validate_phone(vals.get('phone'))
        if 'zip' in vals.keys() and vals.get('zip'):
            self.env['res.company'].validate_zip(vals.get('zip'))
        if 'name' in vals.keys() and vals.get('name'):
            self.env['res.company']._validate_name(vals.get('name'))
        if 'middle_name' in vals.keys() and vals.get('middle_name'):
            self.env['res.company']._validate_name(vals.get('middle_name'))
        if 'last_name' in vals.keys() and vals.get('last_name'):
            self.env['res.company']._validate_name(vals.get('last_name'))
        return True

    @api.onchange('name', 'middle_name', 'last_name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name
        if self.middle_name:
            middle_name = self.env['res.company']._validate_name(self.middle_name)
            self.middle_name = middle_name
        if self.last_name:
            last_name = self.env['res.company']._validate_name(self.last_name)
            self.last_name = last_name

    def _get_groups(self, existing_user_base_groups, groups):
        group_ids = existing_user_base_groups
        for g in groups:
            group = self.env.ref(g, raise_if_not_found=False)
            if group:
                group_ids.append(group.id)
        return [[6, False, group_ids]]

    @api.onchange('login')
    def onchange_login(self):
        if self.login and self.employee_id:
            if not self.login == self.employee_id.emp_id:
                self.login = self.employee_id.emp_id
                return {
                    'warning': {'title': _('Warning'), 'message': _('Login ID should be Employee ID.'), },
                }

    @api.model
    def create(self, vals):
        self._validate_vals(vals)
        vals.update({'password': vals.get('login') or 'a', 'pro_user': True, })
        # vals.update({'password':vals.get('login') or 'a',})
        # Updating Security Groups
        groups = []
        # Markting
        if 'pro_user' in vals and vals.get('pro_user'):
            groups.append('pappaya_base.marketing_pro_user')
        if 'pro_admin' in vals and vals.get('pro_admin'):
            groups.append('pappaya_base.marketing_pro_admin')

        # HR
        if 'hr_administrator' in vals and vals.get('hr_administrator'):
            groups.append('pappaya_base.hr_administrator')
        if 'hr_executives' in vals and vals.get('hr_executives'):
            groups.append('pappaya_base.hr_executives')
        if 'hr_operations_head' in vals and vals.get('hr_operations_head'):
            groups.append('pappaya_base.hr_operations_head')
        if 'hr_cpo' in vals and vals.get('hr_cpo'):
            groups.append('pappaya_base.hr_cpo')
        if 'payroll_operation' in vals and vals.get('payroll_operation'):
            groups.append('pappaya_base.payroll_operation')
        if 'payroll_head' in vals and vals.get('payroll_head'):
            groups.append('pappaya_base.payroll_head')
        if 'hr_branch_accountants' in vals and vals.get('hr_branch_accountants'):
            groups.append('pappaya_base.hr_branch_accountants')
        if 'hr_zonal_accountant' in vals and vals.get('hr_zonal_accountant'):
            groups.append('pappaya_base.hr_zonal_accountant')
        if 'hr_principal_hod' in vals and vals.get('hr_principal_hod'):
            groups.append('pappaya_base.hr_principal_hod')
        if 'hr_deans' in vals and vals.get('hr_deans'):
            groups.append('pappaya_base.hr_deans')
        if 'hr_branch_employees' in vals and vals.get('hr_branch_employees'):
            groups.append('pappaya_base.hr_branch_employees')

        # Admission
        if 'admission_administrator' in vals and vals.get('admission_administrator'):
            groups.append('pappaya_base.group_admission_admin')
        if 'admission_revenue_head' in vals and vals.get('admission_revenue_head'):
            groups.append('pappaya_base.group_admission_revenue_head')
        if 'admission_revenue_assistant' in vals and vals.get('admission_revenue_assistant'):
            groups.append('pappaya_base.group_admission_revenue_assistant')
        if 'admission_revenue_operation_head' in vals and vals.get('admission_revenue_operation_head'):
            groups.append('pappaya_base.group_admission_revenue_operation_head')
        if 'admission_revenue_operation_assistant' in vals and vals.get('admission_revenue_operation_assistant'):
            groups.append('pappaya_base.group_admission_revenue_operation_assistant')
        if 'admission_chamber' in vals and vals.get('admission_chamber'):
            groups.append('pappaya_base.group_admission_chamber')

        if groups:
            vals.update({'groups_id': self._get_groups([], groups)})
        elif 'active' in vals and not groups:
            raise ValidationError("Please select at least one 'User Role'.")
        return super(ResUsers, self).create(vals)

    @api.multi
    def write(self, vals):
        self._validate_vals(vals)
        groups = [
            # Marketing
            'pappaya_base.marketing_pro_user', 'pappaya_base.marketing_pro_admin',
            # HR
            'pappaya_base.hr_administrator', 'pappaya_base.hr_executives',
            'pappaya_base.hr_operations_head', 'pappaya_base.hr_cpo',
            'pappaya_base.payroll_operation', 'pappaya_base.payroll_head',
            'pappaya_base.hr_branch_accountants', 'pappaya_base.hr_zonal_accountant',
            'pappaya_base.hr_principal_hod', 'pappaya_base.hr_deans', 'pappaya_base.hr_branch_employees',
            # Admission
            'pappaya_base.group_admission_admin', 'pappaya_base.group_admission_revenue_head',
            'pappaya_base.group_admission_revenue_assistant', 'pappaya_base.group_admission_revenue_operation_head',
            'pappaya_base.group_admission_revenue_operation_assistant', 'pappaya_base.group_admission_chamber',
        ]
        # ***************************** Marketing Management *****************************
        if 'pro_user' in vals and not vals.get('pro_user') or not self.pro_user:
            groups.remove('pappaya_base.marketing_pro_user')
            if 'pro_user' in vals and vals.get('pro_user'):
                groups.append('pappaya_base.marketing_pro_user')
        if 'pro_admin' in vals and not vals.get('pro_admin') or not self.pro_admin:
            groups.remove('pappaya_base.marketing_pro_admin')
            if 'pro_admin' in vals and vals.get('pro_admin'):
                groups.append('pappaya_base.marketing_pro_admin')
        # ***************************** HR Management ***********************************
        if 'hr_administrator' in vals and not vals.get('hr_administrator') or not self.hr_administrator:
            groups.remove('pappaya_base.hr_administrator')
            if 'hr_administrator' in vals and vals.get('hr_administrator'):
                groups.append('pappaya_base.hr_administrator')

        if 'hr_executives' in vals and not vals.get('hr_executives') or not self.hr_executives:
            groups.remove('pappaya_base.hr_executives')
            if 'hr_executives' in vals and vals.get('hr_executives'):
                groups.append('pappaya_base.hr_executives')

        if 'hr_operations_head' in vals and not vals.get('hr_operations_head') or not self.hr_operations_head:
            groups.remove('pappaya_base.hr_operations_head')
            if 'hr_operations_head' in vals and vals.get('hr_operations_head'):
                groups.append('pappaya_base.hr_operations_head')

        if 'hr_cpo' in vals and not vals.get('hr_cpo') or not self.hr_cpo:
            groups.remove('pappaya_base.hr_cpo')
            if 'hr_cpo' in vals and vals.get('hr_cpo'):
                groups.append('pappaya_base.hr_cpo')

        if 'payroll_operation' in vals and not vals.get('payroll_operation') or not self.payroll_operation:
            groups.remove('pappaya_base.payroll_operation')
            if 'payroll_operation' in vals and vals.get('payroll_operation'):
                groups.append('pappaya_base.payroll_operation')

        if 'payroll_head' in vals and not vals.get('payroll_head') or not self.payroll_head:
            groups.remove('pappaya_base.payroll_head')
            if 'payroll_head' in vals and vals.get('payroll_head'):
                groups.append('pappaya_base.payroll_head')

        if 'hr_branch_accountants' in vals and not vals.get('hr_branch_accountants') or not self.hr_branch_accountants:
            groups.remove('pappaya_base.hr_branch_accountants')
            if 'hr_branch_accountants' in vals and vals.get('hr_branch_accountants'):
                groups.append('pappaya_base.hr_branch_accountants')

        if 'hr_zonal_accountant' in vals and not vals.get('hr_zonal_accountant') or not self.hr_zonal_accountant:
            groups.remove('pappaya_base.hr_zonal_accountant')
            if 'hr_zonal_accountant' in vals and vals.get('hr_zonal_accountant'):
                groups.append('pappaya_base.hr_zonal_accountant')

        if 'hr_principal_hod' in vals and not vals.get('hr_principal_hod') or not self.hr_principal_hod:
            groups.remove('pappaya_base.hr_principal_hod')
            if 'hr_principal_hod' in vals and vals.get('hr_principal_hod'):
                groups.append('pappaya_base.hr_principal_hod')

        if 'hr_deans' in vals and not vals.get('hr_deans') or not self.hr_deans:
            groups.remove('pappaya_base.hr_deans')
            if 'hr_deans' in vals and vals.get('hr_deans'):
                groups.append('pappaya_base.hr_deans')

        if 'hr_branch_employees' in vals and not vals.get('hr_branch_employees') or not self.hr_branch_employees:
            groups.remove('pappaya_base.hr_branch_employees')
            if 'hr_branch_employees' in vals and vals.get('hr_branch_employees'):
                groups.append('pappaya_base.hr_branch_employees')

        # ***************************** Admission ***********************************
        if 'admission_administrator' in vals and not vals.get('admission_administrator') or \
                not self.admission_administrator:
            groups.remove('pappaya_base.group_admission_admin')
            if 'admission_administrator' in vals and vals.get('admission_administrator'):
                groups.append('pappaya_base.group_admission_admin')

        if 'admission_revenue_head' in vals and not vals.get('admission_revenue_head') or \
                not self.admission_revenue_head:
            groups.remove('pappaya_base.group_admission_revenue_head')
            if 'admission_revenue_head' in vals and vals.get('admission_revenue_head'):
                groups.append('pappaya_base.group_admission_revenue_head')

        if 'admission_revenue_assistant' in vals and not vals.get('admission_revenue_assistant') or \
                not self.admission_revenue_assistant:
            groups.remove('pappaya_base.group_admission_revenue_assistant')
            if 'admission_revenue_assistant' in vals and vals.get('admission_revenue_assistant'):
                groups.append('pappaya_base.group_admission_revenue_assistant')

        if 'admission_revenue_operation_head' in vals and not vals.get('admission_revenue_operation_head') or \
                not self.admission_revenue_operation_head:
            groups.remove('pappaya_base.group_admission_revenue_operation_head')
            if 'admission_revenue_operation_head' in vals and vals.get('admission_revenue_operation_head'):
                groups.append('pappaya_base.group_admission_revenue_operation_head')

        if 'admission_revenue_operation_assistant' in vals and not vals.get('admission_revenue_operation_assistant') or \
                not self.admission_revenue_operation_assistant:
            groups.remove('pappaya_base.group_admission_revenue_operation_assistant')
            if 'admission_revenue_operation_assistant' in vals and vals.get('admission_revenue_operation_assistant'):
                groups.append('pappaya_base.group_admission_revenue_operation_assistant')

        if 'admission_chamber' in vals and not vals.get('admission_chamber') or not self.admission_chamber:
            groups.remove('pappaya_base.group_admission_chamber')
            if 'admission_chamber' in vals and vals.get('admission_chamber'):
                groups.append('pappaya_base.group_admission_chamber')

        if groups:
            ir_module_category_ids = [];
            existing_base_groups = []
            try:
                # category_domain = ['Narayana Marketing Management', 'HR &amp; Payroll Management', 'Admission']
                ir_module_category_ids = self.env['ir.module.category'].sudo().search(
                    [('sequence', 'in', (301, 302, 303))]).ids
            except:
                pass
            pappaya_groups = self.env['res.groups'].sudo().search([('category_id', 'in', ir_module_category_ids)]).ids
            existing_user_groups = self.groups_id
            for eug in existing_user_groups:
                if eug.id not in pappaya_groups and eug.id not in existing_base_groups:
                    existing_base_groups.append(eug.id)

            vals.update({'groups_id': self._get_groups(existing_base_groups, groups)})

        # End
        if 'password' in vals and 'mobile_user_login_status' not in vals:
            vals.update({'mobile_user_login_status': 2})
        return super(ResUsers, self).write(vals)

    """ Purpose : Hiding 'Administrator' record in many2one fields. """

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if SUPERUSER_ID != self._uid:
            args += ([('id', '!=', 1)])
        mids = self.search(args)
        return mids.name_get()

    """ Purpose : Hiding 'Administrator' record when other user login and try to view in users menu if login user has access to view users menu. """
    #     @api.model
    #     def search(self, args, offset=0, limit=None, order=None, count=False):
    #         if SUPERUSER_ID != self._uid:
    #             args += [('id', '!=', 1)]
    #         return super(ResUsers, self).search(args, offset, limit, order, count=count)

    ''' Purpose: Restricting every users to not to delete "Administrator" record '''

    @api.multi
    def unlink(self):
        for user in self:
            if user.id == 1:
                raise ValidationError(
                    "Sorry, You are not allowed to delete it.\nThis record is considered as master configuration.")
        return super(ResUsers, self).unlink()


class academiYearwiseuserConfig(models.Model):
    _name = 'academic.yearwise.userconfig'
    _description = 'Academic Yearwise User Configuration'
    _rec_name = 'academic_year_id'

    @api.model
    def default_get(self, fields):
        res = super(academiYearwiseuserConfig, self).default_get(fields)
        if 'payroll_branch_id' in self._context and self._context['payroll_branch_id']:
            res['payroll_branch_id'] = self._context.get('payroll_branch_id') or False
        return res

    user_id = fields.Many2one('res.users', 'User ID')
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1,
                                       default=lambda self: self.env['academic.year'].search(
                                           [('is_active', '=', True)]))
    payroll_branch_id = fields.Many2one('pappaya.payroll.branch', 'Payroll Branch')
    admission_branch_ids_m2m = fields.Many2many('operating.unit', string='Admission Branches')

    @api.onchange('admission_branch_ids_m2m', 'payroll_branch_id')
    def onchange_admission_branch_ids_m2m(self):
        domain = {};
        domain['admission_branch_ids_m2m'] = [('id', 'in', [])]
        domain['payroll_branch_id'] = [('id', 'in', [])]
        if self.payroll_branch_id:
            domain['payroll_branch_id'] = [('id', 'in', [self.payroll_branch_id.id])]
            if 'payroll_branch_id' in self._context and self._context['payroll_branch_id']:
                domain['payroll_branch_id'] = [('id', 'in', [self._context['payroll_branch_id']])]
            domain['admission_branch_ids_m2m'] = [('id', 'in', self.env['res.company'].sudo().search(
                [('id', '!=', 1), ('tem_state_id', '=', self.payroll_branch_id.state_id.id)]).ids)]
        return {'domain': domain}

    @api.constrains('academic_year_id')
    def validate_duplicate(self):
        if self.academic_year_id and self.sudo().search_count(
                [('user_id', '=', self.user_id.id), ('academic_year_id', '=', self.academic_year_id.id)]) > 1:
            raise ValidationError("Record already exists for given academic year.")


class ChangePasswordUserInherit(models.TransientModel):
    _inherit = 'change.password.user'

    @api.multi
    def change_password_button(self):
        for line in self:
            if not line.new_passwd:
                raise UserError(_("Before clicking on 'Change Password', you have to write a new password."))
            line.user_id.sudo().write({'password': line.new_passwd})
        self.write({'new_passwd': False})
