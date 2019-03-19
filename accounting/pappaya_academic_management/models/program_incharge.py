from odoo import fields, models, api


class ProgramIncharge(models.Model):
    _name = 'program.incharge'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    division = fields.Many2one("division.division", string="Division")
    branch = fields.Many2one("branch.branch", string="Branch")
    search_select = fields.Selection(string="Search On", selection=[('employee_number', 'Employee No.')])
    employee_search = fields.Char(string="Name/Employee No.")
    employees = fields.Many2one('employee.employee',string="Employees")
    program_name = fields.Char(string="Name")
    program_description = fields.Text(string="Description")

    program_type = fields.One2many('program.incharge.line','program_id')


class ProgramLine(models.Model):
    _name = 'program.incharge.line'
    _rec_name = 'name'

    name = fields.Char(string="Prog IC Name")
    exam_region = fields.Char(string="Exam Region Sl No")
    division_name = fields.Char(string="Division Name")
    employee_number = fields.Char(string="Emp Sl No")
    status = fields.Char(string="Status")
    description = fields.Text(string="Description")
    program_id = fields.Many2one("program.incharge")


class Division(models.Model):
    _name = 'division.division'
    _rec_name = 'name'

    name = fields.Char(string="Division")


class Branch(models.Model):
    _name = 'branch.branch'
    _rec_name = 'name'

    name = fields.Char(string="Branch")


class Employee(models.Model):
    _name = 'employee.employee'
    _rec_name = 'name'

    name = fields.Char(string="Employee")