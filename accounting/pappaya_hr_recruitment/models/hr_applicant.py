# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo import http
from odoo.http import request
from datetime import datetime,date
from odoo import SUPERUSER_ID
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import math
import re

class HrApplicantInherit(models.Model):
    _inherit = "hr.applicant"
    _rec_name = "partner_name"
    
    def _default_stage_id(self):
        if self._context.get('default_job_id'):
            ids = self.env['hr.recruitment.stage'].search([
                '|',
                ('job_id', '=', False),
                ('job_id', '=', self._context['default_job_id']),
                ('fold', '=', False)
            ], order='sequence asc', limit=1).ids
            if ids:
                return ids[0]
        return False
    
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve job_id from the context and write the domain: ids + contextual columns (job or default)
        job_id = self._context.get('default_job_id')
        search_domain = []
        if job_id:
            search_domain = [('job_id', '=', job_id)] 
        else:
            search_domain = [('job_id', '=', False)]

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    name = fields.Char("Subject / Application Name", required=True,size=30)
    email_from = fields.Char("Email",help="These people will receive email." , size=60)
    salary_proposed = fields.Float("Proposed Salary", group_operator="avg", help="Salary Proposed by the Organisation", default=1)
    stage_id = fields.Many2one('hr.recruitment.stage', 'Stage', track_visibility='onchange',copy=False, index=True,)
    short_list = fields.Boolean('Short List')
    screening_list = fields.Boolean('Screening List')
    final_state = fields.Boolean(compute="final_state_calcu",string='Final State')
    aadhaar_no = fields.Char('Aadhaar No', size=12)
    aadhaar_file = fields.Binary('Aadhaar Upload')
    reject_date = fields.Date(string='Reject Date')
    doc_verified = fields.Selection([('no','No'),('yes','Yes')],string='Document Verified',default='no')
    access_url = fields.Char('Document Attachment URL')
    job_id = fields.Many2one('hr.job', "Designation")
    partner_street = fields.Char('Address 1',size=120)
    partner_street2 = fields.Char('Address 2',size=120)
    partner_zip = fields.Char('Zip',change_default=True,size=6)
    partner_city_id = fields.Many2one("pappaya.city", string='City', ondelete='restrict')
    partner_district_id = fields.Many2one("state.district", string='District', ondelete='restrict')
    partner_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    partner_country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=lambda self: self.env.user.company_id.country_id, domain=[('is_active','=',True)])
    availability = fields.Date("Date of Joining",help="The date at which the applicant will be available to start working")
    # email_from, partner_phone,partner_mobile
    
    # inherit ids
    company_id = fields.Many2one('res.company', "Organization",default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', 'Branch',domain=[('type','=','branch')], copy=False)
    category_id = fields.Many2one('pappaya.employee.category','Category')
    sub_category_id = fields.Many2one('hr.employee.subcategory','Sub Category')
    entity_id = fields.Many2one('operating.unit', string='Entity',domain=[('type','=','entity')])
    office_type_id = fields.Many2one('pappaya.office.type', string='Office Type')
    subject_id = fields.Many2one('pappaya.subject', string='Subject')
    partner_mobile = fields.Char("Mobile", size=10)
    partner_phone = fields.Char("Phone", size=12)
    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    gender_id = fields.Many2one('pappaya.gender', 'Gender')
    is_budget_applied = fields.Boolean(related='job_id.is_budget_applicable', string='Is Budget Applied?')
    sub_category_code = fields.Char(related='job_id.sub_category_id.code')
    
    partner_name = fields.Char("Applicant's Name",size=50)
    segment_id = fields.Many2one('pappaya.segment', 'Segment')
    finalized_salaries = fields.Integer(string='Finalized Salary', default=1)
    struct_id = fields.Many2one('hr.payroll.structure',string='Salary Structure')
    unique_id = fields.Char('Biometric ID', size=8)
    employee_type = fields.Many2one('hr.contract.type', string='Type of Employment')
    emp_work_hours = fields.Many2one('pappaya.branch.worked.hours.line', string='Work Hours')

    stream_id = fields.Many2one('pappaya.stream', string="Stream")
    pan_no = fields.Char("PAN No.", size=10)
    designation = fields.Selection([('agm', 'AGM'), ('dgm', 'DGM'), ('gm', 'GM'), ('ao', 'AO'),
                                    ('dean', 'Dean'), ('principal', 'Principal'),('incharge', 'Incharge')], string='Designation')
    interviewer_id = fields.Many2one('hr.job', string='Interviewer',track_visibility="onchange")
    country_id = fields.Many2one('res.country', 'Nationality (Country)', default=lambda self: self.env['res.country'].search([('is_active', '=', 'True')]))
    is_confirmed = fields.Boolean('Is Confirmed')
    is_job_confirm_sent = fields.Boolean('Is job Confirmation Sent?')
    is_job_offer_sent = fields.Boolean('Is job Offer Sent?')
    is_employee_created = fields.Boolean('Is Employee Created?')
    
    create_stage_ids = fields.Many2many('hr.recruitment.stage',string="Stage created")

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
                employee = record.env['hr.employee'].search([('pan_no', '=', record.pan_no)])
                if len(employee) > 1:
                    raise ValidationError(_("PAN number already exists"))
            if record.aadhaar_no:
                employee = record.env['hr.employee'].search([('aadhaar_no', '=', record.aadhaar_no)])
                if len(employee) > 1:
                    raise ValidationError(_("Aadhaar number already exists"))

    @api.onchange('partner_country_id')
    def onchange_partner_country_id(self):
        for record in self:
            if record.partner_country_id:
                record.partner_state_id = record.partner_district_id = record.partner_city_id = None

    @api.onchange('partner_state_id')
    def onchange_partner_state_id(self):
        for record in self:
            if record.partner_state_id:
                record.partner_district_id = record.partner_city_id = None

    @api.onchange('partner_district_id')
    def onchange_partner_district_id(self):
        for record in self:
            if record.partner_district_id:
                record.partner_city_id = None

    @api.model
    def create(self, vals):
        self._validate_vals(vals)
        res = super(HrApplicantInherit, self).create(vals)
        new_partner_id = self.env['res.partner'].sudo().create({
            'is_company': False,
            'name': res.partner_name,
            'email': res.email_from,
            'phone': res.partner_phone,
            'mobile': res.partner_mobile,
            'street': res.partner_street,
            'street2': res.partner_street2,
            'city': res.partner_city_id.name,
            'state_id': res.partner_state_id.id,
            'zip': res.partner_zip,
            'country_id': res.partner_country_id.id,
            'company_id': res.company_id.id,
            'branch_id': res.branch_id.id
        })
        res.partner_id = new_partner_id
        return res
    
    @api.multi
    def write(self, vals):
        self._validate_vals(vals)
        res = super(HrApplicantInherit, self).write(vals)
        return res
    
    
    
    def _validate_vals(self, vals):
        company = self.env['res.company']
        if 'aadhaar_no' in vals.keys() and vals.get('aadhaar_no'):
            company.validation_student_aadhaar_no(vals.get('aadhaar_no'))
        if 'email_from' in vals.keys() and vals.get('email_from'):
            if self.search([('email_from','=', vals.get('email_from'))]).id:
                raise ValidationError("The given Email Address already exists.")
            company.validate_email(vals.get('email_from'))
        if 'partner_phone' in vals.keys() and vals.get('partner_phone'):
            company.validate_phone(vals.get('partner_phone'))
        if 'partner_mobile' in vals.keys() and vals.get('partner_mobile'):
            company.validate_mobile(vals.get('partner_mobile'))
        if 'partner_zip' in vals.keys() and vals.get('partner_zip'):
            company.validate_zip(vals.get('partner_zip'))
        return True

    # @api.multi
    # @api.constrains('availability')
    # def date_validation_availability(self):
    #     if self.availability and self.availability > str(datetime.today().date()):
    #         raise ValidationError("Date of Joining should not be in future date.!")

    @api.multi
    @api.constrains('date_of_birth')
    def date_validation_birthday(self):
        if self.date_of_birth and self.date_of_birth >= str(datetime.today().date()):
            raise ValidationError("Date of Birth should not be in future date.!")

    @api.multi
    @api.constrains('date_of_birth', 'availability')
    def date_birthday_availability(self):
        if self.date_of_birth and self.availability:
            if self.date_of_birth >= self.availability:
                raise ValidationError("Date of Join should be greater than Date of Birth.!")

    @api.constrains('unique_id')
    def check_unique_id(self):
        for record in self:
            if record.unique_id:
                applicant = self.search([('unique_id', '=', record.unique_id)])
                if len(applicant) > 1:
                    raise ValidationError("Biometric ID should be unique!")

    @api.constrains('salary_proposed','finalized_salaries','salary_expected')
    def check_salary_proposed(self):
        for record in self:
            if record.salary_proposed <= 0:
                raise ValidationError("Proposed Salary must be greater than Zero")
            if record.salary_expected <= 0:
                raise ValidationError("Expected Salary must be greater than Zero")
            if record.finalized_salaries <= 0:
                raise ValidationError("Finalized Salary must be greater than Zero")
                
                

    @api.onchange('branch_id')
    def onchange_branch_id_department_id(self):
        for record in self:
            record.department_id = record.job_id = record.segment_id = record.subject_id = None
            record.office_type_id = record.entity_id = None
            department = segment_ids = []
            if record.branch_id:
                record.entity_id = record.branch_id.parent_id.id
                record.office_type_id = record.branch_id.office_type_id.id
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.branch_id.office_type_id.id)])
                for job in job_positions:
                    department.append(job.department_id.id)
                for segment in record.branch_id.segment_cource_mapping_ids :
                    segment_ids.append(segment.segment_id.id)
            return {'domain': {'department_id': [('id', 'in', department)],'segment_id': [('id', 'in', segment_ids)]}}
            
    


    @api.onchange('category_id')
    def onchange_branch_category_id(self):
        for record in self:
            subcategory = []
            record.sub_category_id = None
            if record.branch_id and record.category_id and record.office_type_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.office_type_id.id),('category_id', '=', record.category_id.id)])
                for job in job_positions:
                    subcategory.append(job.sub_category_id.id)
            return {'domain': {'sub_category_id': [('id', 'in', subcategory)]}} 
        
        
    @api.onchange('sub_category_id')
    def onchange_branch_subcategory_id(self):
        for record in self:
            department_ids = []
            record.department_id = record.job_id = None
            if record.category_id and record.office_type_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.office_type_id.id),
                                                           ('category_id', '=', record.category_id.id),
                                                           ('sub_category_id', '=', record.sub_category_id.id)
                                                           ])
                for job in job_positions:
                    department_ids.append(job.department_id.id)
            return {'domain': {'department_id': [('id', 'in', department_ids)]}}
    
    
    @api.onchange('department_id')
    def onchnage_department_id(self):
        for record in self:
            job_ids = []
            record.job_id = None
            if record.department_id and record.branch_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.branch_id.office_type_id.id),
                                                           ('department_id', '=', record.department_id.id)
                                                           ])
                for job in job_positions:
                    job_ids.append(job.id)
            return {'domain': {'job_id': [('id', 'in', job_ids)]}}
    
    @api.onchange('job_id')
    def onchange_branch_job_id(self):
        for record in self:
            record.subject_id = None
            subjects = []
            if record.branch_id and record.job_id:
                record.salary_expected = record.job_id.budgeted_salary
                record.salary_proposed = record.job_id.budgeted_salary
                job_description = self.env['pappaya.job.description'].search([('branch_id','=',record.branch_id.id),('job_id','=',record.job_id.id)])
                for job in job_description:
                    for subject in job.subject_ids:
                        subjects.append(subject.id)
            return {'domain': {'subject_id': [('id', 'in', subjects)]}}
    
    
    @api.onchange('segment_id')
    def _onchange_subject_id(self):
        for record in self:
            record.subject_id = None
            subjects = []
            if record.branch_id and record.segment_id:
                for lines in record.branch_id.segment_cource_mapping_ids:
                    if lines.segment_id.id == record.segment_id.id:
                        for course in lines.course_package_id:
                            subject_val = self.env['pappaya.subject'].search([('course_id', '=', course.course_id.id)])
                            for subject in subject_val:
                                subjects.append(subject.id)
            return {'domain': {'subject_id': [('id', 'in', tuple(subjects))]}}


    

    @api.depends('stage_id')
    def final_state_calcu(self):
        for record in self:
            if record.stage_id.final_stage:
                record.final_state = True
            else:
                record.final_state = False

    @api.constrains('aadhaar_no')
    def check_aadhaar_no_applicant_repeat(self):
        for record in self:
            if record.aadhaar_no:
                applicant_sr = record.search(['|',('active','=',True),('active','=',False),('aadhaar_no','=',record.aadhaar_no)])
                if len(applicant_sr) > 1:
                    applicant_false = record.search([('aadhaar_no', '=', record.aadhaar_no),('active','=',False)],order='id desc', limit=1)
                    if applicant_false.reject_date:
                        reject_date = datetime.strptime(applicant_false.reject_date, DEFAULT_SERVER_DATE_FORMAT).date()
                        six_months_after  =  reject_date + relativedelta(months=6)
                        if datetime.now().date() < six_months_after:
                            raise ValidationError(_("Dear applicant you are allowed to apply for this job after %s ") % six_months_after)
                    

    @api.multi
    def archive_applicant(self):
        self.write({'active': False,'reject_date':datetime.today().strftime('%Y-%m-%d')})

    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """

        employee = False
        for applicant in self:

            new_exsit_job_vancancy = 0
            exsit_job_vancancy = self.env['branch.wise.job.vecancy'].search([('branch_id','=',applicant.branch_id.id),('job_id','=',applicant.job_id.id)])
            new_exsit_job_vancancy = exsit_job_vancancy.new_count
            if new_exsit_job_vancancy < 1:
                raise ValidationError("There is no Vacancy for this Designation. First update the Vacancy Details")

            address_id = applicant.partner_id.address_get(['contact'])['contact']
            contact_name = False
            if applicant.partner_id:
                contact_name = applicant.partner_id.name_get()[0][1]

            if applicant.job_id and (applicant.partner_name or contact_name):
                applicant.job_id.sudo().write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                new_exsit_job_vancancy = 0
                exsit_job_vancancy = self.env['branch.wise.job.vecancy'].search([('branch_id','=',applicant.branch_id.id),('job_id','=',applicant.job_id.id)])
                exsit_job_vancancy.write({
                                            'new_count': exsit_job_vancancy.new_count - 1,
                                            'existing_count': exsit_job_vancancy.existing_count + 1
                                            })
                
                employee = self.env['hr.employee'].sudo().create({
                    'name': applicant.partner_name or contact_name,
                    'job_id': applicant.job_id.id,
                    'subject_id': applicant.subject_id.id,
                    'address_home_id': address_id,
                    'department_id': applicant.department_id.id,
                    'work_email': applicant.email_from,
                    'work_phone': applicant.partner_phone,
                    'work_mobile': applicant.partner_mobile,
                    'aadhaar_no': applicant.aadhaar_no,
                    'branch_id': applicant.branch_id.id,
                    'company_id': applicant.company_id.id,
                    'gross_salary':applicant.finalized_salaries,
                    # 'emp_id':employee_id,
                    'date_of_joining':applicant.availability,
                    'work_street': applicant.partner_street,
                    'work_street2': applicant.partner_street2,
                    'work_city_id': applicant.partner_city_id.id,
                    'work_district_id': applicant.partner_district_id.id,
                    'work_state_id': applicant.partner_state_id.id,
                    'work_zip': applicant.partner_zip,
                    'work_country_id': applicant.partner_country_id.id,
                    'employee_type': applicant.employee_type.id,
                    'segment_id': applicant.segment_id.id,
                    'struct_id':applicant.struct_id.id,
                    'birthday':applicant.date_of_birth,
                    'unique_id':applicant.unique_id,
                    'gender_id':applicant.gender_id.id,
                    'unit_type_id':applicant.office_type_id.id,
                    'entity_id':applicant.entity_id.id,
                    'category_id':applicant.category_id.id,
                    'sub_category_id':applicant.sub_category_id.id,
                    'pan_no':applicant.pan_no,
                    'stream_id':applicant.stream_id.id,
                    'country_id':applicant.country_id.id,
                    'designation':applicant.designation,
                    'unit_type_id':applicant.branch_id.office_type_id.id,
                    'start_time': applicant.branch_id.start_time,
                    'start_duration': applicant.branch_id.start_duration,
                    'end_time': applicant.branch_id.end_time,
                    'end_duration': applicant.branch_id.end_duration,
                })
                applicant.write({'emp_id': employee.id})
                applicant.job_id.sudo().message_post(
                    body=_(
                        'New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
                employee._broadcast_welcome()
                applicant.is_employee_created = True

            else:
                raise UserError(_('You must define an Applied Job and a Contact Name for this applicant.'))

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.sudo().read([])[0]
        if employee:
            dict_act_window['res_id'] = employee.id
        dict_act_window['view_mode'] = 'form,tree'
        return dict_act_window

    @api.multi
    def document_verification(self):
        '''
        This function opens a window to compose an email, with the edi Offer letter template message loaded by default
        '''
        for record in self:

            new_exsit_job_vancancy = 0
            exsit_job_vancancy = self.env['branch.wise.job.vecancy'].search([('branch_id','=',record.branch_id.id),('job_id','=',record.job_id.id)])
            new_exsit_job_vancancy = exsit_job_vancancy.new_count
            if new_exsit_job_vancancy < 1:
                raise ValidationError("There is no Vacancy for this Designation. First update the Vacancy Details")
            
            
            applicant = self.env['pappaya.applicant.attachment'].search([('application_id','=', record.id)])
            if not applicant:
                applicant = self.env['pappaya.applicant.attachment'].create({
                                                                'name':record.name,
                                                                'branch_id':record.branch_id.id,
                                                                'department_id':record.department_id.id,
                                                                'designation_id':record.job_id.id,
                                                                'aadhaar_no':record.aadhaar_no,
                                                                'email':record.email_from,
                                                                'mobile':record.partner_mobile,
                                                                'edu_qualification_ids':[(4,record.type_id.id)],
                                                                'application_id':record.id,
                                                                })
                attachment_line = self.env['pappaya.applicant.attachment.line']
                if record.stage_id.final_stage and record.stage_id.doc_ids:
                    for doc in record.stage_id.doc_ids:
                        attachment_line.create({
                                                'attachment_id':applicant.id,
                                                'attachment_name':doc.document_id.id,
                                                'is_required':doc.required,
                                                })
                        
            
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = base_url + "/web#id=%s&view_type=form&model=pappaya.applicant.attachment" %(applicant.id)
            record.access_url = url
            
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('pappaya_hr_recruitment', 'email_template_edi_recruitment_documentation_verification')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
#                 attachment_id = self.env.ref('pappaya_hr_recruitment.nspira_appointment_letter_report').report_action(self)
#                 aa = self.attachment_return(attachment_id)
#                 print (attachment_id,"attachment_idattachment_idattachment_idattachment_id",aa) 
            except ValueError:
                compose_form_id = False
            ctx = dict()
            update=ctx.update({
                'default_model': 'hr.applicant',
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
    def action_offer_send(self):
        '''
        This function opens a window to compose an email, with the edi Offer letter template message loaded by default
        '''
        for record in self:
            
            new_exsit_job_vancancy = 0
            exsit_job_vancancy = self.env['branch.wise.job.vecancy'].search([('branch_id','=',record.branch_id.id),('job_id','=',record.job_id.id)])
            new_exsit_job_vancancy = exsit_job_vancancy.new_count
            if new_exsit_job_vancancy < 1:
                raise ValidationError("There is no Vacancy for this Designation. First update the Vacancy Details")
            
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('pappaya_hr_recruitment', 'email_template_edi_recruitment_nspira_offer_letter')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
#                 attachment_id = self.env.ref('pappaya_hr_recruitment.nspira_appointment_letter_report').report_action(self)
#                 aa = self.attachment_return(attachment_id)
#                 print (attachment_id,"attachment_idattachment_idattachment_idattachment_id",aa) 
            except ValueError:
                compose_form_id = False
            ctx = dict()
            update=ctx.update({
                'default_model': 'hr.applicant',
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
    def action_confirmation_send(self):
        '''
        This function opens a window to compose an email, with the edi Offer letter template message loaded by default
        '''
        for record in self:

            contact_name = False
            if record.partner_id:
                address_id = record.partner_id.address_get(['contact'])['contact']
                contact_name = record.partner_id.name_get()[0][1]

            if record.job_id and (record.partner_name or contact_name):
                record.job_id.sudo().write({'no_of_hired_employee': record.job_id.no_of_hired_employee + 1})
            
            
            branch = record.branch_id
            
    
            if record.job_id.is_budget_applicable:
                budget = self.env['pappaya.budget.hr'].search([('branch_id', '=', branch.id), ('segment_id', '=', record.segment_id.id),\
                                                           ('state', '=', 'confirm'), ('active', '=', True)], limit=1, order='id desc')
                if not budget:
                    raise ValidationError("Budget is not incorporated")
                if budget.total_vacancies == 0 or budget.balance_vacancies == 0:
                    raise ValidationError("There is no Vacancy for this Designation. First update the Vacancy Details or Budget Details")
                for budget_line in budget.budget_line_ids:
                    if budget_line.subject_id.id == record.subject_id.id:
                        if record.finalized_salaries <= 0:
                            raise ValidationError("Please Enter valid Finalized Salaries")
                        if budget_line.avg_salary < record.finalized_salaries:
                            raise ValidationError(_("Allotted Average Salary is %s Rs. only.") % (math.ceil(budget_line.avg_salary)))
            
            
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('pappaya_hr_recruitment', 'email_template_edi_recruitment_confirmation_letter')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            ctx = dict()
            update=ctx.update({
                'default_model': 'hr.applicant',
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
    def action_appointment_send(self):
        '''
        This function opens a window to compose an email, with the edi Offer letter template message loaded by default
        '''
        for record in self:
            
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('pappaya_hr_recruitment', 'email_template_edi_recruitment_nspira_appointment_letter')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            ctx = dict()
            update=ctx.update({
                'default_model': 'hr.applicant',
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
    def attachment_return(self, attachement): 
        return attachement

    
    
    
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve job_id from the context and write the domain: ids + contextual columns (job or default)
        job_id = self._context.get('default_job_id')
        
        if job_id:
            search_domain = [('job_id', '=', job_id)]
        else:
            search_domain = [('job_id', '=', False)]
            
#         if stages:
#             search_domain = ['|', ('id', 'in', stages.ids)] + search_domain

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
    
    @api.onchange('job_id','partner_name')
    def onchange_partner_name_job_id(self):
        for record in self:
            domain = []
            if record.job_id or record.partner_name:
                domain.append(('job_id', '=', record.job_id.id))
            else:
                domain.append(('job_id', '=', False))
            stages = record.env['hr.recruitment.stage'].search(domain,order="sequence")
            return {'domain': {'stage_id': [('id', 'in', stages.ids)]}}
    
    @api.multi
    def confirm_applicant(self):
        for record in self:
            if not record.stage_id:
                domain = []
                if record.job_id:
                    job_stages_sr = record.env['hr.recruitment.stage'].search([('job_id', '=', record.job_id.id)],order="sequence")
                    if job_stages_sr:
                        domain.append(('job_id', '=', record.job_id.id))
                    else:
                        domain.append(('job_id', '=', False))
                stages = record.env['hr.recruitment.stage'].search(domain,order="sequence")
                if stages:
                    record.stage_id = stages.ids[0]
                    
                    record.sudo().write({'create_stage_ids':[(6, 0, [record.stage_id.id])]})
                    #interviewer = record.env['hr.recruitment.stage'].search([('id', '=', stages.ids[0])])
                    record.interviewer_id = record.stage_id.interviewer_id.id
                    record.is_confirmed = True
                else:
                    raise ValidationError("Update Interview Stage Details")
            else:
                domain = []
                if record.job_id:
                    job_stages_sr = record.env['hr.recruitment.stage'].search([('job_id', '=', record.job_id.id)],order="sequence")
                    if job_stages_sr:
                        domain.append(('job_id', '=', record.job_id.id))
                    else:
                        domain.append(('job_id', '=', False))
                if record.create_stage_ids:
                    domain.append(('id','not in',record.create_stage_ids.ids))
                domain.append(('sequence','>=',record.stage_id.sequence))
                stages = record.env['hr.recruitment.stage'].search(domain,order="sequence")
                print (stages,"weeeeeeeeeeeeeeeeeeeeeeeeeeee")
                record.stage_id = stages.ids[0]
                record.sudo().write({'create_stage_ids':[(6, 0, record.create_stage_ids.ids + [record.stage_id.id])]})
                record.interviewer_id = record.stage_id.interviewer_id.id

    
class RecruitmentStage(models.Model):
    _inherit = "hr.recruitment.stage"

    name = fields.Char("Stage name", required=True, translate=True,size=15)
    sequence = fields.Integer(
        "Sequence", default=10,
        help="Gives the sequence order when displaying a list of stages.")
    final_stage = fields.Boolean('Final Stage')
    doc_upload = fields.Boolean(string='Document Upload')
    doc_ids = fields.One2many('hr.recruitment.stage.doc','recruitment_stage_id',string='Document Verification')
    is_responsible_person = fields.Boolean('Responsible Person')
    
    entity_id = fields.Many2one('operating.unit', string='Entity',domain=[('type','=','entity')])
    office_type_id = fields.Many2one('pappaya.office.type', string='Office Type')
    parent_department_id = fields.Many2one('hr.department', string='Department')
    category_id = fields.Many2one('pappaya.employee.category','Category')
    sub_category_id = fields.Many2one('hr.employee.subcategory','Sub Category')
    
    department_id = fields.Many2one('hr.department', string='Reponsible Department')
    reponsible_person_ids = fields.Many2many('hr.employee', string='Responsible Person')
    interviewer_id = fields.Many2one('hr.job', string='Interviewer')
    
    
    @api.onchange('entity_id')
    def onchnage_parent_id(self):
        for record in self:
            if record.entity_id:
                record.office_type_id = None
                record.interviewer_id = None
                record.department_id = None
                return {'domain':{'office_type_id':[('entity_id','=',record.entity_id.id)]}}
            else:
                return {'domain':{'office_type_id':[('id','=',[])]}}
    
    @api.onchange('office_type_id')
    def onchange_branch_id(self):
        for record in self:
            category = []
            record.category_id = None
            record.interviewer_id = None
            record.department_id = None
            if record.office_type_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.office_type_id.id)])
                for job in job_positions:
                    category.append(job.category_id.id)
            return {'domain': {'category_id': [('id', 'in', category)]}}
        
        
    @api.onchange('category_id')
    def onchange_branch_category_id(self):
        for record in self:
            subcategory = []
            record.sub_category_id = None
            record.interviewer_id = None
            record.department_id = None
            if record.category_id and record.office_type_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.office_type_id.id),('category_id', '=', record.category_id.id)])
                for job in job_positions:
                    subcategory.append(job.sub_category_id.id)
            return {'domain': {'sub_category_id': [('id', 'in', subcategory)]}}
        
    
    @api.onchange('sub_category_id')
    def onchange_branch_sub_category_id(self):
        for record in self:
            department_ids = []
            record.parent_department_id = None
            record.interviewer_id = None
            record.department_id = None
            if record.category_id and record.office_type_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.office_type_id.id),
                                                           ('category_id', '=', record.category_id.id),
                                                           ('sub_category_id', '=', record.sub_category_id.id)
                                                           ])
                for job in job_positions:
                    department_ids.append(job.department_id.id)
            return {'domain': {'parent_department_id': [('id', 'in', department_ids)]}}
    
    
    @api.onchange('parent_department_id')
    def onchange_branch_designation_id(self):
        for record in self:
            job_id = []
            record.job_id = None
            record.interviewer_id = None
            record.department_id = None
            record.parent_department_id
            if record.office_type_id and record.category_id and record.sub_category_id and record.parent_department_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.office_type_id.id),
                                                           ('category_id', '=', record.category_id.id),
                                                           ('sub_category_id', '=', record.sub_category_id.id),
                                                           ('department_id', '=', record.parent_department_id.id)
                                                           ])
                for job in job_positions:
                    job_id.append(job.id)
            return {'domain': {'job_id': [('id', 'in', job_id)],'department_id': [('id', 'in', [record.parent_department_id.id])]}}     

    @api.constrains('name','final_stage','doc_upload','doc_ids')
    def validate_of_name(self):
        for record in self:
            if len(record.sudo().search([('name', '=', record.name),('job_id','=',False)])) > 1:
                raise ValidationError("Stage name already exists")
            if len(record.sudo().search([('name', '=', record.name),('job_id','=',record.job_id.id)])) > 1:
                raise ValidationError("Stage name already exists")
            
    
    @api.onchange('job_id')
    def onchange_job_id_ids(self):
        for record in self:
            record.department_id = None
            record.interviewer_id = None
            record.reponsible_person_ids = None
            if record.parent_department_id:
                return {'domain': {'department_id': [('id', '=', record.parent_department_id.id)]}}
            else:
                return {'domain': {'department_id': [('id', '=', [])]}}
            
    @api.onchange('department_id')
    def onchange_interviewer_id(self):
        for record in self:
            job_id = []
            record.interviewer_id = None
            if record.office_type_id and record.category_id and record.sub_category_id and record.department_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.office_type_id.id),
                                                           ('category_id', '=', record.category_id.id),
                                                           ('sub_category_id', '=', record.sub_category_id.id),
                                                           ('department_id', '=', record.department_id.id)
                                                           ])
                for job in job_positions:
                    job_id.append(job.id)
            return {'domain': {'interviewer_id': [('id', 'in', job_id)]}}         
            
    
    

class RecruitmentDegree(models.Model):
    _inherit = "hr.recruitment.degree"

    name = fields.Char("Degree", required=True, translate=True,size=30)
    sequence = fields.Integer("Sequence", default=1, help="Gives the sequence order when displaying a list of degrees.")



class pappaya_workflow_grade_doc_config(models.Model):
    """ Workflow Recruitment document   """
    _name = "hr.recruitment.stage.doc"
    _order = "id asc"
    _description = "Recruitment document config ..."
    
    document_id = fields.Many2one('recruitment.document',string='Document Name')
    recruitment_stage_id = fields.Many2one('hr.recruitment.stage')
    description = fields.Char('Description', size=100)
    required = fields.Boolean('Required')
    
class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'
    
    @api.multi
    def send_mail_action(self):
        if 'active_model' in self._context and self._context['active_model'] == 'hr.applicant':
            if 'active_id' in self._context and int(self._context['active_id']):
                applicant_id = self.env['hr.applicant'].search([('id','=',self._context['active_id'])])
                if applicant_id.is_job_confirm_sent:
                    applicant_id.write({'is_job_offer_sent':True})
                else:
                    applicant_id.write({'is_job_confirm_sent':True})
        # TDE/ ???
        return self.send_mail()    
    
    
               
    

