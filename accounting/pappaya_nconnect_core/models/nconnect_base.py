# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import date

GENDER = [('male','Male'), ('female','Female')]
GROUPS = [('all', "All"), ('teacher', "Teacher"), ('parent', "Parent")]
ISSUE_STATE = [('open', "Open"), ('close', "Closed")]
SCHOOL_TYPE = [('primary', "Primary"), ('secondary', "Secondary"), ('high', "High")]

PARENT_TYPE = [('father', "Father"), ('mother', "Mother")]
FATHER_DETAILS = ['father', 'father_mobile', 'father_mail']
MOTHER_DETAILS = ['mother', 'mother_mobile', 'mother_mail']


class nconnectGrade(models.Model):
    _name = 'pappaya.grade'
    _description = 'Pappaya Grade nConnect base'

    name = fields.Char('Grade', required=True,size=50)
    # subject_m2m_id = fields.Many2many('pappaya.subject', string='Subjects')


class nconnectSection(models.Model):
    _name = 'pappaya.section'
    _description = 'Pappaya Section nConnect base'

    name = fields.Char("Section", required=True,size=50)
    # class_teacher_id = fields.Many2one('pappaya.teacher', 'Class Teacher')


# class nconnectClass(models.Model):
#     _name = 'pappaya.class'
#     _description = "Pappaya Class nConnect base"

#     @api.depends('grade_id', 'section_id')
#     def compute_class_name(self):
#         for obj in self:
#             if obj.grade_id and obj.section_id:
#                 obj.name = obj.grade_id.name + " - " + obj.section_id.name

#     name = fields.Char("Class Name", compute="compute_class_name", store=True)
#     grade_id = fields.Many2one('pappaya.grade', "Grade", required=True)
#     section_id = fields.Many2one('pappaya.section', "Section", required=True)


class nconnectSubject(models.Model):
    _name = 'pappaya.subject'
    _description = "Pappaya Subject nConnect base"

    name = fields.Char("Subject", required=True,size=50)
    code = fields.Char("Code", size=6)


class nconnectPlace(models.Model):
    _name = 'pappaya.place'
    _description = "Pappaya Place nConnect base"

    name = fields.Char("Place", required=True ,size=50)


class nconnectCity(models.Model):
    _name = 'res.city'
    _description = "Pappaya City nConnect base"

    name = fields.Char("Name" ,size=30)
    state_id = fields.Many2one('res.country.state', "State", required=True)
    country_id = fields.Many2one('res.country', "Country", required=True)


class nconnectSchool(models.Model):
    _inherit = 'res.company'

    @api.onchange('city_id')
    def onchange_city(self):
        self.update({
            'state_id': self.city_id.state_id.id,
            'country_id': self.city_id.country_id.id
        })

    city_id = fields.Many2one('res.city', "City")
    principal_id = fields.Many2one('pappaya.teacher', "Principal", required=True)
    type = fields.Selection(SCHOOL_TYPE, string="Type", default='primary', required=True)
    locality = fields.Char("Locality" ,size=150)

nconnectSchool()


