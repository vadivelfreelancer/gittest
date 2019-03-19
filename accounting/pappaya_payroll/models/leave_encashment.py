# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from odoo import tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
import re
import math
import calendar

class leave_encashment_request(models.Model):
    _name='leave.encashment.request'
    _inherit = 'mail.thread'
    _mail_post_access = 'read'
    _rec_name= 'year'
    
    name = fields.Char('Name',size=100)
    employee_id = fields.Many2one('hr.employee', 'Employee')
    emp_id = fields.Char(related='employee_id.emp_id', string='Employee ID')
    requested_date = fields.Date('Date', default=fields.Date.today())
    state = fields.Selection([('draft', 'Draft'),('requested', 'Requested'),('approved', 'Approved'),
                              ('carry_forward', 'carry forward'),('paid', 'Encashment Paid'), 
                              ('rejected', 'Rejected'),('cancelled', 'Cancelled')], default='draft',track_visibility='onchange')
    year = fields.Selection([(num, str(num)) for num in range(((datetime.now().year)-1), ((datetime.now().year)+1))], 'Leave Year')
    carryforward_year = fields.Selection([(num, str(num)) for num in range(((datetime.now().year)), ((datetime.now().year)+2))], 'Leave carryforward Year')
    leave_balance_count = fields.Float('Leave balance in days')
    encashment_amount = fields.Float('Encashment Amount', help="no.of leave balance/no of eligibility per year * wage")
    
    type = fields.Selection([('encashment','Encashment')],default='encashment')
    lines = fields.One2many('leave.encashment.carryforward.line','leave_id',string='Lines')
    previous_holidays_ids = fields.Many2many('hr.holidays', 'hr_holidays_encasment_rel', 'encashment_id','holiday_id',string='previous holidays')
    payslip_id = fields.Many2one('hr.payslip')


#     @api.constrains('payslip_id','type')
#     def check_constrains_last_month_payslip(self):
#         for record in self:
#             if record.type == 'encashment' and not record.payslip_id:
#                 raise ValidationError(_('Please generate previous month payslip'))

    @api.constrains('employee_id','year','carryforward_year')
    def check_constrains_employee_year(self):
        for record in self:
            if len(record.search([('employee_id','=',record.employee_id.id),('year','=',record.year),('state','!=','rejected')]).ids) > 1:
                raise ValidationError(_('Already Leave  carry forward or encashment - %s Request applied ') % str(record.year))
            if record.type == 'carry_forward' and record.year and record.carryforward_year:
                if record.year == record.carryforward_year:
                    raise ValidationError(_('You are not allowed to Carryforward/Encashment for same years'))
                

    @api.onchange('employee_id','type','year')
    def onchange_requested_by(self):
        type = {'carry_forward':'carry forward','encashment':'encashment'}
        for record in self:
            if record.employee_id and record.type and record.year:
                record.name = record.employee_id.name and  record.employee_id.name +' is requesting for leave '+ type[record.type]
                total_leave_balance_count = 0.00
                previous_holidays_ids = []
                if record.type == 'encashment':
                    encashment_list = []
                    for holiday_status_id in self.env['hr.holidays.status'].search([('leave_encashment','=','yes')]):
                        leave_balance_count = 0.0
                        allocated_days = 0.0
                        leave_taken = 0.0
                        leaves_sr = self.env['hr.holidays'].search([('employee_id','=',record.employee_id.id),('holiday_status_id', '=', holiday_status_id.id),('state','=','validate'),('year_of_passing','=',record.year)])
                        
                        for leave in leaves_sr:
                            if leave.holiday_status_id and leave.holiday_status_id.leave_encashment == 'yes':
                                if leave.type == 'add':
                                    allocated_days += leave.number_of_days_temp
                                    if leave.number_of_days_temp:
                                        previous_holidays_ids.append(leave.id)
                                elif leave.type == 'remove':
                                    leave_taken += abs(leave.number_of_days_temp)
                        
#                         leave_balance_holidays_count = 0.00
#                         leave_balance_holidays_count = (abs(allocated_days) - abs(leave_taken))
#                         if leave_balance_holidays_count:
#                                     previous_holidays_ids = previous_holidays_ids + 
                                        
                        if holiday_status_id.leave_encashment_type == 'Balanced':
                            leave_balance_count += (abs(allocated_days) - abs(leave_taken))
                        else:
                            if holiday_status_id.max_leave_encashment_days:
                                if (abs(allocated_days) - abs(leave_taken)) >=  holiday_status_id.max_leave_encashment_days:
                                    leave_balance_count += holiday_status_id.max_leave_encashment_days
                                else:
                                    leave_balance_count += (abs(allocated_days) - abs(leave_taken))
                            else:
                                leave_balance_count += (abs(allocated_days) - abs(leave_taken))
                        if leave_balance_count:
                            encashment_list.append((0,0,{
                                                            'leave_id':record.id,
                                                            'holiday_status_id':holiday_status_id.id,
                                                            'leave_balance':leave_balance_count
                                                            }))
                        total_leave_balance_count += leave_balance_count
                            
                    record.lines = None
                    record.lines = encashment_list
                    record.leave_balance_count = 0.00
                    record.leave_balance_count = total_leave_balance_count

                    record.encashment_amount = 0
                    if record.leave_balance_count :
