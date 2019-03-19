from odoo import fields, models, api


class HolidayEntry(models.TransientModel):
    _name = 'holiday.entry.view'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    holiday_entry_line = fields.Many2many('holiday.entry.line')

    @api.model
    def default_get(self, fields):
        res = super(HolidayEntry, self).default_get(fields)
        holiday_entry = self.env['holiday.entry.line'].search([])
        res['holiday_entry'] = holiday_entry.ids
        return res