class nconnectTeacher(models.Model):
    _name = 'pappaya.teacher'
    _description = 'Pappaya Teacher nConnect base'

    name = fields.Char('Name', required=True ,size=20)
    last_name = fields.Char('Last Name' ,size=20)
    teacher_id = fields.Char('Teacher ID',size=15)
    dob = fields.Date('Date of Birth', required=True)
    gender = fields.Selection(GENDER, 'Gender', required=True, default='male')
    blood_group = fields.Char('Blood Group',size=4)
    image = fields.Binary("Image")
    document = fields.Binary("Upload Documents")

    address1 = fields.Text("Address 1", required=True ,size=200)
    address2 = fields.Text("Address 2" ,size=200)
    # parent_father_id = fields.Many2one('pappaya.parent', 'Father')
    # parent_mother_id = fields.Many2one('pappaya.parent', 'Mother')
    mobile = fields.Char('Mobile', size=10, required=True)
    mobile_emergency = fields.Char("Emergency Contact", size=10, required=True)
    email = fields.Char('Email')
    street = fields.Char('Street' ,size=100)
    street2 = fields.Char('Street2',size=100)
    zip = fields.Char('Zip',size=6)
    city = fields.Char('City',size=25)
    state_id = fields.Many2one("res.country.state", 'State', ondelete='restrict')
    country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')
    qualification = fields.Char('Qualification', required=True ,size=100)
    specialization = fields.Char("Specialization", required=True ,size=100)
    specification = fields.Char('Specification',size=100)
    is_principal = fields.Boolean("Is a Principal?")

    subject_assign_ids = fields.Many2many('pappaya.subject', string="Assigned Subject", required=True) 
    # taken_subject_id = fields.Many2one('pappaya.subject',string='Subject')
    # assign_class_m2m_id = fields.Many2many('pappaya.grade',string='Assign Class')
    # assign_class_section_m2m_id = fields.Many2many('pappaya.section','Assign Section')
    # class_teacher_class_id = fields.Many2one('pappaya.grade', 'Class Teacher')
    # class_teacher_section_id = fields.Many2one('pappaya.section', 'Class Teacher Section')
    school_id = fields.Many2one('res.company', 'School', required=True)
    grade_id = fields.Many2one('pappaya.grade', "Grade")
    section_id = fields.Many2one('pappaya.section', "Section")
    # class_id = fields.Many2one('pappaya.class', "Class Teacher for", required=True)
    # class_assign_ids = fields.Many2many('pappaya.class', 'rel_teacher_class', 'teacher_id', 'class_id', "Assigned Classes", required=True)

    class_assign_ids = fields.One2many('pappaya.teacher.class', 'teacher_id', string="Assigned Classes", required=True)

    _sql_constraints = [('teacher_id_unique', 'unique(teacher_id)', 'Teacher ID should be unique!')]

    @api.model
    def create(self, vals):
        vals['teacher_id'] = self.env['ir.sequence'].next_by_code('pappaya.teacher') or 'New'
        return super(nconnectTeacher, self).create(vals)


class nconnectTeacherClasses(models.Model):
    _name = 'pappaya.teacher.class'
    _description = "Pappaya Teacher Classes nConnect base"

    teacher_id = fields.Many2one('pappaya.teacher', "Teacher") # required=True
    grade_id = fields.Many2one('pappaya.grade', "Grade", required=True)
    section_id = fields.Many2one('pappaya.section', "Section", required=True)


class res_users(models.Model):
    _description = 'res.users'
    
    parent_id = fields.Many2one('pappaya.parent', "Parent")

class nconnectParent(models.Model):
    _name = 'pappaya.parent'
    _description = "Pappaya Parent nConnect base"

    name = fields.Char("Name", required=True,size=100)
    mobile = fields.Char("Mobile", size=10, required=True)
    email = fields.Char("Email")
    parent_type = fields.Selection(PARENT_TYPE, string="Parent Type", default='father', required=True)
    user_id = fields.Many2one('res.users', "Related user")
    children_ids = fields.Many2many('pappaya.student', 'rel_parent_child_id',
    'parent_id', 'child_id', string="Childrens")
    address = fields.Text("Address" ,size=200)

    _sql_constraints = [('mobile_unique', 'unique(mobile)', 'Mobile number already exists!')]

    # @api.multi
    # def write(self, vals):
    #     if self.parent_type == 'father':
    #         if vals.get('name'):
    #             for child in self.children_ids:
    #                 child.father = vals['name']
    #         if vals.get('mobile'):
    #             for child in self.children_ids:
    #                 child.father_mobile = vals['mobile']
    #         if vals.get('email'):
    #             for child in self.children_ids:
    #                 child.father_mail = vals['email']
    #         if vals.get('address'):
    #             for child in self.children_ids:
    #                 child.address1 = vals['address']

    #     if self.parent_type == 'mother':
    #         if vals.get('name'):
    #             for child in self.children_ids:
    #                 child.mother = vals['name']
    #         if vals.get('mobile'):
    #             for child in self.children_ids:
    #                 child.mother_mobile = vals['mobile']
    #         if vals.get('email'):
    #             for child in self.children_ids:
    #                 child.mother_mail = vals['email']
    #         if vals.get('address'):
    #             for child in self.children_ids:
    #                 if child.address2:
    #                     child.address2 = vals['address']
    #                 else:
    #                     child.address1 = vals['address']
    #     return super(nconnectParent, self).write(vals)


