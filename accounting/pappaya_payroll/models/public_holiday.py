import logging
import math
from datetime import datetime, date
from datetime import timedelta
from werkzeug import url_encode
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo import tools
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class yearly_holidays(models.Model):
    _name = 'yearly.holidays'
    _description = 'Holidays'
    _rec_name='year'

    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    year = fields.Selection([(num, str(num)) for num in (range((datetime.now().year), (datetime.now().year) + 2))], string='Year')
    holidays_list_ids= fields.One2many('holidays.list', 'yearly_holidays_id', string='Holidays List', required=True)
    state= fields.Selection([('draft','Draft'),('done','Confirmed'),],string='State', readonly=True,default='draft')
    change_log = fields.One2many('yearly.holidays.log','yearly_holidays_id',stringt='Change Log', readonly=True,)
    
    def case_confirm(self):
        for record in self:
            calendars = self.env['hr.calendar'].sudo().search([('branch_id', '=', record.branch_id.id)])
            for calendar in calendars:
                for holiday in record.holidays_list_ids:
                    for calendar_line in calendar.calendar_line:
                        if holiday.date == calendar_line.date:
                            calendar_line.sudo().write({'remarks': holiday.reason, 'work_type': 'holiday'})

            record.write({'state':'done'})
            record.env['yearly.holidays.log'].sudo().create({'from_state': 'draft', 'activity_time': datetime.now(), \
                                             'to_state':'done' , 'user_id': record.env.uid, 'yearly_holidays_id': record.id})

        return True
    
    def case_reset(self): 
        for record in self:  
            record.write({'state': 'draft'})
            record.env['yearly.holidays.log'].sudo().create({'from_state': 'done', 'activity_time': datetime.now(), \
                                             'to_state':'draft' , 'user_id': record.env.uid, 'yearly_holidays_id': record.id})
        return True

    @api.constrains('branch_id','year','state')
    def check_branch_year_state(self):
        for record in self:
            if len(record.search([('branch_id', '=', record.branch_id.id),('year', '=', record.year),('state', '=', 'done')])) > 1:
                raise ValidationError("Holidays are already set for this Year")
    
yearly_holidays()


class yearly_holidays_log(models.Model):
    _name = 'yearly.holidays.log'
    _description = "Holidays Log"
    
    from_state= fields.Selection([('draft','Draft'),
                                    ('done','Done'),
                                    ('freeze', 'Freezed'),
                                    ],'From State', readonly=True)
    to_state= fields.Selection([('draft','Draft'),
                                  ('done','Done'),
                                  ('freeze', 'Freezed'),
                                  ],string='To State', readonly=True)
    user_id = fields.Many2one('res.users','Users', readonly=True)
    activity_time = fields.Datetime('Time', readonly=True)
    yearly_holidays_id = fields.Many2one('yearly.holidays','Yearly Holidays ID', readonly=True)
    create_date = fields.Datetime('Created On', readonly=True)
    create_uid = fields.Many2one('res.users', 'Created By', readonly=True)
    write_date = fields.Datetime('Modified On', readonly=True)
    write_uid = fields.Many2one('res.users', 'Last Modification By', readonly=True)
                            
yearly_holidays_log()


class holidays_list(models.Model):
    _name = 'holidays.list'
    _description = 'Holidays List'
    
    date = fields.Date('Holiday Date')
    reason = fields.Text('Reason For Holiday',size=300)
    yearly_holidays_id = fields.Many2one('yearly.holidays', 'Yearly Holidays')

    @api.constrains('date')
    def check_date(self):
        for record in self:
            year_value = datetime.strptime(record.date, "%Y-%m-%d")
            if record.yearly_holidays_id.year != year_value.year:
                raise ValidationError('Holiday Date must be in above given Year')

holidays_list()
