from odoo import fields, models, api


class VcParentPhone(models.Model):
    _name = 'vc.parent.phone'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])

    exam_branch = fields.Many2one("exam.branch", string="Exam Branch")
    admission_no = fields.Many2one("admission.number", string="Admission Number")
    date = fields.Date(string="Date")
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    phone_number = fields.Many2one("phone.number", string="Phone Number")
    remarks = fields.Text(string="Remarks")


class AdmissionNumber(models.Model):
    _name = 'admission.number'
    _rec_name = 'name'

    name = fields.Char(string="Admission Number")


class PhoneNumber(models.Model):
    _name = 'phone.number'
    _rec_name = 'name'

    name = fields.Char(string="Phone Number")


