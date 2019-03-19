from odoo import fields, models, api


class HolidayEntry(models.Model):
    _name = 'holiday.entry'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    holiday_entry_line = fields.One2many('holiday.entry.line', 'holiday_id')


class HolidayLineEntry(models.Model):
    _name = 'holiday.entry.line'
    _rec_name = 'holiday_name'

    holiday_name = fields.Char(string="Holiday Name")
    description = fields.Text(string="Description")

    holiday_id = fields.Many2one('holiday.entry')


    @api.multi
    def action_create_holiday_entry(self):
        return {
            'name': 'Holiday Entry',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'holiday.entry.view',
            'target': 'inline',
        }