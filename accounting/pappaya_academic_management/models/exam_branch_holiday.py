from odoo import fields, models


class ExamBranchHoliday(models.Model):
    _name = 'exam.branch.holiday'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    select_all = fields.Boolean("Check All Course")
    holiday = fields.Many2one("holiday.entry.line", string="Holiday")
    holiday_name = fields.Many2many('holiday.entry.line')
    holiday_date = fields.Date(string="Holiday Date")

    # update
    new_holiday_name = fields.Many2one('holiday.entry.line', string="Holiday")
    new_holiday_date = fields.Date(string="Holiday Date")
    description = fields.Text(string="Description")

    # add
    region_zone = fields.Selection(default="region",selection=[('region', 'Region'), ('zone', 'Zone'),])
    region = fields.Many2one("region.region", string="")
    zone = fields.Many2one("zone.zone", string="")
    exam_branch = fields.Many2many('holiday.entry.line')
    selected_branch = fields.Many2many('holiday.entry.line')
    add_holiday_name = fields.Many2one('holiday.entry.line', string="Holiday")
    add_holiday_date = fields.Date(string="Holiday Date")
    add_description = fields.Text(string="Description")


class Region(models.Model):
    _name = 'region.region'
    _rec_name = 'name'

    name = fields.Char(string='Region')


class Zone(models.Model):
    _name = 'zone.zone'
    _rec_name = 'name'

    name = fields.Char(string='Zone')


