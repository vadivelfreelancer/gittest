from odoo import fields,models,api


class ProgramInchargeView(models.TransientModel):
    _name = 'program.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    division = fields.Many2one("division.division", string="Division")
    branch = fields.Many2one("branch.branch", string="Branch")
    search_select = fields.Selection(string="Search On", selection=[('employee_number', 'Employee No.')])
    employee_search = fields.Char(string="Name/Employee No.")
    employees = fields.Many2one('employee.employee', string="Employees")
    program_name = fields.Char(string="Name")
    program_description = fields.Text(string="Description")

    program_incharge_lines = fields.Many2many('program.incharge.line')

    @api.model
    def default_get(self, fields):
        res = super(ProgramInchargeView, self).default_get(fields)
        program = self.env['program.incharge.line'].search([])
        res['program_incharge_lines'] = program.ids
        return res