#                         last_payslip = self.env['hr.payslip'].search([('employee_id', '=', record.employee_id.id),('branch_id', '=', record.employee_id.branch_id.id)],order='id desc', limit=1)
#                         record.payslip_id = last_payslip.id
                        gross_salary = record.employee_id.gross_salary
                        if gross_salary > 0.00:
                            gross_salary = gross_salary * 0.30
                        
                        requested_date = record.requested_date
                        days_total = 0.00
                        date_from    = datetime.strptime(record.requested_date, '%Y-%m-%d').date().replace(day=1)
                        end_date_str = datetime.strftime(date_from + relativedelta(months=+1, day=1, days=-1), "%Y-%m-%d")
                        date_to    = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                        days_total = (date_to - date_from).days + 1
                        # if last_payslip_basic_amt:
                        #     record.encashment_amount = math.ceil((last_payslip_basic_amt/days_total) * record.leave_balance_count)
                        for line in record.lines:
                            if line.holiday_status_id.code == 'PRL':
                                record.encashment_amount += math.ceil((gross_salary / 30) * line.leave_balance)
                            else:
                                record.encashment_amount += math.ceil((gross_salary / days_total) * line.leave_balance)
                else:
                    record.carryforward_year = None
                    carry_forward_list = []
                    for holiday_status_id in self.env['hr.holidays.status'].search([('carry_forward','=','yes')]):
                        leave_balance_count = 0.0
                        allocated_days = 0.0
                        leave_taken = 0.0
                        leaves_sr = self.env['hr.holidays'].search([('employee_id','=',self.employee_id.id),('holiday_status_id', '=', holiday_status_id.id),('state','=','validate'),('year_of_passing','=',record.year)])
        
                        for leave in leaves_sr:
                            if leave.holiday_status_id and leave.holiday_status_id.carry_forward == 'yes':
                                if leave.type == 'add':
                                    allocated_days += leave.number_of_days_temp
                                    if leave.number_of_days_temp:
                                        previous_holidays_ids.append(leave.id)
                                elif leave.type == 'remove':
                                    leave_taken += abs(leave.number_of_days_temp)
        
                        if holiday_status_id.carry_forward_type == 'Balanced':
                            leave_balance_count += (abs(allocated_days) - abs(leave_taken))
                        else:
                            if holiday_status_id.max_carry_days:
                                if (abs(allocated_days) - abs(leave_taken)) >=  holiday_status_id.max_carry_days:
                                    leave_balance_count += holiday_status_id.max_carry_days
                                else:
                                    leave_balance_count += (abs(allocated_days) - abs(leave_taken))
                            else:
                                leave_balance_count += (abs(allocated_days) - abs(leave_taken))
                        if leave_balance_count:
                            carry_forward_list.append((0,0,{
                                                            'leave_id':record.id,
                                                            'holiday_status_id':holiday_status_id.id,
                                                            'leave_balance':leave_balance_count
                                                            }))
                            total_leave_balance_count += leave_balance_count
                    record.lines = None
                    record.lines = carry_forward_list
                record.leave_balance_count = 0.00    
                record.leave_balance_count = total_leave_balance_count
                record.previous_holidays_ids = None        
                record.previous_holidays_ids = previous_holidays_ids               

    
    @api.model
    def default_get(self, fields):
        res = super(leave_encashment_request, self).default_get(fields)
        if self.env['hr.employee'].search([('user_id','=',self._uid)]):
            res['employee_id'] = self.env['hr.employee'].search([('user_id','=',self._uid)]).id
        return res

    
    @api.multi
    def button_request(self):
        for record in self:
            record.write({'state': 'requested'})
            
    @api.multi
    def button_approve(self):
        for record in self:
            if record.type == 'encashment':
                record.previous_holidays_ids.write({'encashment_leave':record.id})
                record.write({'state': 'approved'})
            else:
                for line in record.lines:
                    if line.leave_balance > 0:
                        carry_forward_holidays = self.env['hr.holidays'].create({
                                                                                    'employee_id':record.employee_id.id,
                                                                                    'type':'add',
                                                                                    'state':'draft',
                                                                                    'year_of_passing':record.carryforward_year,
                                                                                    'holiday_status_id':line.holiday_status_id.id,
                                                                                    'number_of_days_temp':line.leave_balance,
                                                                                    'from_carry_forward_leave':record.id
                                                                                    })
                        carry_forward_holidays.action_confirm()
                        carry_forward_holidays.action_approve()
                for previous_allocate_holiday in record.previous_holidays_ids:
                    previous_allocate_holiday.write({'to_carry_forward_leave':record.id})
                record.write({'state': 'carry_forward'})
                            
            
    @api.multi
    def button_reject(self):
        for record in self:
            record.write({'state': 'rejected'})
            
    @api.multi
    def button_reset(self): 
        for record in self:
            record.write({'state': 'draft'})        
        
    @api.multi
    def button_cancel(self):
        for record in self:
            record.write({'state': 'cancelled'})  
            
            
class LeaveEncashmentCarryForwardLine(models.Model):
    _name = 'leave.encashment.carryforward.line'
    
    leave_id = fields.Many2one('leave.encashment.request', string='Leave Encashment / Carryforward')
    holiday_status_id = fields.Many2one('hr.holidays.status',string='Leave Type')
    leave_balance = fields.Float(string='Leave Balance')
    
    
             

