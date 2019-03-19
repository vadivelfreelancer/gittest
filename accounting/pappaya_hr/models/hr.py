# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta as td
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
import re
import math
import string

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _order='emp_id asc'
    
    record_id = fields.Integer('ID')
    name = fields.Char(related='resource_id.name', store=True, oldname='name_related', size=30)
    emp_no_ref = fields.Char('Created/Modified Employee No', size=9)
    work_email = fields.Char('Work Email',size=60)
    passport_id = fields.Char('Passport No', size=20)
    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', 'Branch',domain=[('type','=','branch')])
    entity_id = fields.Many2one('operating.unit','Entity',domain=[('type','=','entity')])
    #legal_entity_id = fields.Many2one('pappaya.legal.entity','Legal Entity',related='branch_id.legal_entity_id')
    state_id = fields.Many2one('res.country.state','State',related='branch_id.state_id')
    unit_type_id = fields.Many2one('pappaya.office.type',string="Office Type")
    # date = fields.Date()
    category_id = fields.Many2one('pappaya.employee.category','Category')
    sub_category_id = fields.Many2one('hr.employee.subcategory','Sub Category')
    subject_id = fields.Many2one('pappaya.subject', string='Subject')
    sur_name = fields.Char('Sur Name', size=15)
    middle_name = fields.Char('Middle Name', size=15)
    last_name = fields.Char('Last Name', size=15)
    father_name = fields.Char('Father Name', size=40)
    mother_name = fields.Char('Mother Name', size=40)
    date_of_joining = fields.Date('Date of Join',default=datetime.today())
    date_of_joining_year = fields.Integer('Date of Join Year',compute="cal_date_of_joining_year")
    religion = fields.Many2one('pappaya.religion', 'Religion')
    caste = fields.Many2one('pappaya.caste', 'Caste')
    blood_group_id = fields.Many2one('pappaya.blood.group', 'Blood Group')
    # blood_group_id = fields.Many2one('pappaya.master', string='Blood Group', domain="[('type','=','blood_group')]")
    bank_account_id = fields.Many2one('res.partner.bank', 'Bank Account Number',domain="[('partner_id', '=', address_home_id)]", groups="pappaya_base.hr_administrator,pappaya_base.hr_executives,pappaya_base.hr_operations_head,pappaya_base.hr_cpo,pappaya_base.payroll_operation,pappaya_base.payroll_head,pappaya_base.hr_branch_accountants,pappaya_base.hr_zonal_accountant,pappaya_base.hr_principal_hod,pappaya_base.hr_deans,pappaya_base.hr_branch_employees")
    birthday = fields.Date('Date of Birth', groups="pappaya_base.hr_administrator,pappaya_base.hr_executives,pappaya_base.hr_operations_head,pappaya_base.hr_cpo,pappaya_base.payroll_operation,pappaya_base.payroll_head,pappaya_base.hr_branch_accountants,pappaya_base.hr_zonal_accountant,pappaya_base.hr_principal_hod,pappaya_base.hr_deans,pappaya_base.hr_branch_employees")
    address_home_id = fields.Many2one('res.partner', 'Private Address', groups="pappaya_base.hr_administrator,pappaya_base.hr_executives,pappaya_base.hr_operations_head,pappaya_base.hr_cpo,pappaya_base.payroll_operation,pappaya_base.payroll_head,pappaya_base.hr_branch_accountants,pappaya_base.hr_zonal_accountant,pappaya_base.hr_principal_hod,pappaya_base.hr_deans,pappaya_base.hr_branch_employees")
    marital = fields.Selection([('single', 'Single'),('married', 'Married'),('cohabitant', 'Legal Cohabitant'),('widower', 'Widower'),('divorced', 'Divorced')
        ], string='Marital Status', groups="pappaya_base.hr_administrator,pappaya_base.hr_executives,pappaya_base.hr_operations_head,pappaya_base.hr_cpo,pappaya_base.payroll_operation,pappaya_base.payroll_head,pappaya_base.hr_branch_accountants,pappaya_base.hr_zonal_accountant,pappaya_base.hr_principal_hod,pappaya_base.hr_deans,pappaya_base.hr_branch_employees", default='single')
    
    employee_type = fields.Many2one('hr.contract.type', string='Type of Employment')
    
    emp_work_hours = fields.Many2one('pappaya.branch.worked.hours.line', string='Work Hours')
    start_time = fields.Float('Work Hours')
    end_time = fields.Float('Work Timings')
    start_duration = fields.Selection([('am', 'AM'), ('pm', 'PM')], string='Start Duration', default='am')
    end_duration = fields.Selection([('am', 'AM'), ('pm', 'PM')], string='End Duration', default='pm')
    min_work_hours = fields.Integer('Min. Work Hours')
    max_work_hours = fields.Integer('Max. Work Hours')
    total_work_time = fields.Float('Total Work Time')
    is_any_9hours = fields.Boolean('Is Any 9 Hours', default=False)
    esi_no = fields.Char('ESI No', size=17)
    gross_salary = fields.Float('Gross Salary(Per Month)')
    struct_id = fields.Many2one('hr.payroll.structure',string='Salary Structure')
    is_budget_applied = fields.Boolean(related='job_id.is_budget_applicable',string='Is Budget Applied?')
    sub_category_code = fields.Char(related='sub_category_id.code')
    
    cluster_id = fields.Many2one('pappaya.cluster', 'Cluster')
    division_id = fields.Many2one('pappaya.division', 'Division')
    # id_proof = fields.Selection([('pancard', 'PAN Card'), ('aadhaar', 'Aadhaar Card')], 'ID Proof')
    # id_proof_no = fields.Char('ID Proof No',size=40)
    is_pf = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Is PF', default='no')
    is_pan_required = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Is PAN Required', default='yes')
    emp_replace_with = fields.Many2one('hr.employee', 'EMP. Replace With')
    emp_replaced_by = fields.Many2one('hr.employee', 'EMP. Replace By')
    education_line = fields.One2many('employee.education', 'employee_id', 'Educationa; Qualification')
    profession_line = fields.One2many('employee.profession', 'employee_id', 'Professional Experience')
    family_details_line = fields.One2many('employee.family.details', 'employee_id', 'Family Details')
    nominee_details_line = fields.One2many('employee.nominee.details', 'employee_id', 'Nominee Details')

    # Personal Information Tab Fields

    work_street = fields.Char('Street', size=100)
    work_street2 = fields.Char('Street2', size=100)
    # work_city =  fields.Char('City', size=25)
    work_district_id = fields.Many2one("state.district", string='District', ondelete='restrict')
    work_city_id = fields.Many2one("pappaya.city", string='City', ondelete='restrict')
    work_state_id = fields.Many2one('res.country.state', string="State", domain=[('country_id.is_active','=',True)])
    work_zip = fields.Char('Pincode', size=6)
    work_country_id = fields.Many2one('res.country', string="Country", domain=[('is_active','=',True)], default=lambda self: self.env.user.company_id.country_id)
    emp_id = fields.Char(string='Employee ID')
    
    tem_employee_id = fields.Char(string="Employee ID Full", related="employee_id", store=True)
    
    employee_id = fields.Char(string="Employee ID Full",compute="get_emp_id_calculation")
    denomination_employee_id = fields.Char(compute="get_emp_id_calculation",string="Denomination")
    
    view_employee_id = fields.Char(compute="get_emp_id_calculation",string="View Employee ID")
    staff_type = fields.Selection([('pro', 'PRO USER'), ('proadmin', 'PRO ADMIN'), ('regular', 'Regular')], 'Staff Type')
    work_mobile = fields.Char('Mobile', size=10)
    work_mobile_code = fields.Char('Mobile Code', size=2)
    alternate_mobile = fields.Char('Alternate Mobile', size=10)
    alternate_mobile_code = fields.Char('Alternate Mobile Code', size=2)
    work_phone = fields.Char('Phone', size=15)
    # phone_country_code = fields.Char(string='Std Code', size=3)
    #gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    gender_id = fields.Many2one('pappaya.gender', 'Gender')
    aadhaar_no = fields.Char('Aadhaar No', size=12)
    driving_license = fields.Char('Driving License', size=20)
    staff_id = fields.Char('Staff ID', size=8)
    age = fields.Char('Age')
    payroll_branch_id = fields.Many2one('pappaya.payroll.branch', string='Payroll Branch')
    admission_branch_ids_m2m = fields.Many2many('res.company', string='Admission Branches')
    unique_id = fields.Char('Biometric ID', size=8)
    country_id = fields.Many2one('res.country', 'Nationality (Country)', default=lambda self: self.env['res.country'].search([('is_active','=','True')]))
    
    # Additional Fields - From Narayana Screenshot

    branch = fields.Char("Branch Name")
    exam_branch = fields.Char("Exam Branch")
    segment_id = fields.Many2one('pappaya.segment', string="Segment")
    stream_id = fields.Many2one('pappaya.stream', string="Stream")
    teach_type = fields.Many2one('pappaya.teaching.type', string="Teaching Type")
    spouse_name = fields.Char("Spouse Name")
    bank_id = fields.Many2one('res.bank', string="Bank")
    bank_branch = fields.Char("Acc Branch")
    account_number = fields.Char('Account Number', size=30)
    ifsc = fields.Char("RTGS (IFSC)",size=11)
    pan_no = fields.Char("PAN No.", size=10)
    pf_no = fields.Char("PF UAN No.", size=12)
    is_fresh_emp = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='yes', string='Is Fresh Employee')
    

    aadhaar_file = fields.Binary('Aadhaar Upload')
    aadhaar_filename = fields.Char(string='Aadhaar Filename')

    pan_file = fields.Binary(string='PAN Upload')
    pan_filename = fields.Char(string='PAN Filename')
    is_required_user = fields.Boolean('Is Required User')
    
    # HR Fields
    status_id = fields.Many2one('employee.dynamic.stage.line',string="State",track_visibility='onchange')
    button_visible = fields.Boolean(compute="visible_button",string='Visible')
    cancel_button_visible = fields.Boolean(compute="cancel_visible_button_action",string='Visible')
    asset_allocation_line = fields.One2many('employee.asset.allocation', 'employee_id', string='Asset Allocation')
    date_of_left = fields.Date('Date of Left')
    old_employee_id = fields.Char(string="Old Employee ID")
    gross_history_line = fields.One2many('hr.employee.gross.line','employee_id', string='Gross Change Log')
    probation_state = fields.Selection([('pro_pending','Probation Pending'),('pro_approve','Probation Confirmed')],default='pro_pending')

    # dept_superwiser_name = fields.Char('Department Supervisor Name')
    zone_id = fields.Many2one('pappaya.zone', string='Zone',compute="get_branch_superwise_data")
    agm_id = fields.Many2one('hr.employee', string="AGM",compute="get_branch_superwise_data")
    dgm_id = fields.Many2one('hr.employee', string="DGM",compute="get_branch_superwise_data")
    gm_id = fields.Many2one('hr.employee', string="GM",compute="get_branch_superwise_data")
    ao_id = fields.Many2one('hr.employee', string="AO",compute="get_branch_superwise_data")
    dean_id = fields.Many2one('hr.employee', string="Dean",compute="get_branch_superwise_data")
    principal_id = fields.Many2one('hr.employee', string="Principal",compute="get_branch_superwise_data")
    incharge_id = fields.Many2one('hr.employee', string="Branch Incharge",compute="get_branch_superwise_data")

    # Inherit fields
    
    #company_id = fields.Many2one('res.company',related='branch_id', string='Company')
    
    
