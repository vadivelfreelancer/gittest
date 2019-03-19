from odoo import fields,models,api


class DivisionView(models.TransientModel):
    _name = 'division.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    branch = fields.Many2one("branch.branch", string="Branch")
    employee_number = fields.Many2one("employee.number", string="Employee No.")
    name = fields.Char(string="Name")
    short_name = fields.Char(string="Short Name")
    mobile_number = fields.Char(string="Mobile Number")
    ic_name = fields.Char(string="IC Name")
    email = fields.Char(string="Email")
    division_lines = fields.Many2many('division.line')

    @api.model
    def default_get(self, fields):
        res = super(DivisionView, self).default_get(fields)
        division = self.env['division.line'].search([])
        res['division_lines'] = division.ids
        return res


