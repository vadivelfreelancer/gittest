from odoo import fields, models, api


class Division(models.Model):
    _name = 'division.division'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    branch = fields.Many2one("branch.branch", string="Branch")
    employee_number = fields.Many2one("employee.number", string="Employee No.")
    name = fields.Char(string="Name")
    short_name = fields.Char(string="Short Name")
    mobile_number = fields.Char(string="Mobile Number")
    ic_name = fields.Char(string="IC Name")
    email = fields.Char(string="Email")
    division_type = fields.One2many('division.line','division_id')


class DivisionLine(models.Model):
    _name = 'division.line'
    _rec_name = 'name'
    exam_region_number = fields.Char(string="Exam Region No")
    name = fields.Char(string="Name")
    short_name = fields.Char(string="Short Name")
    mobile_number = fields.Char(string="Mobile Number")
    employee_number = fields.Many2one("employee.number", string="Employee No.")
    ic_name = fields.Char(string="IC Name")
    email = fields.Char(string="Email")
    division_id = fields.Many2one("division.division")


class EmployeeNumber(models.Model):
    _name = 'employee.number'
    _rec_name = 'name'

    name = fields.Char(string="Employee Number")

