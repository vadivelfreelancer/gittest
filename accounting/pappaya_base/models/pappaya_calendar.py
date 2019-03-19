from odoo import fields, models, api, tools, _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import datetime, timedelta
import babel
from dateutil import relativedelta


class PappayaCalendar(models.Model):
    _name = 'hr.calendar'

    def get_calendar_name(self):
        for record in self:
            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(record.date_from, "%Y-%m-%d")))
            locale = self.env.context.get('lang') or 'en_US'
            record.name = ('%s - %s') % (record.sudo().branch_id.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))


    name = fields.Char('Name', compute='get_calendar_name')
    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    date_from = fields.Date(string='From date', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='To date', required=True, default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    state = fields.Selection([('draft', 'Draft'), ('request', 'Requested'), ('approve', 'Approved'), ('cancel', 'Cancelled')]
                                , string="State", default='draft', track_visibility='onchange', copy=False)
    calendar_line = fields.One2many('hr.calendar.line', 'calendar_id', string='Calendar Lines')
    #generation_id = fields.Many2one('calendar.generation')
    generation_line_id = fields.Many2one('calendar.generation.line',ondelete='cascade')
    

    @api.constrains('date_from', 'date_to')
    def check_from_to_date(self):
        if self.date_to < self.date_from:
            raise ValidationError('To Date is less than From Date !!')

    @api.onchange('branch_id','date_from','date_to')
    def onchange_branch_id(self):
        for record in self:
            if record.branch_id and record.date_from and record.date_to:
                dates = self.generate_dates(record.date_from,record.date_to)
                year = datetime.strptime(record.date_from, '%Y-%m-%d').strftime('%Y')
    
                holiday_sr = self.env['yearly.holidays'].sudo().search([('branch_id', '=', record.branch_id.id)])
                #holiday_line = holiday.holidays_list_ids
    
                weekly_days = []
                branch_workday = self.env['operating.unit'].sudo().search([('id', '=', record.branch_id.id)])
                if branch_workday.days_monday:
                    weekly_days.append(0)
                if branch_workday.days_tuesday:
                    weekly_days.append(1)
                if branch_workday.days_wednesday:
                    weekly_days.append(2)
                if branch_workday.days_thursday:
                    weekly_days.append(3)
                if branch_workday.days_friday:
                    weekly_days.append(4)
                if branch_workday.days_saturday:
                    weekly_days.append(5)
                if branch_workday.days_sunday:
                    weekly_days.append(6)
    
                calendar_lines = []
                for daily_date in dates:
                    holiday_line = self.env['holidays.list'].search([('yearly_holidays_id', 'in', holiday_sr.ids),('date','=',daily_date)])
                    if holiday_line:
                        calendar_lines.append((0, 0, {
                            'date': daily_date,
                            'work_type': 'holiday',
                            'remarks': holiday_line.reason,
                            }
                        ))
                    elif daily_date.weekday() not in weekly_days:
                        calendar_lines.append((0, 0, {
                             'date': daily_date,
                             'work_type': 'week_off',
                            }
                        ))
                    else:
                        calendar_lines.append((0, 0, {
                            'date': daily_date,
                            'work_type': 'work',
                            }
                        ))
                record.calendar_line = calendar_lines

    @api.multi
    def generate_dates(self, date_from, date_to):
        dates = []
        td = timedelta(days=1)
        current_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        while current_date <= datetime.strptime(date_to, "%Y-%m-%d").date():
            dates.append(current_date)
            current_date += td
        return dates

    @api.multi
    def action_submit(self):
        self.write({'state': 'request'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def action_approve(self):
        self.write({'state': 'approve'})

    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")


class PappayaCalendarLine(models.Model):
    _name = 'hr.calendar.line'

    calendar_id = fields.Many2one('hr.calendar', string='Calendar ID')
    date = fields.Date('Date')
    work_type = fields.Selection([('work', 'Work Day'), ('week_off', 'Weekly-Off'), ('holiday', 'Holiday')]
                                ,string="State", default='work', track_visibility='onchange', copy=False)
    remarks = fields.Char('Remarks',size=200)
