from odoo import fields, models, api


class ParentFeedback(models.Model):
    _name = 'parent.feedback'
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
    state = fields.Selection(selection=[('satisfied', 'Satisfied'), ('dissatisfied', 'Dissatisfied'), ])
    physics = fields.Char(string="Physics")
    maths = fields.Char(string="Maths")
    chemistry = fields.Char(string="chemistry")
    english = fields.Char(string="English")
    diary_correction = fields.Char(string="Diary correction")
    syllabus = fields.Char(string="Syllabus")
    transport = fields.Char(string="Transport")
    books = fields.Char(string="Books")
    wash_room = fields.Char(string="Washroom")
    infrastructure = fields.Char(string="Infrastructure")
    ground = fields.Char(string="Ground")



