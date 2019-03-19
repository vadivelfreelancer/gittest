from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import babel
import logging


_logger = logging.getLogger(__name__)
   
class CalendarGeneration(models.Model):
    _name = 'calendar.generation'
    _inherit = 'mail.thread'
    _order = "id desc"
    _rec_name = 'fiscal_year_id'
    
    fiscal_year_id = fields.Many2one('fiscal.year',domain=[('active','=',True)],ondelete='cascade')
    date_start = fields.Date(string='Date From')
    date_end = fields.Date(string='Date To')
    #line_ids = fields.One2many('calendar.generation.line','calendar_generation_id',string="Month")
    
    #initial_date = fields.Date(string='Initial Date')
    state_id = fields.Many2one('res.country.state')
    region_id = fields.Many2one('pappaya.region')
    #hr_calendar_ids = fields.One2many('hr.calendar','generation_id',string='Calendar Line')
    state = fields.Selection([('draft', 'Draft'), ('request', 'Requested'), ('generated', 'Generated')], string="Status", default='draft', track_visibility='onchange', copy=False)
    hr_calendar_line_ids = fields.One2many('calendar.generation.line','calendar_generation_id',string='Calendar Line',ondelete='cascade')
    
    @api.constrains('fiscal_year_id')
    def check_fiscal_year_id(self):
        for record in self:
            if record.fiscal_year_id:
                calendar = record.env['calendar.generation'].search([('fiscal_year_id','=',record.fiscal_year_id.id)])
                if len(calendar) > 1:
                    raise ValidationError(_("Calendar was already generated for this Fiscal Year"))
    
    @api.multi
    def calender_generation(self):
        for record in self:
#             domain = []
#             if record.state_id:
#                 domain.append(('state_id','=',record.state_id.id))
#             if record.region_id:
#                 domain.append(('region_id','=',record.region_id.id))
#             
#             domain.append(('type','=','branch'))
#             branch_sr = self.env['operating.unit'].search(domain)
            for line in record.hr_calendar_line_ids:
                already_branch_ids = []
                for calendar in self.env['hr.calendar'].search([('date_from','=',line.date_start),('date_to','=',line.date_end)]):
                    already_branch_ids.append(calendar.branch_id.id)
                branch_sr = self.env['operating.unit'].search([('type','=','branch'),('id','not in',already_branch_ids)])
                for branch in branch_sr:
                    calendar_new = self.env['hr.calendar'].create({
                                                                    'branch_id' : branch.id,
                                                                    'date_from' :line.date_start,
                                                                    'date_to'   :line.date_end,
                                                                    'state'     :'draft',
                                                                    'generation_line_id':line.id
                                                                    })
                    calendar_new.onchange_branch_id()
                    _logger.info("HR and Payroll Calendar Generation Branch: <%s>, Calendar<%s>", branch.name,calendar_new.name)
            record.state = 'generated'
                

    @api.multi
    def action_submit(self):
        for record in self:
            record.state = 'request'

    @api.multi
    def schedule_action_calender_generation(self):
        fiscal_year_id = self.env['fiscal.year'].search([('active','=',True)])
        calender_generation_ids = self.search([('state','=','request'),('fiscal_year_id','in',fiscal_year_id.ids)])
        for calender_generation in calender_generation_ids:
            calender_generation.onchange_fiscal_year_id()
            calender_generation.calender_generation()
        return True
    
    @api.multi
    def schedule_action_calender_regeneration(self):
        fiscal_year_id = self.env['fiscal.year'].search([('active','=',True)])
        calender_generation_ids = self.search([('fiscal_year_id','in',fiscal_year_id.ids)])
        for calender_generation in calender_generation_ids:
            calender_generation.onchange_fiscal_year_id()
            calender_generation.calender_generation()
        return True

    
    @api.onchange('fiscal_year_id')
    def onchange_fiscal_year_id(self):
        for record in self:
            if record.fiscal_year_id and not record.hr_calendar_line_ids.ids:
                date_start          = datetime.strptime(record.fiscal_year_id.date_start, '%Y-%m-%d').date()
                date_end            = datetime.strptime(record.fiscal_year_id.date_end, '%Y-%m-%d').date()
                record.date_start   = date_start
                record.date_end     = date_end
                lines               = []
                if record.date_start and record.date_end:
                    fiscal_year_month_start_date    = datetime.strptime(record.date_start, '%Y-%m-%d').date()
                    if fiscal_year_month_start_date:
                        fiscal_year_month_start_date = fiscal_year_month_start_date.replace(day=1)
                    fiscal_year_month_last_date_str = datetime.strftime(date_end + relativedelta(months=+1, day=1, days=-1), "%Y-%m-%d")
                    fiscal_year_month_last_date     = datetime.strptime(fiscal_year_month_last_date_str, '%Y-%m-%d').date()
                    month_start_date                = fiscal_year_month_start_date
                    month_end_date_str              = datetime.strftime(fiscal_year_month_start_date + relativedelta(months=+1, day=1, days=-1), "%Y-%m-%d")
                    month_end_date                  = datetime.strptime(month_end_date_str, '%Y-%m-%d').date()
                    count = 1
                    while month_start_date < fiscal_year_month_last_date and month_end_date <= fiscal_year_month_last_date:
                        
                        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(month_end_date_str, "%Y-%m-%d")))
                        locale = self.env.context.get('lang') or 'en_US'
                        name = tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))
                        lines.append((0, 0, {
                                                 'date_start': month_start_date,
                                                 'date_end': month_end_date,
                                                 'name':name,
                                                 'fiscal_year_id':record.fiscal_year_id.id
                                                }
                                            ))
                        count +=1
                        month_end_date_str  = datetime.strftime(month_start_date + relativedelta(months=+2, day=1, days=-1), "%Y-%m-%d")
                        month_start_date    = datetime.strptime(month_end_date_str, '%Y-%m-%d').date().replace(day=1)
                        month_end_date      = datetime.strptime(month_end_date_str, '%Y-%m-%d').date()
                record.hr_calendar_line_ids =  lines       
                        
                    
                
    
    
