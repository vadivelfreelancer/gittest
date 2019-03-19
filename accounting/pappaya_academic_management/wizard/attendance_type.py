from odoo import fields, models, api


class AttendanceType(models.TransientModel):
    _name = 'attendance.type.view'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    attendance_type_line = fields.Many2many('attendance.type.line')

    @api.model
    def default_get(self, fields):
        res = super(AttendanceType, self).default_get(fields)
        attendance_type = self.env['attendance.type.line'].search([])
        res['attendance_type'] = attendance_type.ids
        return res