class nconnectStudent(models.Model):
    _name = 'pappaya.student'
    _description = 'Pappaya Student nConnect base'

    # @api.depends('grade_id', 'section_id')
    # def get_class_name(self):
    #     for obj in self:
    #         if obj.grade_id and obj.section_id:
    #             class_id = self.env['pappaya.class'].search([
    #                 ('grade_id', '=', obj.grade_id.id), 
    #                 ('setion_id', '=', obj.section_id.id)])
    #             if class_id:
    #                 obj.class_id = class_id.id
    #             else:
    #                 raise UserError(_("Class name doesn't exist!"))

    name = fields.Char('Name', required=True,size=30)
    last_name = fields.Char('Last Name' ,size=30)
    student_id = fields.Char('Student ID',size=100)
    image = fields.Binary("Image")
    document = fields.Binary("Documents")
    dob = fields.Date('Date of Birth', required=True)
    gender = fields.Selection(GENDER, 'Gender', required=True, default='male')
    blood_group = fields.Char('Blood Group' ,size=4)
    address1 = fields.Text("Address 1", required=True,size=150)
    address2 = fields.Text("Address 2" ,size=150)
    # parent_father_id = fields.Many2one('pappaya.parent','Father')
    # parent_mother_id = fields.Many2one('pappaya.parent','Mother')
    class_teacher_id = fields.Many2one('pappaya.teacher', "Class Teacher", required=True)
    father = fields.Char("Father Name", required=True,size=100)
    mother = fields.Char("Mother Name", required=True ,size=100)
    father_id = fields.Many2one('pappaya.parent', "Father Details")
    mother_id = fields.Many2one('pappaya.parent', "Mother Details")
    father_mobile = fields.Char("Father Mobile", size=10, required=True)
    mother_mobile = fields.Char("Mother Mobile", size=10, required=True)
    father_mail = fields.Char("Father Email")
    mother_mail = fields.Char("Mother Email")
    mobile = fields.Char('Mobile', size=10)
    email = fields.Char('Email')
    street = fields.Char('Street',size=100)
    street2 = fields.Char('Street2',size=100)
    zip = fields.Char('Zip',size=6)
    city = fields.Char('City',size=50)
    state_id = fields.Many2one("res.country.state", 'State', ondelete='restrict')
    country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')
    school_id = fields.Many2one('res.company', 'School', required=True)
    grade_id = fields.Many2one('pappaya.grade', "Grade", required=True)
    section_id = fields.Many2one('pappaya.section', "Section", required=True)
    # class_id = fields.Many2one('pappaya.class', "Class", compute="get_class_name", store=True, required=True)

    _sql_constraints = [('student_id_unique', 'unique(student_id)', 'Student ID should be unique!')]

    @api.onchange('father_mobile')
    def onchange_father_mobile(self):
        father_id = self.env['pappaya.parent'].search([('mobile', '=', self.father_mobile)])
        if father_id:
            self.update({
                'father': father_id.name,
                'father_id': father_id.id,
                'father_mobile': father_id.mobile,
                'father_mail': father_id.email
            })

    @api.onchange('mother_mobile')
    def onchange_mother_mobile(self):
        mother_id = self.env['pappaya.parent'].search([('mobile', '=', self.mother_mobile)])
        if mother_id:
            self.update({
                'mother': mother_id.name,
                'mother_id': mother_id.id,
                'mother_mobile': mother_id.mobile,
                'mother_mail': mother_id.email
            })

    @api.model
    def create(self, vals):
        vals['student_id'] = self.env['ir.sequence'].next_by_code('pappaya.student') or 'New'
        
        father_id = False; mother_id = False
        if vals['father_mobile']:
            father_id = self.env['pappaya.parent'].search([('mobile', '=', vals['father_mobile']), 
            ('parent_type', '=', 'father')])
            if father_id:
                vals['father_id'] = father_id.id
            else:
                values = {
                    'name': vals['father'],
                    'mobile': vals['father_mobile'],
                    'email': vals['father_mail'],
                    'parent_type': 'father',
                    'address': vals['address1']
                }
                father_id_new = self.env['pappaya.parent'].create(values)
                vals['father_id'] = father_id_new.id
                father_id = father_id_new

        if vals['mother_mobile']:
            mother_id = self.env['pappaya.parent'].search([('mobile', '=', vals['mother_mobile']), 
            ('parent_type', '=', 'mother')])
            if mother_id:
                vals['mother_id'] = mother_id.id
            else:
                values = {
                    'name': vals['mother'],
                    'mobile': vals['mother_mobile'],
                    'email': vals['mother_mail'],
                    'parent_type': 'mother',
                    'address': vals['address2'] if vals['address2'] else vals['address1']
                }
                mother_id_new = self.env['pappaya.parent'].create(values)
                vals['mother_id'] = mother_id_new.id
                mother_id = mother_id_new

        create_id = super(nconnectStudent, self).create(vals)
        father_id.children_ids = [(6, 0, father_id.children_ids.ids + [create_id.id])] if father_id.children_ids.ids else [(6, 0, [create_id.id])]
        mother_id.children_ids = [(6, 0, mother_id.children_ids.ids + [create_id.id])] if mother_id.children_ids.ids else [(6, 0, [create_id.id])]
        return create_id

    @api.multi
    def write(self, vals):
        if vals.get('father_id') or vals.get('mother_id'):
            raise UserError(_("You can't change Father/Mother once it's been created. Instead you can edit details."))

        # result = super(nconnectStudent, self).write(vals)

        if vals.get('father'):
            self.father_id.name = vals['father']
            for child in self.father_id.children_ids:
                if child != self:
                    child.father = vals['father']
        if vals.get('father_mobile'):
            self.father_id.mobile = vals['father_mobile']
            for child in self.father_id.children_ids:
                if child != self:
                    child.father_mobile = vals['father_mobile']
        if vals.get('father_mail'):
            self.father_id.email = vals['father_mail']
            for child in self.father_id.children_ids:
                if child != self:
                    child.father_mail = vals['father_mail']

        if vals.get('mother'):
            self.mother_id.name = vals['mother']
            for child in self.mother_id.children_ids:
                if child != self:
                    child.mother = vals['mother']
        if vals.get('mother_mobile'):
            self.mother_id.mobile = vals['mother_mobile']
            for child in self.mother_id.children_ids:
                if child != self:
                    child.mother_mobile = vals['mother_mobile']
        if vals.get('mother_mail'):
            self.mother_id.email = vals['mother_mail']
            for child in self.mother_id.children_ids:
                if child != self:
                    child.mother_mail = vals['mother_mail']

        return super(nconnectStudent, self).write(vals)


