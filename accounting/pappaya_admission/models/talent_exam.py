from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class PappayaTalentExam(models.Model):
    _name = 'pappaya.talent.exam'
    _description = 'Talent Exam'

    @api.constrains('dob')
    def _check_dob(self):
        if self.dob:
            d1 = datetime.strptime(self.dob, "%Y-%m-%d").date()
            d2 = date.today()
            rd = relativedelta(d2, d1)
            age = str(rd.years) + ' years'
            if rd.years > 60:
                raise ValidationError('Age should not exceed more than 60 Years')

    name = fields.Char('First Name', size=40)
    image = fields.Binary("Image")
    sur_name = fields.Char('Sur Name', size=40)
    talent_exam_no = fields.Char(string='Application No.', size=40)
    exam_date = fields.Date(string='Date', default=lambda self:fields.Date.today())
    school_id = fields.Many2one('operating.unit', 'Branch',)
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    school_name = fields.Char('School Name', size=40)
    course_id = fields.Many2one('pappaya.course', string='Course')
    group_id = fields.Many2one('pappaya.group', string='Group')
    batch_id = fields.Many2one('pappaya.batch', string='Batch')
    exam_center= fields.Char('Exam Center', size=40)
    exam_name= fields.Char('Exam Name', size=40)
    mark= fields.Float('Marks')
    dob = fields.Date('Date of Birth')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    blood_group_id = fields.Many2one('pappaya.master', string='Blood Group', domain="[('type','=','blood_group')]")
    caste_id = fields.Many2one('pappaya.master', string='Caste', domain="[('type','=','caste')]")
    house_no = fields.Char('House No.', size=10)
    father_name = fields.Char("Father Name", size=40)
    mother_name = fields.Char("Mother Name", size=40)
    father_mobile = fields.Char("Father Mobile", size=10)
    mother_mobile = fields.Char("Mother Mobile", size=10)
    father_email = fields.Char("Father Email",size=20)
    mother_email = fields.Char("Mother Email",size=20)
    email = fields.Char('Email',size=20)
    street = fields.Char('Street', size=30)
    street2 = fields.Char('Street2', size=30)
    zip = fields.Char('Zip' ,size=6)
    city_id = fields.Many2one('pappaya.city',string='City')
    state_id = fields.Many2one("res.country.state", 'State', domain=[('country_id.is_active', '=', True)])
    country_id = fields.Many2one("res.country", 'Country', domain=[('is_active', '=', True)],
                                 default=lambda self: self.env.user.company_id.country_id)
    payment_mode = fields.Selection([('cash', 'Cash'), ('dd', 'DD'), ('cheque', 'Cheque')], string='Payment Mode', default='cash')
    cheque_dd_no = fields.Char(string='Cheque/DD No.', size=10)
    bank_id = fields.Many2one('res.bank','Bank Name')
    course_type = fields.Selection([('ssc', 'SSC'), ('cbse', 'CBSE'), ('icse', 'ICSE'), ('mfc', 'MFC')],
                                   string='Course Type')


    @api.constrains('mark')
    def check_marks(self):
        if self.mark <=0.0 or self.mark >100.0:
            raise ValidationError('Please enter the valid Marks')

    @api.constrains('name', 'father_name,', 'father_mobile', 'academic_year_id', 'school_id')
    def check_student(self):
        if len(self.search([('name', '=', self.name),('father_name', '=', self.father_name),
                            ('father_mobile', '=', self.father_mobile),('school_id', '=', self.school_id.id),
                            ('academic_year_id', '=', self.academic_year_id.id)])) > 1:
            raise ValidationError('Student already exist..!')

    @api.onchange('payment_mode')
    def onchange_payment_mode(self):
        if self.payment_mode:
            self.cheque_dd_no = self.bank_id = None

    @api.onchange('city_id')
    def onchange_city_id(self):
        if self.city_id:
            self.state_id = self.city_id.state_id

    @api.onchange('school_id')
    def onchange_school_id(self):
        if self.school_id:
            self.academic_year_id = self.course_id = self.group_id = self.batch_id = None

    @api.onchange('course_id')
    def onchange_course_id(self):
        if self.course_id:
            self.group_id = self.batch_id = None

    @api.onchange('group_id')
    def onchange_group_id(self):
        if self.group_id:
           self.batch_id = None

    @api.onchange('dob')
    def _onchange_dob(self):
        if self.dob:
            today = date.today()
            value = datetime.strptime(self.dob, "%Y-%m-%d").date()
            if value >= today:
                raise ValidationError("'Date of Birth' should not be current or future date.")

    @api.onchange('father_mobile')
    def onchange_father_mobile(self):
        if self.father_mobile:
            self.env['res.company'].validate_mobile(self.father_mobile)

    @api.onchange('mother_mobile')
    def onchange_mother_mobile(self):
        if self.mother_mobile:
            self.env['res.company'].validate_mobile(self.mother_mobile)

    @api.onchange('father_email')
    def onchange_father_email(self):
        if self.father_email:
            self.env['res.company'].validate_email(self.father_email)

    @api.onchange('mother_email')
    def onchange_mother_email(self):
        if self.mother_email:
            self.env['res.company'].validate_email(self.mother_email)

    @api.onchange('zip')
    def onchange_zip(self):
        if self.zip:
            self.env['res.company'].validate_zip(self.zip)


    @api.model
    def create(self, vals):
        vals['talent_exam_no'] = self.env['ir.sequence'].next_by_code('pappaya.talent.exam')
        return super(PappayaTalentExam,self).create(vals)

    @api.multi
    @api.depends('name', 'sur_name', 'talent_exam_no')
    def name_get(self):
        result = []
        for rec in self:
            if rec.sur_name and rec.name and rec.talent_exam_no:
                name = str(rec.sur_name+' '+rec.name) + ' (' + str(rec.talent_exam_no) + ')'
            else:
                name = str(rec.name )+' (' + str(rec.talent_exam_no) + ')'
            result.append((rec.id, name))
        return result

    @api.onchange('academic_year_id', 'school_id')
    def onchange_academic_year(self):
        course_domain = []
        if self.academic_year_id and self.school_id:
            self.course_id = None
            self.group_id = None
            self.batch_id = None
            for academic in self.school_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        course_domain.append(course_package.course_id.id)
        return {'domain': {'course_id': [('id', 'in', course_domain)]}}

    @api.onchange('course_id')
    def onchange_course_id(self):
        domain = []
        if self.academic_year_id and self.school_id:
            self.group_id = None;
            self.batch_id = None;
            for academic in self.school_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id:
                            domain.append(course_package.group_id.id)
        return {'domain': {'group_id': [('id', 'in', domain)]}}

    @api.onchange('group_id')
    def onchange_group_id(self):
        domain = []
        if self.academic_year_id and self.school_id:
            self.batch_id = None;
            for academic in self.school_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id:
                            domain.append(course_package.batch_id.id)
        return {'domain': {'batch_id': [('id', 'in', domain)]}}
