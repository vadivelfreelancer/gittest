from odoo import fields, models, api


class AttendanceRemark(models.Model):
    _name = 'attendance.remark'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    attendance_remark_line = fields.One2many('attendance.remark.line', 'attendance_remark_id')


class AttendanceRemarkLine(models.Model):
    _name = 'attendance.remark.line'
    attendance_remark = fields.Char(string="Attendance Remark")
    remark_code = fields.Char(string="Remark Code")

    attendance_remark_id = fields.Many2one('attendance.remark')


    @api.multi
    def action_create_attendance_remark(self):
        return {
            'name': 'Attendance Remark',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'attendance.remark.view',
            'target': 'inline',
        }