class nconnectAttendanceView(models.TransientModel):
    _name = 'pappaya.attendance.view'
    _description = "Pappaya View Attendance nConnect base"

    # class_id = fields.Many2one('pappaya.class', "Class")
    student_id = fields.Many2one('pappaya.student', "Student", required=True)
    date_from = fields.Date("From", required=True)
    date_to = fields.Date("To", required=True)


class nconnectAttendance(models.Model):
    _name = 'pappaya.attendance'
    _description = "Pappaya Attendance nConnect base"

    student_id = fields.Many2one('pappaya.student', "Student", required=True)
    student_id_id = fields.Char("Student ID", related="student_id.student_id", store=True, readonly=True)
    grade_id = fields.Many2one('pappaya.grade', "Grade", related="student_id.grade_id", store=True, required=True)
    section_id = fields.Many2one('pappaya.section', "Section", related="student_id.section_id", store=True, required=True)
    # class_id = fields.Many2one('pappaya.class', "Class")
    school_id = fields.Many2one('res.company', 'School', related="student_id.school_id", store=True, required=True)
    date = fields.Date("Date", required=True, default=lambda self: date.today())
    is_present = fields.Boolean("Is Present")

    _rec_name = 'student_id'


class nconnectEvent(models.Model):
    _name = 'pappaya.event'
    _description = "Pappaya Event nConnect base"

    name = fields.Char("Title", required=True,size=200)
    description = fields.Text("Description" ,size=200)
    image = fields.Binary("Image")
    date_from = fields.Datetime("From", required=True)
    date_to = fields.Datetime("To", required=True)
    location = fields.Char("Location", required=True,size=200)
    # location_id = fields.Many2one('pappaya.place', "Location", required=True)
    post_to = fields.Selection(GROUPS, string="Post to", required=True, default='all')
    grade_id = fields.Many2one('pappaya.grade', "Grade")
    section_id = fields.Many2one('pappaya.section', "Section")
    # class_id = fields.Many2one('pappaya.class', "Class")
    school_id = fields.Many2one('res.company', 'School', required=True)


