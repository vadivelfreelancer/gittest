from odoo import fields, models, api


class AttendanceRemark(models.TransientModel):
    _name = 'attendance.remark.view'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    attendance_remark_line = fields.Many2many('attendance.remark.line')


    @api.model
    def default_get(self, fields):
        res = super(AttendanceRemark, self).default_get(fields)
        attendance_remark = self.env['attendance.remark.line'].search([])
        res['attendance_remark'] = attendance_remark.ids
        return res

