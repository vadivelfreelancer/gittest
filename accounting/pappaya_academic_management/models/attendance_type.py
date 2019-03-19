from odoo import fields, models, api


class AttendanceType(models.Model):
    _name = 'attendance.type'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    attendance_type_line = fields.One2many('attendance.type.line', 'attendance_id')


class AttendanceTypeLine(models.Model):
    _name = 'attendance.type.line'
    _rec_name = 'attendance_type'
    attendance_type = fields.Char(string="Attendance Type")
    description = fields.Text(string="Description")
    period_from = fields.Char(string="Period From")
    period_to = fields.Char(string="Period To")

    attendance_id = fields.Many2one('attendance.type')


    @api.multi
    def action_create_attendance_type(self):
        return {
            'name': 'Attendance Entry',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'attendance.type.view',
            'target': 'inline',
        }