class nconnectAnnouncement(models.Model):
    _name = 'pappaya.announcement'
    _description = "Pappaya Announcement nConnect base"

    name = fields.Char("Title", required=True ,size=250)
    description = fields.Text("Description" ,size=200)
    date = fields.Date("Date", required=True, default=lambda self: date.today())
    post_to = fields.Selection(GROUPS, string="Post to", required=True, default='all')
    grade_id = fields.Many2one('pappaya.grade', "Grade")
    section_id = fields.Many2one('pappaya.section', "Section")
    # class_id = fields.Many2one('pappaya.class', "Class")
    school_id = fields.Many2one('res.company', 'School', required=True)


class nconnectStory(models.Model):
    _name = 'pappaya.story'
    _description = "Pappaya Story nConnect base"

    name = fields.Char("Title", required=True,size=350)
    description = fields.Text("Description" ,size=200)
    date = fields.Date("Date", default=lambda self: date.today(), required=True)
    image = fields.Binary("Image")
    images = fields.Many2many('ir.attachment', string="Images")
    grade_id = fields.Many2one('pappaya.grade', "Grade")
    section_id = fields.Many2one('pappaya.section', "Section")
    # school_id = fields.Many2one('res.company', 'School')


class nconnectIssue(models.Model):
    _name = 'pappaya.issue'
    _description = "Pappaya Issue nConnect base"

    name = fields.Char("Title", required=True ,size=350)
    state = fields.Selection(ISSUE_STATE, string="Status", required=True, default='open')
    description = fields.Text("Description",size=200)
    date = fields.Date("Date", required=True)
    raised_by = fields.Many2one('pappaya.parent', "Raised By", required=True)
    assign_to = fields.Many2one('pappaya.teacher', "Assigned to", required=True)
    escalate_to = fields.Many2one('pappaya.teacher', domain="[('is_principal', '=', True)]", string="Escalate to")
    student_id = fields.Many2one('pappaya.student', "Student Name", required=True)
    grade_id = fields.Many2one('pappaya.grade', "Grade", related="student_id.grade_id", store=True, readonly=True)
    section_id = fields.Many2one('pappaya.section', "Section", related="student_id.section_id", store=True, readonly=True)
    # class_id = fields.Many2one('pappaya.class', "Class", related="student_id.class_id", store=True)
    school_id = fields.Many2one('res.company', 'School', required=True)


class nconnectAPI(models.Model):
    _name = 'pappaya.nconnect.api'
    _description = "Pappaya nConnect API base"

    otp = fields.Char("OTP")
    otp_verify = fields.Boolean("OTP Verified?")
    response = fields.Text("Response" ,size=200)

