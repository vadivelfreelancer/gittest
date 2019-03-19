from odoo import fields, models, api


class HallTicket(models.Model):
    _name = 'hall.ticket'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    exam_branch = fields.Many2one("exam.branch ", string="Exam Branch")
    course = fields.Many2one("exam.course.line", string="Course")
    section = fields.Many2one("section.line", string="Section")
    division = fields.Many2one("exam.division", string="Division")
    status = fields.Selection(string="Status", selection=[('active', 'Active'), ('inactive', 'Inactive'), ])
    exam_name = fields.Many2one("exam.name.line", string="Exam Name")
    is_default = fields.Boolean(string="Default Fields",default=True)

    hall_ticket_line = fields.One2many("hall.ticket.line", "hall_ticket_id")


class HallTicketLine(models.Model):
    _name = 'hall.ticket.line'

    admission_no = fields.Many2one("admission.number", string="Admission No")
    name = fields.Char(string="Name")
    application_no = fields.Char(string="Application No ")
    roll_number = fields.Char(string="Roll No")
    password = fields.Char(string="Password")
    remarks = fields.Char(string="Remark")
    exam_type = fields.Many2one("exam.type.line", string="Exam Type")
    exam_date = fields.Date(string="Exam Date")
    phone_number = fields.Char(string="Phone Number")
    email_id = fields.Char(string="E-mail ID")
    school = fields.Char(string="School/College")
    centre_code = fields.Char(string="Center Code")
    time_slot_name = fields.Many2one("time.slot.name", string="Times Slot Name")
    paper_name = fields.Many2one("paper.name", string="Paper Name")
    hall_ticket_no = fields.Char(string="Hall Ticket No")

    hall_ticket_id = fields.Many2one('hall.ticket')


class ApplicationNumber(models.Model):
    _name = 'application.number'
    _rec_name = 'name'
    name = fields.Char(string="Application No.")


class RollNumber(models.Model):
    _name = 'roll.number'
    _rec_name = 'name'
    name = fields.Char(string="Roll No.")


class TimeSlotName(models.Model):
    _name = 'time.slot.name'
    _rec_name = 'name'
    name = fields.Char(string="Time Slot Name")


class PaperName(models.Model):
    _name = 'paper.name'
    _rec_name = 'name'
    name = fields.Char(string="Paper Name")


class ExamDivision(models.Model):
    _name = 'exam.division'
    _rec_name = 'name'

    name = fields.Char(string="Division")