#     # Remove fields during New DB
# 
#     pan_attachment_ids = fields.Many2many('ir.attachment', string="Attachment")
#     aadhaar_attachment_id = fields.Many2one('ir.attachment', string="Attachment")
#     aadhaar_file_name = fields.Char('File Name')
#     pan_file_name = fields.Char(string='File Name')

    # Branch related
    designation = fields.Selection([('agm','AGM'),('dgm','DGM'),('gm','GM'),('ao','AO'),('dean','Dean'),('principal','Principal'),
                                    ('incharge','Incharge')], string='Designation')

    age = fields.Integer(string='Age (in Years)', compute='_get_age_value', store=True)
    no_of_yrs = fields.Integer('Years of Service',compute="set_no_of_years")
    
    data = ['entities','segment','state','branch','category','stream','employee']
    employee_count = fields.Integer(compute='_compute_employee_count')
    recruitment_count = fields.Integer(compute='_compute_recruitment_count')
    payslip_amount = fields.Integer(compute='_compute_payslip_amount')

    @api.multi
    def to_probation_confirm(self):
        for record in self:
            record.probation_state = 'pro_approve'
    
    @api.multi
    def _compute_recruitment_count(self):
        sql = """select sum(no_of_recruitment) from hr_job where no_of_recruitment > 0"""
        cr = self._cr
        cr.execute(sql)
        job = cr.fetchall()
        for employee in self:
            employee.recruitment_count = job[0][0]

    @api.multi
    def _compute_employee_count(self):
        all_employees = self.search([('id','!=',1)])
        for employee in self:
            employee.employee_count = len(all_employees)

    @api.constrains('pan_no')
    def check_pan_no(self):
        for record in self:
            if record.pan_no:
                match_pan_no = re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}', record.pan_no)
                if not match_pan_no or len(record.pan_no) < 10:
                    raise ValidationError(_("Please enter a valid PAN number"))

    @api.constrains('pan_no', 'aadhaar_no')
    def check_pan_aadhaar_duplicate(self):
        for record in self:
            if record.pan_no:
                employee = record.env['hr.employee'].search([('pan_no','=',record.pan_no)])
                if len(employee) > 1:
                    raise ValidationError(_("PAN number already exists"))
            if record.aadhaar_no:
                employee = record.env['hr.employee'].search([('aadhaar_no','=',record.aadhaar_no)])
                if len(employee) > 1:
                    raise ValidationError(_("Aadhaar number already exists"))

    @api.onchange('work_country_id')
    def onchange_work_country_id(self):
        for record in self:
            if record.work_country_id:
                record.work_state_id = record.work_district_id = record.work_city_id = None

    @api.onchange('work_state_id')
    def onchange_work_state_id(self):
        for record in self:
            if record.work_state_id:
                record.work_district_id = record.work_city_id = None

    @api.onchange('work_district_id')
    def onchange_work_district_id(self):
        for record in self:
            if record.work_district_id:
                record.work_city_id = None


    @api.onchange('segment_id')
    def _onchange_subject_id(self):
        for record in self:
            if record.branch_id and record.segment_id:
                subjects = []
                for lines in record.branch_id.segment_cource_mapping_ids:
                    if lines.segment_id == record.segment_id:
                        subject_val = self.env['pappaya.subject'].search([('course_id', '=', lines.course_package_id.course_id.id)])
                        for subject in subject_val:
                            subjects.append(subject.id)
                return {'domain': {'subject_id': [('id', 'in', tuple(subjects))]}}

    @api.depends('employee_id','emp_id')
    def get_emp_id_calculation(self):
        for record in self:
            name = ''
            denomination_employee_id = ''
            view_employee_id = ''
            meta_data_master = self.env['meta.data.master'].search([],order="sequence")
            for meta_data in meta_data_master:
                if meta_data.name == 'entity':
                    if record.branch_id.parent_id.entity_sequence_id:
                        name += record.branch_id.parent_id.entity_sequence_id
                        denomination_employee_id += 'Entity - ' + record.branch_id.parent_id.entity_sequence_id + ' / '
                        view_employee_id += record.branch_id.parent_id.entity_sequence_id + '-'
                elif meta_data.name == 'organization':
                    if record.branch_id.parent_id.company_id.organization_sequence_id:
                        name += record.branch_id.parent_id.company_id.organization_sequence_id
                        denomination_employee_id += 'Organization - ' + record.branch_id.parent_id.company_id.organization_sequence_id + ' / ' 
                        view_employee_id += record.branch_id.parent_id.company_id.organization_sequence_id + '-'
                elif meta_data.name == 'segment':
                    if record.segment_id.segment_squence:
                        name += record.segment_id.segment_squence
                        denomination_employee_id += 'Segment - ' + record.segment_id.segment_squence + ' / '
                        view_employee_id += record.segment_id.segment_squence + '-'
                elif meta_data.name == 'state':
                    if record.branch_id.state_id.sequence_id:
                        name += record.branch_id.state_id.sequence_id
                        denomination_employee_id += 'State - ' + record.branch_id.state_id.sequence_id + ' / '
                        view_employee_id += record.branch_id.state_id.sequence_id + '-'
                elif meta_data.name == 'branch':
                    if record.branch_id.branch_sequence_id:
                        name += record.branch_id.branch_sequence_id
                        denomination_employee_id += 'Branch - ' + record.branch_id.branch_sequence_id + ' / '
                        view_employee_id += record.branch_id.branch_sequence_id + '-'
                elif meta_data.name == 'category':
                    if record.employee_type.sequence_id:
                        name += record.employee_type.sequence_id
                        denomination_employee_id += 'Category - ' + record.employee_type.sequence_id + ' / '
                        view_employee_id += record.employee_type.sequence_id + '-'
                elif meta_data.name == 'stream':
                    if record.stream_id.sequence_id:
                        name += record.stream_id.sequence_id
                        denomination_employee_id += 'Stream - ' + record.stream_id.sequence_id + ' / '
                        view_employee_id += record.stream_id.sequence_id + '-'
                elif meta_data.name == 'employee':
                    if record.emp_id:
                        name += record.emp_id
                        denomination_employee_id += 'Employee - ' + record.emp_id
                        view_employee_id += record.emp_id
            record.employee_id = name
            record.denomination_employee_id = denomination_employee_id
            record.view_employee_id = view_employee_id

    
    # @api.onchange('emp_replace_with')
    # def onchange_emp_replace_with(self):
    #     for record in self:
    #         if record.emp_replace_with:
    #             record.unique_id = record.emp_replace_with.unique_id
    #             record.gross_salary = record.emp_replace_with.gross_salary
    #         return {'domain': {'emp_replace_with': [('active', '=', False),('emp_replaced_by', '=', False)]}}

    @api.multi
    def _compute_payslip_amount(self):
        sql = """select sum(total) from hr_payslip_line where slip_id in (select id from hr_payslip where state ='done' and code ='NET' and total > 0)"""
        cr = self._cr
        cr.execute(sql)
        amount = cr.fetchall()
        for employee in self:
            employee.payslip_amount = amount[0][0]
            

    @api.multi
    def _compute_payslip_total(self):
        all_payslips = self.env['hr.payslip.line'].search([('code','=','NET'),('total','>=',0)])
        amount = 0.0
        for pay in all_payslips:
            amount += pay.total
        for employee in self:
            employee.payslip_total = amount

    @api.constrains('gross_salary')
    def check_gross_salary(self):
        if self.emp_replace_with and self.gross_salary > self.emp_replace_with.gross_salary:
            raise ValidationError(_("Maximum Gross Salary per month is %s") % self.emp_replace_with.gross_salary)

        if self.gross_salary <= 0.0:
            raise ValidationError(_("Gross Salary should be greater than Zero"))

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        for record in self:
            if record.branch_id:
                record.category_id = record.sub_category_id = record.department_id = record.job_id = None
                record.unit_type_id = record.branch_id.office_type_id.id
                record.entity_id = record.branch_id.parent_id.id
                record.start_time = record.branch_id.start_time
                record.start_duration = record.branch_id.start_duration
                record.end_time = record.branch_id.end_time
                record.end_duration = record.branch_id.end_duration
                for workhour in record.branch_id.branch_workhours_line:
                    if workhour.status_type == 'present':
                        record.min_work_hours = workhour.min_work_hours
                        record.max_work_hours = workhour.max_work_hours
            category = []
            record.category_id = None
            if record.unit_type_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.unit_type_id.id)])
                for job in job_positions:
                    category.append(job.category_id.id)
            record.segment_id = None
            segment_ids = []
            for lines in record.branch_id.segment_cource_mapping_ids:
                if lines.active:
                    segment_ids.append(lines.segment_id.id)
            return {'domain': {'category_id': [('id', 'in', category)],'segment_id': [('id', 'in', segment_ids)]}}    


    @api.multi
    def get_branch_superwise_data(self):
        for record in self:
            if record.branch_id:
                branch = self.env['operating.unit'].search([('id', '=', record.branch_id.id)])
                record.zone_id= branch.zone_id.id
                record.agm_id=branch.agm_id
                record.dgm_id= branch.dgm_id
                record.gm_id=branch.gm_id
                record.ao_id=branch.ao_id
                record.dean_id=branch.dean_id
                record.principal_id=branch.principal_id
                record.incharge_id=branch.incharge_id

    
    
    
    @api.onchange('category_id')
    def onchange_branch_category_id(self):
        for record in self:
            subcategory = []
            record.sub_category_id = None
            if record.branch_id and record.category_id and record.unit_type_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.unit_type_id.id),('category_id', '=', record.category_id.id)])
                for job in job_positions:
                    subcategory.append(job.sub_category_id.id)
            return {'domain': {'sub_category_id': [('id', 'in', subcategory)]}} 
        
        
    @api.onchange('sub_category_id')
    def onchange_branch_subcategory_id(self):
        for record in self:
            department_ids = []
            record.department_id = record.job_id = None
            if record.category_id and record.unit_type_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.unit_type_id.id),
                                                           ('category_id', '=', record.category_id.id),
                                                           ('sub_category_id', '=', record.sub_category_id.id)
                                                           ])
                for job in job_positions:
                    department_ids.append(job.department_id.id)
            return {'domain': {'department_id': [('id', 'in', department_ids)]}}
    
        
    
        
    @api.onchange('department_id')
    def _onchange_department(self):
        for record in self:
            record.job_id = None
            record.parent_id = record.department_id.manager_id
            job_id = []
            if record.branch_id and record.category_id and record.sub_category_id and record.department_id:
                
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.unit_type_id.id),
                                                           ('category_id', '=', record.category_id.id),
                                                           ('sub_category_id', '=', record.sub_category_id.id),
                                                           ('department_id', '=', record.department_id.id)
                                                           ])
                for job in job_positions:
                    job_id.append(job.id)
            return {'domain': {'job_id': [('id', 'in', job_id)]}} 
    
    @api.depends('birthday')
    def _get_age_value(self):
        for record in self:
            if record.birthday:
                dt = record.birthday
                d1 = datetime.strptime(dt, "%Y-%m-%d").date()
                d2 = date.today()
                rd = relativedelta(d2, d1)
                record.age = int(rd.years)
    
    @api.depends('date_of_joining')
    def cal_date_of_joining_year(self):
        for record in self:
            if record.date_of_joining:
                record.date_of_joining_year = datetime.strptime(record.date_of_joining, "%Y-%m-%d").date().year
        
    
    @api.depends('no_of_yrs')
    def set_no_of_years(self):
        for rec in self:
            years = 0
            months = 0.00
            contract_ids = self.env['hr.contract'].search([('employee_id','=',rec.id)])
            #contract_ids = rec.contract_ids
            for contract in contract_ids:
                if contract.date_start:
                    dt = contract.date_start
                    d1 = datetime.strptime(dt, "%Y-%m-%d").date()
                    d2 = None
                    if contract.date_end:
                        d2 = datetime.strptime(contract.date_end, "%Y-%m-%d").date()
                    else:
                        d2 = date.today()
                    rd = relativedelta(d2, d1)
                    #rec.age = str(rd.years) + ' years'
                    years +=  int(rd.years)
                    months +=  rd.months
            rec.no_of_yrs = years + int(round(months/12))
            #rec.no_of_yrs_char = str(years) + ' Years' + ' - ' + str(int(round(months))) + ' Months'
            return years 

    @api.onchange('emp_work_hours')
    def onchange_emp_work_hours(self):
        for record in self:
            if record.emp_work_hours:
                time_value = self.env['pappaya.branch.worked.hours.line'].search([('branch_id','=',record.branch_id.id),('work_type','=',record.emp_work_hours.work_type)])
                record.start_time = time_value.start_time
                record.end_time = time_value.end_time
                record.start_duration = time_value.start_duration
                record.end_duration = time_value.end_duration
                record.total_work_time = time_value.total_work_hours
                record.is_any_9hours = time_value.is_any_9hours

    @api.depends('status_id')
    def visible_button(self):
        visible = False
        group_ids = []
        for record in self:
            groups_id = self.env['res.groups'].sudo().search([('category_id','in','HR &amp; Payroll Management'),('id','in',self.env.user.groups_id.ids)])
            completed_name_sr = self.env['ir.model.data'].sudo().search([('model','=','res.groups'),('res_id','in',groups_id.ids)])
            for completed_name in completed_name_sr:
                if self.env.user.has_group(completed_name.complete_name):
                    group_ids.append(completed_name.res_id)
            if record.sudo().status_id:
                for user_group in group_ids:
                    if user_group in record.status_id.sudo().groups_id.ids and record.status_id.action_type != 'cancel':
                        visible = True
            record.button_visible = visible
            
    @api.multi
    def to_state(self):
        for record in self:
            print (record.status_id,"record.status_id")
            if record.status_id:
                sequence_no = record.status_id.sequence_no
                status_dict = {}
                for lines in record.status_id.dynamic_stage_id.line_ids:
                    if lines.sequence_no > sequence_no and lines.active_id and lines.action_type == 'approve':
                        status_dict[lines.sequence_no]= lines.id
                status_list = list(status_dict.keys())
                if status_list:
                    min_value = min(status_list)
                    record.status_id = status_dict[min_value]
            else:
                next_status = record.status_id.search([('sequence_no','=',1),('menu','=','employees'),('active_id','=',True),('action_type','=','approve')])
                if next_status:
                    record.status_id = next_status.id
    
    @api.depends('status_id')
    def cancel_visible_button_action(self):
        visible = False
        group_ids = []
        for record in self:
            groups_id = self.env['res.groups'].sudo().search([('category_id','in','HR &amp; Payroll Management'),('id','in',self.env.user.groups_id.ids)])
            completed_name_sr = self.env['ir.model.data'].sudo().search([('model','=','res.groups'),('res_id','in',groups_id.ids)])
            for completed_name in completed_name_sr:
                if self.env.user.has_group(completed_name.complete_name):
                    group_ids.append(completed_name.res_id)
            if record.sudo().status_id:
                for user_group in group_ids:
                    if user_group in record.status_id.sudo().groups_id.ids and record.status_id.action_type != 'cancel':
                        visible = True
            record.cancel_button_visible = visible
            
    @api.multi
    def cancel_to_state(self):
        for record in self:
            if record.status_id:
                sequence_no = record.status_id.sequence_no
                status_dict = {}
                for lines in record.status_id.dynamic_stage_id.line_ids:
                    if lines.sequence_no > sequence_no and lines.active_id and lines.action_type == 'cancel':
                        status_dict[lines.sequence_no]= lines.id
                status_list = list(status_dict.keys())
                if status_list:
                    min_value = min(status_list)
                    record.status_id = status_dict[min_value]
            else:
                next_status = record.status_id.search([('sequence_no','=',1),('menu','=','employees'),('active_id','=',True),('action_type','=','cancel')])
                if next_status:
                    record.status_id = next_status.id        
         
    
    @api.constrains('account_number', 'bank_id')
    def check_account_number(self):
        if self.bank_id and self.account_number:
            account = self.search([('account_number', '=', self.account_number)])
            if len(account) > 1:
                raise ValidationError("Account Number is already exists...!")
            valid_ac_number = re.match('^[\d]*$', self.account_number)
            if not valid_ac_number:
                raise ValidationError("Please enter valid Account Number.")
            if len(self.account_number) != self.bank_id.account_number_length:
                raise ValidationError(_("Account Number should be %s digits for %s Bank") % (self.bank_id.account_number_length, self.bank_id.name))
 
    @api.constrains('ifsc')
    def check_ifsc(self):
        if self.ifsc:
            match_pan_no = re.match(r'^[A-Z]{4}[0-9]{7}', self.ifsc)
            if len(self.ifsc) != 11 or not match_pan_no:
                raise ValidationError('Please enter valid IFSC..!')
                    

    @api.onchange('work_country_id')
    def on_change_work_country(self):
        if self.work_country_id:
            country_value = self.env['res.country'].search([('id','=',self.work_country_id.id)])
            self.work_mobile_code = self.alternate_mobile_code = country_value.phone_code


    @api.onchange('emp_id', 'unique_id')
    def onchange_unique_id(self):
        if self.emp_id:
            if self.sudo().search_count([('emp_id','=',self.emp_id)]) > 1:
                raise ValidationError("Employee ID is already exists...!")
            valid_number = re.match('^[\d]*$', self.emp_id)
            if not valid_number:
                raise ValidationError("Please enter valid employee ID.")
            # if len(self.emp_id) < 19:
            #     raise ValidationError("Employee ID length should be minimum 19 numbers")
        if self.unique_id:
            if self.sudo().search_count([('unique_id','=',self.unique_id)]) > 1:
                raise ValidationError("Biometric ID already exists and it should not be duplicated.")
            if not re.match('^[\d]*$', self.unique_id):
                raise ValidationError("Please enter valid Unique ID")        
        
    @api.onchange('admission_branch_ids_m2m','payroll_branch_id')
    def onchange_admission_branch_ids_m2m(self):
        if not self.payroll_branch_id:
            self.admission_branch_ids_m2m = False
        domain={}; domain['admission_branch_ids_m2m'] = [('id','in',[])]
        if self.payroll_branch_id:
            domain['admission_branch_ids_m2m'] = [('id','in',self.env['res.company'].sudo().search([('id','!=',1),('tem_state_id','=',self.payroll_branch_id.state_id.id)]).ids)]
        return {'domain':domain}

    # @api.onchange('account_number')
    # def onchange_account_number(self):
    #     if self.account_number:
    #         if self.search_count([('account_number', '=', self.account_number)]) > 1:
    #             raise ValidationError("Account Number already exists..!")
    #         valid_ac_number = re.match('^[\d]*$', self.account_number)
    #         if not valid_ac_number:
    #             raise ValidationError("Please enter valid Account Number.")
    #         if len(self.account_number) != self.bank_id.account_number_length:
    #             raise ValidationError(_("Invalid account number for %s ") % self.bank_id.name)

    @api.onchange('bank_id')
    def onchange_bank_id(self):
        if self.bank_id:
            self.ifsc = self.bank_id.ifsc_code_prefix

    @api.onchange('ifsc')
    def onchange_ifsc(self):
        if self.bank_id and self.ifsc:
            if str(self.ifsc[:len(self.bank_id.ifsc_code_prefix)]) != self.bank_id.ifsc_code_prefix:
                raise ValidationError(_("Please enter valid IFSC Prefix of %s ") % self.bank_id.name)
            # if self.ese_pass_mark < 0:
            #     self.ese_pass_mark = ''
            # return {'warning': {
            #     'title': _("Warning"),
            #     'message': _("ESE - Maximum Mark - Please enter positive mark")}}
    
    @api.constrains('record_id')
    def validate_of_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")

    @api.multi
    def action_get_related_user_tree_view(self):
        for record in self:
            res_user_action = self.env.ref('pappaya_base.pappaya_users_action')
            action = res_user_action.read()[0]
            action['domain'] = str([('employee_id','=',record.id)])
            if self.env['res.users'].sudo().search_count([('employee_id','=',record.id)]) == 1:
                return {
                    'name':_("Related User"),
                    'view_mode': 'form',
                    'view_id': self.env.ref('pappaya_base.view_pappaya_users_form').id,
                    'view_type': 'form',
                    'res_model': 'res.users',
                    'res_id': self.env['res.users'].sudo().search([('employee_id','=',record.id)], limit=1).id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'current',
                    'domain': '[]',
                    'context': self._context
                }
            return action
        
    @api.model
    def default_get(self, fields):
        res = super(HrEmployee, self).default_get(fields)
        model, res_id = self.env['ir.model.data'].get_object_reference('base', 'in')
        if res_id:
            res['work_country_id'] = res_id
        return res

    @api.multi
    def toggle_active(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """
        for record in self:
            record.active = not record.active
            if record._name =='hr.employee':
                if record.user_id:
                    record.user_id.active = record.active
                      
    @api.multi
    @api.constrains('birthday')
    def check_date(self):
        if self.birthday:
            if datetime.strptime(self.birthday, DEFAULT_SERVER_DATE_FORMAT).date() >= datetime.now().date():
                raise ValidationError('Please check the entered Date of Birth')

    @api.multi
    def action_offer_letter_send(self):
        for record in self:
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('pappaya_hr','email_template_pappaya_hr_nspira_appointment_letter')[
                    1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            ctx = dict()
            update = ctx.update({
                'default_model': 'hr.employee',
                'default_res_id': record.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True
            })
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }

    @api.multi
    def create_user(self):
        print ("USERRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR")
        for record in self:
            if not record.emp_id:
                raise ValidationError("Please configure Employee ID.")
            username=''
            if record.sur_name:
                username = (record.sur_name+' '+record.name).strip()
            else:
                username = record.name
            user_dict = {
                'name':username,
                'email': record.work_email,
                'login': record.emp_id,
                'phone' : record.work_phone,
                'mobile' : record.work_mobile,
                'employee_id': record.id,
                'street':record.work_street,
                'street2':record.work_street2,
                'city': record.work_city_id.name,
                'state_id': record.work_state_id.id,
                'zip': record.work_zip,
                'country_id': record.work_country_id.id,
                'password_crypt':'',
                'password': record.emp_id,
                'payroll_branch_id':record.payroll_branch_id.id,
                'gender_id':record.gender_id.id
                }
            if record.staff_type:
                if record.staff_type == 'pro':
                    user_dict.update({'pro_user': True})
                elif record.staff_type == 'proadmin':
                    user_dict.update({'pro_admin': True})
            if record.branch_id:
                user_dict.update({'default_operating_unit_id' : record.branch_id.id, 'operating_unit_ids': [[6, 0, [self.branch_id.id,self.entity_id.id]]]})
            if record.birthday:
                user_dict.update({'birth_date': record.birthday})
            if record.date_of_joining:
                user_dict.update({'date_of_joining': self.date_of_joining})
            if user_dict:
                user_id = self.env['res.users'].sudo().create(user_dict)
                record.address_home_id = user_id.partner_id.id
                record.user_id = user_id.id

    @api.onchange('aadhaar_no')
    def _onchange_aadhaar_no(self):
        if self.aadhaar_no:
            self.env['res.company'].validation_student_aadhaar_no(self.aadhaar_no)
     
    @api.onchange('driving_license')
    def _onchange_driving_license(self):
        if self.driving_license:
            self.env['res.company'].validate_driving_license(self.driving_license)
            
    @api.onchange('work_phone')
    def _onchange_work_phone(self):
        if self.work_phone:
            self.env['res.company'].validate_phone(self.work_phone)

    @api.onchange('unique_id')
    def _onchange_unique_id(self):
        if self.unique_id:
            self.env['res.company'].validate_unique_id(self.unique_id)

#     @api.onchange('phone_country_code')
#     def _onchange_phone_country_code(self):
#         if self.phone_country_code:
#             self.env['res.company'].validate_phone_country_code(self.phone_country_code)

    @api.onchange('work_mobile')
    def _onchange_work_mobile(self):
        if self.work_mobile:
            print ("validate")
            self.env['res.company'].validate_mobile(self.work_mobile)

    @api.onchange('alternate_mobile')
    def _onchange_alternate_mobile(self):
        if self.alternate_mobile:
            print ("validate")
            self.env['res.company'].validate_mobile(self.alternate_mobile)
     
    @api.onchange('work_email')
    def _onchange_work_email(self):
        if self.work_email:
            self.env['res.company'].validate_email(self.work_email)
     
    @api.onchange('work_zip')
    def _onchange_work_zip(self):
        if self.work_zip:
            self.env['res.company'].validate_zip(self.work_zip)
     
    def _validate_vals(self, vals):
        if 'work_phone' in vals.keys() and vals.get('work_phone'):
            self.env['res.company'].validate_phone(vals.get('work_phone'))
#         if 'phone_country_code' in vals.keys() and vals.get('phone_country_code'):
#             self.env['res.company'].validate_phone_country_code(vals.get('phone_country_code'))
        if 'work_mobile' in vals.keys() and vals.get('work_mobile'):
            self.env['res.company'].validate_mobile(vals.get('work_mobile'))
        if 'alternate_mobile' in vals.keys() and vals.get('alternate_mobile'):
            self.env['res.company'].validate_mobile(vals.get('alternate_mobile'))
        if 'work_email' in vals.keys() and vals.get('work_email'):
            if self.search([('work_email','=', vals.get('work_email'))]).id:
                raise ValidationError("The given Email Address already exists")
            self.env['res.company'].validate_email(vals.get('work_email'))
        if 'work_zip' in vals.keys() and vals.get('work_zip'):
            self.env['res.company'].validate_zip(vals.get('work_zip'))
        if 'aadhaar_no' in vals.keys() and vals.get('aadhaar_no'):
            self.env['res.company'].validation_student_aadhaar_no(vals.get('aadhaar_no'))
        if 'driving_license' in vals.keys() and vals.get('driving_license'):
            self.env['res.company'].validate_driving_license(vals.get('driving_license'))
        if 'name' in vals.keys() and vals.get('name'):
            self.env['res.company']._validate_name(vals.get('name'))
        if 'unique_id' in vals.keys() and vals.get('unique_id'):
            self.env['res.company'].validate_unique_id(vals.get('unique_id'))
        return True

#     def get_employee_id_sequence(self):
#         sequence_1 = self.env['ir.sequence'].search([('code', '=', 'emp.id.sequence1')])
#         sequence_2 = self.env['ir.sequence'].search([('code', '=', 'emp.id.sequence2')])
#         sequence_3 = self.env['ir.sequence'].search([('code', '=', 'emp.id.sequence3')])
#         sequence_4 = self.env['ir.sequence'].search([('code', '=', 'emp.id.sequence4')])
#         sequence_5 = self.env['ir.sequence'].search([('code', '=', 'emp.id.sequence5')])
#         sequence_6 = self.env['ir.sequence'].search([('code', '=', 'emp.id.sequence6')])
# 
#         if sequence_5.number_next_actual != 99 and sequence_6.number_next_actual == 1000000:
#             sequence_5.number_next_actual += 1
#             sequence_6.number_next_actual = 100000
# 
#         if sequence_4.number_next_actual != 9999 and sequence_5.number_next_actual == 99 and sequence_6.number_next_actual == 1000000:
#             sequence_4.number_next_actual += 1
#             sequence_5.number_next_actual = 1
#             sequence_6.number_next_actual = 100000
# 
#         if sequence_3.number_next_actual != 99 and sequence_4.number_next_actual == 9999 \
#                 and sequence_5.number_next_actual == 99 and sequence_6.number_next_actual == 1000000:
#             sequence_3.number_next_actual += 1
#             sequence_4.number_next_actual = 1
#             sequence_5.number_next_actual = 1
#             sequence_6.number_next_actual = 100000
# 
#         if sequence_2.number_next_actual != 99 and sequence_3.number_next_actual == 99 and sequence_4.number_next_actual == 9999 \
#                 and sequence_5.number_next_actual == 99 and sequence_6.number_next_actual == 1000000:
#             sequence_2.number_next_actual += 1
#             sequence_3.number_next_actual = 1
#             sequence_4.number_next_actual = 1
#             sequence_5.number_next_actual = 1
#             sequence_6.number_next_actual = 100000
# 
#         if sequence_1.number_next_actual != 999 and sequence_2.number_next_actual == 99 and sequence_3.number_next_actual == 99 \
#                 and sequence_4.number_next_actual == 9999 and sequence_5.number_next_actual == 99 and sequence_6.number_next_actual == 1000000:
#             sequence_1.number_next_actual += 1
#             sequence_2.number_next_actual = 1
#             sequence_3.number_next_actual = 1
#             sequence_4.number_next_actual = 1
#             sequence_5.number_next_actual = 1
#             sequence_6.number_next_actual = 100000
# 
#         number_next_actual_2 = "%02d" % (sequence_2.number_next_actual,)
#         number_next_actual_3 = "%02d" % (sequence_3.number_next_actual,)
#         number_next_actual_4 = "%04d" % (sequence_4.number_next_actual,)
#         number_next_actual_5 = "%02d" % (sequence_5.number_next_actual,)
# 
#         sequence = str(sequence_1.number_next_actual) + str(number_next_actual_2) + str(number_next_actual_3) \
#                    + str(number_next_actual_4) + str(number_next_actual_5) + str(sequence_6.number_next_actual)
# 
#         # new_sequence_1 = sequence_1.get_id(sequence_1.id, 'id')
#         # new_sequence_2 = sequence_2.get_id(sequence_2.id, 'id')
#         # new_sequence_3 = sequence_3.get_id(sequence_3.id, 'id')
#         # new_sequence_4 = sequence_4.get_id(sequence_4.id, 'id')
#         # new_sequence_5 = sequence_5.get_id(sequence_5.id, 'id')
#         new_sequence_6 = sequence_6.get_id(sequence_6.id, 'id')
# 
#         return sequence

    @api.model
    def create(self, vals):

        print ("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        if 'branch_id' not in vals:
            raise ValidationError("First choose Branch ID. ")

        #branch = self.env['operating.unit'].sudo().search([('id', '=', vals['branch_id'])])
        job_id = self.env['hr.job'].sudo().browse(vals['job_id'])
        budget = self.env['pappaya.budget.hr'].sudo().search([('branch_id', '=', vals['branch_id']), ('segment_id', '=', vals['segment_id']),\
                                                       ('state', '=', 'confirm'), ('active', '=', True)], limit=1, order='id desc')

        if job_id.is_budget_applicable:
            if not budget:
                raise ValidationError("Budget is not incorporated")
            if budget.total_vacancies == 0 or budget.balance_vacancies == 0:
                raise ValidationError("There is no Vacancy for this Designation. First update the Vacancy Details or Budget Details")
            for budget_line in budget.budget_line_ids:
                if budget_line.subject_id.id == vals['subject_id']:
                    if budget_line.avg_salary < vals['gross_salary']:
                        raise ValidationError(_("Gross salary should not be greater than Allotted Average Salary (Rs. %s)") % (math.ceil(budget_line.avg_salary)))
                    if budget_line.budget_available < vals['gross_salary']:
                        raise ValidationError(_("Gross salary exceeds the Available Budget Amount (Rs. %s)") % (math.ceil(budget_line.budget_available)))

        if 'name' in vals and vals.get('name'):
            vals['name'] = vals['name'].title()
        self._validate_vals(vals)

        sequence_config =self.env['meta.data.master'].sudo().search([('name','=','employee')])
        if not sequence_config:
            raise ValidationError(_("Please Configure Employee Sequence"))
        vals['emp_id'] = self.env['ir.sequence'].sudo().next_by_code('pappaya.hr.employee') or _('New')
        print ("sssssssssssssssssss")
        res = super(HrEmployee, self).create(vals)
        print("222222222222222222222", self, res)
        values = {}
        if 'bank_id' in vals and vals.get('bank_id'):
            values['bank_id'] = vals['bank_id']
        if 'account_number' in vals and vals.get('account_number'):
            values['acc_number'] = vals['account_number']
        if 'ifsc' in vals and vals.get('ifsc'):
            values['ifsc_no'] = vals['ifsc']
        if 'department_id' in vals and vals.get('department_id'):
            values['department_id'] = vals['department_id']
        if 'job_id' in vals and vals.get('job_id'):
            values['job_id'] = vals['job_id']
        print ("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
        values['emp_id'] = res.id
        if 'bank_id' in vals and 'account_number' in vals and 'ifsc' in vals:
            account_id = self.env['res.partner.bank'].sudo().create(values)
            if res:
                res.sudo().write({'bank_account_id':account_id.id})

        partner = {}
        if 'name' in vals and vals.get('name'):
            partner['name'] = vals['name']
        if 'work_email' in vals and vals.get('work_email'):
            partner['email'] = vals['work_email']
        if 'work_mobile' in vals and vals.get('work_mobile'):
            partner['mobile'] = vals['work_mobile']
        if 'work_street' in vals and vals.get('work_street'):
            partner['street'] = vals['work_street']
        if 'work_street2' in vals and vals.get('work_street2'):
            partner['street2'] = vals['work_street2']
        if 'work_state_id' in vals and vals.get('work_state_id'):
            partner['state_id'] = vals['work_state_id']
        if 'work_zip' in vals and vals.get('work_zip'):
            partner['zip'] = vals['work_zip']
        if 'work_country_id' in vals and vals.get('work_country_id'):
            partner['country_id'] = vals['work_country_id']

        partner_id = self.env['res.partner'].sudo().create(partner)

        # Contract Creation
        contract_vals = {}
        contract_vals.update({'wage' :0.0, 'state' : 'open'})
        contract_vals.update({'employee_id': res.id})

        if 'name' in vals and vals['name']:
            vals['name'] = vals['name'].title()
            contract_vals.update({'name': 'Contract for ' + vals['name']})
        if 'department_id' in vals and vals['department_id']:
            contract_vals.update({'department_id':vals['department_id']})
        if 'job_id' in vals and vals['job_id']:
            contract_vals.update({'job_id':vals['job_id']})
        if 'date_of_joining' in vals and vals['date_of_joining']:
            contract_vals.update({'date_start':vals['date_of_joining']})
        if 'gross_salary' in vals and vals['gross_salary']:
            contract_vals.update({'wage' : vals['gross_salary']})
        if 'struct_id' in vals and vals['struct_id']:
            contract_vals.update({'struct_id' : vals['struct_id']})
        if 'company_id' in vals and vals['company_id']:
            contract_vals.update({'company_id' : vals['company_id']})
        if 'branch_id' in vals and vals['branch_id']:
            contract_vals.update({'branch_id' : vals['branch_id']})
        if 'employee_type' in vals and vals['employee_type']:
            contract_vals.update({'type_id' : vals['employee_type']})
        if contract_vals:
            contract = self.env['hr.contract'].sudo().create(contract_vals)

        if job_id.is_budget_applicable:
            for budget_line in budget.budget_line_ids:
                if budget_line.subject_id.id == res.subject_id.id:
                    if (budget_line.new_vacancy_count - budget_line.occupied_vacancies) < 1:
                        raise ValidationError("There is no Vacancy for this Designation. First update the Vacancy Details or Budget Details")

                    budget_line.budget_taken += res.gross_salary
                    budget_line.occupied_vacancies += 1

                    employee_line = self.env['pappaya.budget.employee.line']
                    employee_line.sudo().create({
                        'budget_id': budget.id,
                        'employee_id': res.id,
                        'employee_wage': res.gross_salary,
                        'origin_of_employee': 'From Recruitment',
                    })
                    budget.occupied_vacancies += 1
        print ("ENDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")
        return res

    @api.multi
    def write(self, vals):
        self._validate_vals(vals)
        user_updation = {}
        values = {}
        if 'emp_id' in vals and vals['emp_id']:
            user_updation.update({'login':vals['emp_id'], 'password':vals['emp_id']})
        if 'work_street' in vals:
            user_updation.update({'street':vals['work_street']})
        if 'work_street2' in vals:
            user_updation.update({'street2':vals['work_street2']})
        if 'work_city' in vals:
            user_updation.update({'city':vals['work_city']})  
        if 'work_state_id' in vals:
            user_updation.update({'state_id':vals['work_state_id']})
        if 'work_country_id' in vals:
            user_updation.update({'country_id':vals['work_country_id']})               
        if 'work_zip' in vals:
            user_updation.update({'zip':vals['work_zip']})
        if 'date_of_joining' in vals:
            user_updation.update({'date_of_joining':vals['date_of_joining']})
        if 'birthday' in vals:
            user_updation.update({'birth_date':vals['birthday']})
        if 'gender_id' in vals:
            user_updation.update({'gender_id':vals['gender_id']})
        if 'work_email' in vals:
            user_updation.update({'email':vals['work_email']})
        if 'work_mobile' in vals:
            user_updation.update({'mobile':vals['work_mobile']})
        if 'alternate_mobile' in vals:
            user_updation.update({'mobile':vals['alternate_mobile']})
        if 'work_phone' in vals:
            user_updation.update({'phone':vals['work_phone']})
        if 'staff_type' in vals:
            if vals['staff_type'] == 'pro':
                user_updation.update({'pro_user':True})
            elif vals['staff_type'] == 'proadmin':
                user_updation.update({'pro_admin':True})
        if user_updation:
            self.user_id.sudo().write(user_updation)

        if 'bank_id' in vals:
            values['bank_id'] = vals['bank_id']
        if 'account_number' in vals:
            values['acc_number'] = vals['account_number']
        if 'ifsc' in vals:
            values['ifsc_no'] = vals['ifsc']
        if 'emp_replace_with' in vals:
            employee = self.env['hr.employee'].search([('id', '=', vals['emp_replace_with']),('active', '=', False)])
            employee.emp_replaced_by = self.id
        self.bank_account_id.sudo().write(values)

        contract = self.env['hr.contract'].search([('employee_id','=',self.id),('state','=','open')])
        if contract:
            cont_value = contract.name.split(' ')
            if 'name' in vals:
                contract.name = str.replace(contract.name, cont_value[2], vals['name'])
            if 'sur_name' in vals:
                contract.name = str.replace(contract.name, cont_value[3], vals['sur_name'])
            if 'department_id' in vals:
                contract.department_id = vals['department_id']
            if 'job_id' in vals:
                contract.job_id = vals['job_id']
            if 'date_of_joining' in vals:
                contract.date_start = vals['date_of_joining']
            if 'gross_salary' in vals:
                contract.wage = vals['gross_salary']
            if 'struct_id' in vals:
                contract.struct_id = vals['struct_id']

        return super(HrEmployee, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name
     
    @api.constrains('emp_id','unique_id')
    def validate_emp_id(self):
        if self.emp_id:
            if self.sudo().search_count([('emp_id','=',self.emp_id)]) > 1:
                raise ValidationError("Employee ID is already exists...!")
            valid_number = re.match('^[\w]*$', self.emp_id)
            if not valid_number:
                raise ValidationError("Please enter valid employee ID.")
            # if len(self.emp_id) < 8:
            #     raise ValidationError("Employee ID length should be minimum 8 numbers and maximum 9")
            # elif len(self.emp_id) > 9:
            #     raise ValidationError("Employee ID length should be minimum 8 numbers and maximum 9")
        if self.unique_id:
            if self.sudo().search_count([('unique_id','=',self.unique_id)]) > 1:
                raise ValidationError("Biometric ID already exists and it should not be duplicated.")
            if not re.match('^[\d]*$', self.unique_id):
                raise ValidationError("Please enter valid Unique ID")

    @api.constrains('esi_no', 'pf_no')
    def validate_esi_pf_no(self):
        if self.esi_no:
            if self.sudo().search_count([('esi_no', '=', self.esi_no)]) > 1:
                raise ValidationError("ESI No. is already exists and it should not be duplicated.")
            if not re.match('^[\w]*$', self.esi_no):
                raise ValidationError("Please enter valid ESI No.")
            if len(self.esi_no) < 17:
                raise ValidationError("ESI No. length should be 17 numbers")
        if self.pf_no:
            if self.sudo().search_count([('pf_no', '=', self.pf_no)]) > 1:
                raise ValidationError("PF UAN No. already exists and it should not be duplicated.")
            if not re.match('^[\d]*$', self.pf_no):
                raise ValidationError("Please enter valid PF UAN No.")
            if len(self.pf_no) < 12:
                raise ValidationError("PF UAN No. length should be 12 digits")
            

    # @api.multi
    # @api.constrains('date_of_joining')
    # def _date_validation_date_of_joining(self):
    #     if self.date_of_joining and self.date_of_joining > str(datetime.today().date()):
    #         raise ValidationError("Date of Joining should not be in future date.!")
        
    @api.multi 
    @api.constrains('birthday')
    def _date_validation_birthday(self):
        if self.birthday and self.birthday > str(datetime.today().date()):
            raise ValidationError("Date of Birth should not be in future date.!")

    @api.multi
    @api.constrains('birthday','date_of_joining')
    def _date_birthday_date_of_joining(self):
        if self.birthday and self.date_of_joining:
            if self.birthday >= self.date_of_joining:
                raise ValidationError("Date of Join should be greater than Date of Birth.!")
    
#     """ Purpose : Hiding 'Administrator' record in many2one fields. """
#     @api.model
#     def name_search(self, name='', args=None, operator='ilike', limit=100):
#         args += ([('id', '!=', 1)])
#         mids = self.search(args)
#         return mids.name_get()
#      
#     """ Purpose : Hiding 'Administrator' record when other user login and try to view in users menu if login user has access to view users menu. """
#     @api.model
#     def search(self, args, offset=0, limit=None, order=None, count=False):
#         args += [('id', '!=', 1)]
#         return super(HrEmployee, self).search(args, offset, limit, order, count=count)

    ''' Purpose: Restricting every users to not to delete "Administrator" record '''
    @api.multi
    def unlink(self):
        for user in self:
            if user.id == 1:
                raise ValidationError("Sorry, You are not allowed to delete it.\nThis record is considered as master configuration.")
        return super(HrEmployee, self).unlink()

class EmployeeAllocationLine(models.Model):
    _name = "employee.asset.allocation"

    employee_id = fields.Many2one('hr.employee', string="Employee")
    branch_id   = fields.Many2one('operating.unit',related='employee_id.branch_id',string='Branch_id')
    asset_id = fields.Many2one('pappaya.asset', string='Asset Name')
    model_no = fields.Char('Model No.')
    asset_quantity = fields.Integer('Quality', default=1)
    asset_value = fields.Float('Value')
    issued_by = fields.Many2one('res.users', string='Issued By')
    allocated_date = fields.Date('Allocated Date')
    returned_date = fields.Date('Returned Date')
    state = fields.Selection([('allocate', 'Allocate'), ('return', 'Return')], default='allocate', string='State')
    remarks = fields.Char('Remarks')
    

    @api.constrains('model_no')
    def check_model_no(self):
        if len(self.search([('employee_id','=', self.employee_id.id),('model_no', '=', self.model_no)])) > 1:
            raise ValidationError("Model No. already exists")
        
    @api.onchange('employee_id','branch_id','asset_id','model_no','asset_quantity','asset_value')
    def _onchange_department(self):
        for record in self:
            user_ids = []
            if record.employee_id:
                employees= self.env['hr.employee'].sudo().search([('branch_id','=',record.employee_id.branch_id.id)])
                print (employees,record.employee_id.branch_id.id,"eeeeeeeeeeeeeeeeeee")
                user_ids = self.env['res.users'].search([('employee_id','in',employees.ids)])
                print (user_ids,"dddddddddddddd")
            return {'domain': {'issued_by': [('id', 'in', user_ids.ids)]}}

class EmployeeQualification(models.Model):

    _name = 'employee.education'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    type_id = fields.Many2one('hr.recruitment.degree',"Degree", ondelete="cascade")
    institute = fields.Char('Institutes')
    year = fields.Selection([(num, str(num)) for num in reversed(range(1980, (datetime.now().year)+1 ))], string='Year of Completion')
    doc = fields.Binary('Certificates')
    doc_filename  = fields.Char('FileName')

class EmployeeProfession(models.Model):

    _name = 'employee.profession'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    job_id = fields.Char('Job Title')
    institute = fields.Char('Institutes')
    location = fields.Char('Location')
    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')
    doc = fields.Binary('Experience Certificates')
    doc_filename = fields.Char('FileName')

    @api.constrains('from_date', 'to_date')
    def check_from_to_date(self):
        date = fields.Datetime.now()
        if (self.from_date > date) or (self.to_date > date):
            raise ValidationError('Future Start Date or End Date in Professional experience is not acceptable!!')
        if (self.from_date >= self.employee_id.date_of_joining) or (self.to_date >= self.employee_id.date_of_joining):
            raise ValidationError('Start or End Date is greater than Joining Date !!')
        if self.to_date < self.from_date:
            raise ValidationError('End Date is less than Start Date !!')


class EmployeeFamilyDetails(models.Model):

    _name = 'employee.family.details'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    relationship = fields.Many2one('pappaya.employee.relationship',string='Relationship')
    relation_name = fields.Char('Name')
    relation_dob = fields.Date('DOB')
    relation_contact = fields.Char('Contact No.', size=10)

    @api.onchange('relationship')
    def _onchange_relationship(self):
        for record in self:
            if record.employee_id.marital == 'single':
                return {'domain': {'relationship': [('name', 'not in', ('Spouse', 'Children'))]}}

    @api.constrains('relation_contact')
    def check_relation_contact(self):
        for record in self:
            if record.relation_contact:
                record.env['res.company'].validate_mobile(record.relation_contact)

    @api.multi
    @api.constrains('relation_dob')
    def check_relation_dob(self):
        for record in self:
            if record.relation_dob:
                if datetime.strptime(record.relation_dob, DEFAULT_SERVER_DATE_FORMAT).date() >= datetime.now().date():
                    raise ValidationError('Please check the entered Date of Birth in Family Details Tab')


class EmployeeNomineeDetails(models.Model):

    _name = 'employee.nominee.details'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    statutory_id = fields.Many2one('statutory.requirment', 'Statutory')
    statutory_no = fields.Char('Statutory No.')
    nominee_name = fields.Char('Name')
    nominee_relation = fields.Many2one('pappaya.employee.relationship',string='Relationship')
    nominee_contact = fields.Char('Contact No.', size=10)

    @api.onchange('nominee_relation')
    def _onchange_relationship(self):
        for record in self:
            if record.employee_id.marital == 'single':
                return {'domain': {'nominee_relation': [('name', 'not in', ('Spouse', 'Children'))]}}

    @api.constrains('nominee_contact')
    def check_nominee_contact(self):
        for record in self:
            if record.nominee_contact:
                record.env['res.company'].validate_mobile(record.nominee_contact)

    @api.constrains('statutory_id')
    def check_statutory_id(self):
        for record in self:
            if record.statutory_id:
                statutory_ids = record.employee_id.nominee_details_line.ids
                if len(record.search([('statutory_id', '=', record.statutory_id.id), ('id', 'in', statutory_ids)])) > 1:
                    raise ValidationError("Statutory Requirement already exists for this Employee")




class HrContractWage(models.TransientModel):
    _name = 'hr.employee.gross'
    _description = 'Employee Gross Updation'

    gross_amount = fields.Float('New Gross')
    update_reason = fields.Char('Reason for Gross Updation',size=100)

    @api.multi
    def update_employee_gross(self):
        employee    = self.env['hr.employee'].browse(self._context.get('active_id'))
        old_gross   = employee.gross_salary 
        employee.write({
            'gross_salary' : self.gross_amount,
            'gross_history_line': [(0, 0, {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'user_id': self.env.user.id,
                'old_gross': old_gross,
                'new_gross': self.gross_amount,
                'update_reason': self.update_reason
            })]
        })
        
    @api.constrains('gross_amount')
    def check_gross_amount(self):
        for record in self:
            if record.gross_amount < 0.00:
                    raise ValidationError(_("Can't New Gross Amount because amount is negative" ))
            if record.gross_amount == 0.00:
                    raise ValidationError(_("Can't accept New Gross Amount because amount is zero" ))

class HRContractWageHistory(models.Model):
    _name = 'hr.employee.gross.line'
    _rec_name = 'new_gross'

    employee_id     = fields.Many2one('hr.employee', string='Employee')
    date            = fields.Datetime('Date')
    user_id         = fields.Many2one('res.users', string='User')
    update_reason   = fields.Char('Reason for Gross Updation',size=100)
    new_gross       = fields.Float('New Gross')
    old_gross       = fields.Float('Old Gross')
    arrears_amt     = fields.Float(string='Arrears Amount')
    state           = fields.Selection([('non_pending','Non-Pending'),('pending','Pending'),('paid','Paid')],string='Arrears Status',default='non_pending')
    from_month_id   = fields.Many2one('calendar.generation.line',string='From Month')
    to_month_id     = fields.Many2one('calendar.generation.line',string='To Month')
    date_start      = fields.Date('Start Date')
    date_end      = fields.Date('End Date')