class CalendarGenerationLine(models.Model):
    _name = 'calendar.generation.line'
    _inherit = 'mail.thread'
    _order = "date_start"
     
    calendar_generation_id = fields.Many2one('calendar.generation',ondelete='cascade')
    #branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    fiscal_year_id = fields.Many2one('fiscal.year')
    name = fields.Char('Name' ,size=150)
    date_start = fields.Date(string='Date From')
    date_end = fields.Date(string='Date To')
    hr_calendar_ids = fields.One2many('hr.calendar','generation_line_id',string='Calendar Line')
    fiscal_year_active = fields.Boolean(string='Fiscal Year',compute='get_fiscal_year_active')
    
    @api.depends('fiscal_year_active')
    def get_fiscal_year_active(self):
        for record in self:
            if record.fiscal_year_id:
                record.fiscal_year_active = record.fiscal_year_id.active
            elif record.calendar_generation_id:
                record.fiscal_year_active = record.calendar_generation_id.fiscal_year_id.active
            else:
                record.fiscal_year_active = False
    
    #state = fields.Selection([('')])
            
            
class FiscalYear(models.Model):
    _inherit = "fiscal.year"

    calendar_generation_id = fields.Many2one('calendar.generation')
    calendar_created = fields.Boolean('Calendar Created?')
    
    @api.model
    def create(self, vals):
        res = super(FiscalYear, self).create(vals)
        calendar_generation_id = self.env['calendar.generation'].create({'fiscal_year_id': res.id
                                                                         })
        calendar_generation_id.onchange_fiscal_year_id()
        calendar_generation_id.write({'state':'request'})
        res['calendar_generation_id'] = calendar_generation_id.id
        res['calendar_created'] = True
        return res
    
    @api.multi
    def write(self, vals):
        res = super(FiscalYear, self).write(vals)
        return res
            
    
            
# 
# 
#     @api.
    
    