# -*- coding:utf-8 -*-
import time
from datetime import datetime, timedelta
from datetime import time as datetime_time
from dateutil.relativedelta import relativedelta

import babel
import base64
import logging

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from num2words import num2words
from io import StringIO
from time import gmtime, strftime
import dateutil.parser
from odoo.tools import float_compare, float_is_zero
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import threading


from xlwt import *
#from __builtin__ import True
try:
    import xlwt
except:
    raise osv.except_osv('Warning !','python-xlwt module missing. Please install it.')

import os


_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _order = 'emp_no asc'

    #~ is_payslip = fields.Boolean('If payslip')
    
    branch_id = fields.Many2one('operating.unit', 'Branch',domain=[('type','=','branch')])
    attendance_days_line_ids = fields.One2many('hr.payslip.attendance_days', 'payslip_id',
        string='Payslip Attendance Days', copy=True, readonly=True,
        states={'draft': [('readonly', False)]})
    emp_no = fields.Char(related='employee_id.emp_id', string='Employee ID')
    total_work_days = fields.Float(string='Total Days',compute="cal_total_days_and_hours")
    total_work_hours = fields.Float(string='Total Hours',compute="cal_total_days_and_hours")
    lop_hours = fields.Float(string='LOP Hours',compute="cal_lop_days_and_hours")
    lop_days = fields.Float(string='LOP Days',compute="cal_lop_days_and_hours")
    
    paid_hours = fields.Float(string='Paid Hours',compute="cal_lop_days_and_hours")
    paid_days = fields.Float(string='Paid Days',compute="cal_lop_days_and_hours")
    
    acc_number = fields.Char(string='Bank Account Number',related='employee_id.bank_account_id.acc_number')
    passport_id = fields.Char(string='Passport Number',related='employee_id.passport_id')
    
    is_lock = fields.Boolean('Process Salary', default=False)
    is_sublock = fields.Boolean('Release Payment', default=False)
    is_payroll_cycle = fields.Boolean('Payroll Cycle', default=False)
    work_hours = fields.Float(string="Work Hours",compute="cal_total_days_and_hours")
    
    employee_lock_sublock = fields.Many2one('employee.lock.sublock.line')
    partial_move_id = fields.Many2one('account.move', 'Partial Accounting Entry', readonly=True, copy=False)
    partial_date = fields.Date('Partial Date Account', states={'draft': [('readonly', False)]}, readonly=True,
        help="Keep empty to use the period of the validation(Payslip) date.")

    net_amount = fields.Float(compute='_get_net_amount', string='Net Amount')
    gross_amount = fields.Float(compute='_get_net_amount', string='Gross')
    basic_amount = fields.Float(compute='_get_net_amount', string='Basic')
    da_amount = fields.Float(compute='_get_net_amount', string='DA')
    hra_amount = fields.Float(compute='_get_net_amount', string='HRA')
    pf_amount = fields.Float(compute='_get_net_amount', string='PF')
    esi_amount = fields.Float(compute='_get_net_amount', string='ESI')
    loan_amount = fields.Float(compute='_get_net_amount', string='Loan')
    pt_amount = fields.Float(compute='_get_net_amount', string='PT')
    lop_amount = fields.Float(compute='_get_net_amount', string='LOP')
    month_name = fields.Char(compute='_get_month_name', string='Month')

    payslip_bank_id = fields.Many2one('res.bank', string='Payslip Bank')
    
    company_id = fields.Many2one('res.company', string='Organization', readonly=True, copy=False,
        default=lambda self: self.env['res.company']._company_default_get(),
        states={'draft': [('readonly', False)]})

    employee_attendance_line = fields.Many2many('hr.daily.attendance.line', string='Employee Attendance Line')
    is_paysheet_created = fields.Boolean('Is Paysheet Created', default=False)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if 'date_from' in groupby:
            orderby = 'date_from DESC' + (orderby and (',' + orderby) or '')

        return super(HrPayslip, self).read_group(domain, fields, groupby, offset=0, limit=limit, orderby=orderby, lazy=lazy)

    @api.multi
    def report_payslip_emp(self):
        return self.env.ref('pappaya_payroll.nspira_payslip_reports').report_action(self)

    @api.multi
    def payslip_report_name(self):
        for record in self:
            name = ''
            if record.date_to:
                date_to = datetime.strptime(self.date_to, '%Y-%m-%d').date()
                name = _('%s' + '_'+'%s'+'_'+'%s'+'_payslip' ) % (record.employee_id.emp_id,date_to.month,date_to.year)
            else:
                name = 'Payslip'
            return name

    def _get_net_amount(self):
        for record in self:
            net_amount = gross_amount = basic_amount = da_amount = hra_amount = pf_amount = esi_amount = loan_amount = pt_amount = lop_amount = 0
            for rule in record.line_ids:
                if rule.code == 'NET':
                    net_amount = rule.total
                if rule.code == 'GROSS':
                    gross_amount = rule.total
                if rule.code == 'BASIC':
                    basic_amount = rule.total
                if rule.code == 'DA':
                    da_amount = rule.total
                if rule.code == 'HRA':
                    hra_amount = rule.total
                if rule.code == 'PF':
                    pf_amount = rule.total
                if rule.code == 'ESI':
                    esi_amount = rule.total
                if rule.code == 'LOAN':
                    loan_amount = rule.total
                if rule.code == 'professional_tax':
                    pt_amount = rule.total
                if rule.code == 'LOP':
                    lop_amount = rule.total

            record.gross_amount = gross_amount
            record.net_amount = net_amount
            record.basic_amount = basic_amount
            record.da_amount = da_amount
            record.hra_amount = hra_amount
            record.pf_amount = pf_amount
            record.esi_amount = esi_amount
            record.loan_amount = loan_amount
            record.pt_amount = pt_amount
            record.lop_amount = lop_amount

    def _get_month_name(self):
        for record in self:
            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(record.date_from, "%Y-%m-%d")))
            locale = self.env.context.get('lang') or 'en_US'
            record.month_name = tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))

    @api.onchange('employee_id')
    def employee_onchange(self):
        for record in self:
            if record.employee_id:
                record.branch_id = record.employee_id.branch_id

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee_id_value(self):
        for record in self:
            if record.employee_id and record.date_from and record.date_to:
                attendance_line = self.env['hr.daily.attendance.line'].search([('employee_id', '=', record.employee_id.id), \
                     ('attendance_date', '>=', record.date_from), ('attendance_date', '<=', record.date_to)], order='attendance_date')

                record.employee_attendance_line = [(6, 0, attendance_line.ids)]


    @api.multi
    def action_payslip_done_modification(self):
        print ("122222222222222222222222222")
        precision = self.env['decimal.precision'].precision_get('Payroll')

        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'operating_unit_id': slip.branch_id.id,
                'date': date,
            }
            if slip.credit_note:
                for slip_line in slip.line_ids:
                    if slip_line.salary_rule_id.code != 'NET':
                        slip_line.sudo().unlink()
            for line in slip.details_by_salary_rule_category:
                amount  = 0.00
                debit_account_id = None
                credit_account_id = None
                if not slip.credit_note:
                    # Revert lock and sub lock logic
#                     if not slip.is_sublock or not slip.is_lock and not line.account_move:
#                         if line.salary_rule_id.is_statutory:
#                             amount = slip.credit_note and -line.total or line.total
#                             if float_is_zero(amount, precision_digits=precision):
#                                 continue
#                             debit_account_id = line.salary_rule_id.account_debit.id
#                             credit_account_id = line.salary_rule_id.account_credit.id
#                     
#                     elif slip.is_sublock and slip.is_sublock and not line.account_move:
                    amount = slip.credit_note and -line.total or line.total
                    if float_is_zero(amount, precision_digits=precision):
                        continue
                    debit_account_id = line.salary_rule_id.account_debit.id
                    credit_account_id = line.salary_rule_id.account_credit.id
                    
                else:
                    # Refund Logic
                    if line.amount > 0.00 and line.salary_rule_id.code == 'NET':
                        amount = -line.total 
                        if float_is_zero(amount, precision_digits=precision):
                            continue
                        debit_account_id = line.salary_rule_id.account_debit.id
                        credit_account_id = line.salary_rule_id.account_credit.id
                            
                if debit_account_id:
                    
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                    line.account_move = True
                    
                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                    line.account_move = True
            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            #if slip.is_sublock and slip.is_lock :
            slip.write({'move_id': move.id, 'date': datetime.today().date(),'state': 'done'})
            slip.employee_lock_sublock.write({'account_entry':move.id})
#             else:
#                 slip.write({'partial_move_id': move.id, 'date': date})
#                 slip.employee_lock_sublock.write({'partial_account_entry':move.id})
            move.post()
        return True
    
    @api.multi
    def refund_sheet(self):
        for payslip in self:
            if not payslip.number:
                payslip.number = payslip.env['ir.sequence'].sudo().next_by_code('salary.slip')
            copied_payslip = payslip.sudo().copy({'credit_note': True, 'name': _('Refund: ') + payslip.number + ' - '+ payslip.name})
            copied_payslip.compute_sheet()
            copied_payslip.action_payslip_done_modification()
        formview_ref = self.env.ref('hr_payroll.view_hr_payslip_form', False)
        treeview_ref = self.env.ref('hr_payroll.view_hr_payslip_tree', False)
        return {
            'name': ("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'), (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }

    def get_name_for_payslip(self):
        for record in self:
            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(record.date_to, "%Y-%m-%d")))
            locale = self.env.context.get('lang') or 'en_US'
            month_value = tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))
            report_name = "Pay Slip for the Month of " + month_value
            return report_name

    @api.constrains('date_from','date_to')
    def check_date_from(self):
        for record in self:
            date_from = dateutil.parser.parse(record.date_from).date()
            if date_from > datetime.today().date():
                raise ValidationError("From Date must be less than or equal to Current Date")
            date_to = dateutil.parser.parse(record.date_to).date()
            if date_to > datetime.today().date():
                raise ValidationError("To Date must be less than or equal to Current Date")

    @api.multi
    def net_amount_in_words(self, key):
        net_amount = False
        net_amount_in_words = False
        for record in self:
            for line_id in record.line_ids:
                if line_id.category_id.code == 'NET':
                    net_amount = line_id.total
                    net_amount_in_words = 'Net Pay: '+num2words(line_id.total).title()+' Rupees only'
        if net_amount or net_amount_in_words:
            if key == 'net_amount':
                return net_amount
            elif key == 'net_amount_words':
                return net_amount_in_words
    
#     @api.depends('lop_days','total_work_hours')
#     def cal_paid_days_and_hours(self):
#         for record in self:
#             paid_days = 0.00
#             paid_hours = 0.00
#             record.paid_days = record.total_work_days - record.lop_days
#             record.paid_hours = record.total_work_hours - record.lop_hours
            
    @api.depends('lop_hours','lop_days')
    def cal_lop_days_and_hours(self):
        for record in self:
            pr_days = 0.00
            pr_hours = 0.00
            partial_pr_days = 0.00
            for line in record.worked_days_line_ids:
                if line.code in ['WF','PH','Leave']:
                    pr_days += line.number_of_days
                    pr_hours += line.number_of_hours
                if line.code == 'PR':
                    pr_days += line.number_of_days
                    pr_hours += line.number_of_hours
                if  line.code == 'PPR' and line.number_of_days:
                    partial_pr_days +=  0.5
                    pr_hours += line.number_of_hours
                    
            total_days = (pr_days + partial_pr_days)
            if total_days >= record.total_work_days:
                record.lop_days = 0.00
                record.lop_hours = 0.00
                record.paid_days = record.total_work_days
                record.paid_hours = record.total_work_hours
            else:
                record.lop_days = record.total_work_days - total_days
                record.lop_hours = record.total_work_hours - pr_hours
                record.paid_days = record.total_work_days - record.lop_days
                record.paid_hours = record.total_work_hours - record.lop_hours
                
    
    def _get_days_payable(self):
        working_days = 0.0
        for record_line in self.worked_days_line_ids:
            working_days += record_line.number_of_days
        return working_days
    
    @api.multi
    def work_days(self):
        unpaid = 0
        lst = []
        start = datetime.strptime(self.date_from, '%Y-%m-%d').date()
        end = datetime.strptime(self.date_to, '%Y-%m-%d').date()
        work_days = relativedelta(end,start)
        total_days = work_days.days + 1
        for rec in self.worked_days_line_ids:
            if rec.code == 'Unpaid':
                unpaid += rec.number_of_days
        vals = {}
        vals['total_days'] = total_days
        vals['paid_days'] = int(total_days - unpaid)
        lst.append(vals)
        return lst

    @api.multi
    def get_worked_day_lines_payslip(self):
        contracts, date_from, date_to = self.contract_id, self.date_from,self.date_to;
        print (self,"2222222222222222222222222222222222222222")
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), datetime_time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), datetime_time.max)
            # leave Present
            
            count = 0
            no_of_pr_hours = 0.00
            week_off = 0.00
            holiday = 0.00
            # Employees configuration working hours and ot hours
            maxmum_working_hr = self.employee_id.emp_work_hours.total_work_hours
            org_last_present_date = None
            last_present_date = self.env['hr.daily.attendance.line'].search([('attendance_date','>=',date_from),
                                                                             ('attendance_date','<=',date_to),
                                                                             ('attendance_status','=','present'),
                                                                             ('employee_id','=',self.employee_id.id),('state','=','done')],order="attendance_date desc",limit=1)
            if last_present_date :
                org_last_present_date = last_present_date.attendance_date
            dates = None
            if org_last_present_date:
                dates= self.generate_dates(date_from,org_last_present_date)
            if dates:
                unfound_calendar = []
                for date in dates:
                    monthly_calender = self.env['hr.calendar'].search([('branch_id','=',self.branch_id.id),('date_from','<=',date),('date_to','>=',date)])
                    if not monthly_calender:
                        unfound_calendar.append(str(date))
                print (unfound_calendar,"unfound_calendarunfound_calendarunfound_calendar")
                if unfound_calendar:    
                    raise ValidationError(_('Please create calendar for the selected payroll cycle'))
                else:
                    monthly_calender = self.env['hr.calendar'].search([('branch_id','=',self.branch_id.id),('date_from','<=',date_from),('date_to','>=',date_to)]).ids
                    for date in dates: 
                        calendar_line = self.env['hr.calendar.line'].search([('calendar_id','in',monthly_calender),('date','=',date)])
                        if calendar_line.work_type == 'work':
                            daily_attendance = self.env['hr.daily.attendance'].search([('attendance_date','=',calendar_line.date),
                                                                                       ('state','=','done')])
                            daily_attendance_line = self.env['hr.daily.attendance.line'].search([('daily_attendance_id','in',daily_attendance.ids),
                                                                                                 ('employee_id','=',self.employee_id.id)])
                            worked_hour = 0.00
                            for attendance_line in daily_attendance_line:
                                if attendance_line.attendance_status == 'present':
                                    worked_hour += attendance_line.worked_hours
                            if maxmum_working_hr <= worked_hour:
                                no_of_pr_hours += maxmum_working_hr
                            else:
                                no_of_pr_hours += worked_hour
                        elif calendar_line.work_type == 'week_off':
                            leave = False
                            for leaves in self.env['hr.holidays'].search([('employee_id', '=', self.employee_id.id),
                                                                       '|',('date_to', '<=', date_to),
                                                                       ('date_from','>=',date_from),
                                                                       ('type','=','remove'),
                                                                       ('state','=','validate')
                                                                       ]):
                                leave_line = leaves.holiday_calendar_line.search([('id','in',leaves.holiday_calendar_line.ids),('date','=',calendar_line.date)])
                                if leave_line:
                                    leave = True
                            if not leave:                
                                week_off += 1
                        elif calendar_line.work_type == 'holiday':
                            leave = False
                            for leaves in self.env['hr.holidays'].search([('employee_id', '=', self.employee_id.id),
                                                                       '|',('date_to', '<=', date_to),
                                                                       ('date_from','>=',date_from),
                                                                       ('type','=','remove'),
                                                                       ('state','=','validate')
                                                                       ]):
                                leave_line = leaves.holiday_calendar_line.search([('date','=',calendar_line.date)])
                                if leave_line:
                                    leave = True
                            if not leave:                
                                holiday += 1
                        
            
            no_of_days = 0
            if no_of_pr_hours and maxmum_working_hr > 0:
                no_of_days = no_of_pr_hours / maxmum_working_hr
            if no_of_days:
                res.append({'name': 'Present','sequence': 3,'code': 'PR','number_of_days': no_of_days,
                            'number_of_hours': no_of_pr_hours,'contract_id': contract.id})
            if week_off:
                res.append({'name': 'Weekly Off','sequence': 3,'code': 'WF','number_of_days': week_off,
                            'number_of_hours': week_off * maxmum_working_hr,'contract_id': contract.id})
            if holiday:
                res.append({'name': 'Public Holiday','sequence': 3,'code': 'PH','number_of_days': holiday,
                            'number_of_hours': holiday * maxmum_working_hr,'contract_id': contract.id})

            
            # Leave absent
            count = 0
            total_leave_count = 0
            for holiday_status_id in self.env['hr.holidays.status'].sudo().search([('active','=',True)]):
                leave_count = 0
                for leaves in self.env['hr.holidays'].search([('employee_id', '=', self.employee_id.id),
                                                                   '|',('date_to', '<=', date_to),
                                                                   ('date_from','>=',date_from),
                                                                   ('type','=','remove'),
                                                                   ('state','=','validate'),
                                                                   ('holiday_status_id', '=', holiday_status_id.id)]):
                    leave_count += leaves.number_of_days_temp 
                    total_leave_count += leave_count
                
                if leave_count and  holiday_status_id.code != 'LWP':    
                    if leave_count: 
                        res.append({
                                'name': holiday_status_id.name,
                                'sequence': 4,
                                'code': 'Leave',
                                'number_of_days': leave_count,
                                'number_of_hours': leave_count * self.employee_id.emp_work_hours.total_work_hours,
                                'contract_id': contract.id,
                            }
                            )
                elif holiday_status_id.code == 'LWP':
                    res.append({
                            'name': holiday_status_id.name,
                            'sequence': 4,
                            'code': 'LWP',
                            'number_of_days': -(leave_count),
                            'number_of_hours': leave_count * self.employee_id.emp_work_hours.total_work_hours,
                            'contract_id': contract.id,
                        }
                        )
            
            self.worked_days_line_ids = res
            
            input_lines = []
            leave_encashment = self.env['leave.encashment.request'].search([('employee_id','=',self.employee_id.id),('requested_date','>=',date_from),
                                                                            ('requested_date','<=',date_to),('state','=','approved'),
                                                                            ('type','=','encashment')])
            if leave_encashment:
                for leave_encash in leave_encashment:
                    input_lines.append((0,0,{
                                'name': leave_encash.name,
                                'sequence': 10,
                                'code': 'LE',
                                'amount':leave_encash.encashment_amount,
                                'contract_id': contract.id,
                            }
                            ))
                    for previous_allocate_holiday in leave_encash.previous_holidays_ids:
                        previous_allocate_holiday.write({'to_carry_forward_leave':leave_encash.id})
                    leave_encash.write({'state':'paid'})

            advance_value = self.env['hr.advance'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approve'),
                 ('branch_id', '=', self.branch_id.id), ('date', '>=', date_from), ('date', '<=', date_to)])
            for advance in advance_value:
                input_lines.append((0, 0, {
                        'name': 'Salary Advance',
                        'sequence': 10,
                        'code': 'ADV',
                        'amount': advance.advance_amount,
                        'contract_id': contract.id,
                    }
                ))
                advance.amount_deduct_payslip_id = self.id
            
            other_alw_ded = self.env['other.allowance.and.deduction'].search([('date_from','>=',date_from),('date_to','>=',date_to),('state','=','done')])
            employee_alw_ded = self.env['other.allowance.and.dedution.line'].search([('employee_id','=',self.employee_id.id),('other_allowance_and_deduction_id','in',other_alw_ded.ids)])
            if employee_alw_ded:
                input_lines.append((0, 0, {
                            'name': employee_alw_ded.other_allowance_and_deduction_id.salary_rule_id.name,
                            'sequence': 10,
                            'code': employee_alw_ded.other_allowance_and_deduction_id.salary_rule_id.code,
                            'amount': employee_alw_ded.amount,
                            'contract_id': contract.id,
                        }
                    ))
                employee_alw_ded.write({'state':'archived'})
                employee_alw_ded.other_allowance_and_deduction_id.write({'state':'archived'})
            self.input_line_ids =  input_lines   
                
            # compute worked days
            #work_data = contract.employee_id.get_work_days_data(day_from, day_to, calendar=contract.resource_calendar_id)
            
    @api.depends('total_work_days','total_work_hours')
    def cal_total_days_and_hours(self):
        for record in self:
            date_from = datetime.strptime(record.date_from, "%Y-%m-%d") 
            date_to = datetime.strptime(record.date_to, "%Y-%m-%d")        
            days_total = (date_to.date() - date_from.date()).days + 1
            record.total_work_days = days_total
            #status_type_id = self.env['branch.officetype.workhours.line'].search([('branch_id','=',record.employee_id.branch_id.id),('status_type','=','present')],limit=1)
            status_type_id = []
            status_type_id = self.env['branch.officetype.workhours.line'].search([('employee_type','=',record.employee_id.employee_type.id),('branch_id','=',record.branch_id.id)],limit=1)
            if not status_type_id:
                status_type_id = self.env['branch.officetype.workhours.line'].search([('branch_id','=',record.branch_id.id)],limit=1)
            min_work_hours = 0.00
            if status_type_id:
                min_work_hours = status_type_id.min_work_hours
            record.work_hours = min_work_hours
            record.total_work_hours = (days_total * min_work_hours)
            

    @api.multi
    def generate_dates(self, date_from, date_to):
        dates = []
        td = timedelta(hours=24)
        current_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        while current_date <= datetime.strptime(date_to, "%Y-%m-%d").date():
            dates.append(current_date)
            current_date += td
        return dates
    
    
    @api.multi
    def compute_sheet(self):
        for payslip in self:
            contract_ids = payslip.contract_id.ids
            work_hours = self.env['branch.officetype.workhours.line'].search([('branch_id','=',payslip.branch_id.id),('status_type','=','present')],limit=1)
            
            print (payslip.employee_id.id,payslip.contract_id.id,payslip.branch_id.id,payslip.id,payslip.date_from,payslip.date_to,work_hours.min_work_hours,"3444444444444444444444")
            self.env.cr.execute(""" select create_payslip_lines(%s, %s, %s, %s, %s, %s,%s); """,
                                            (payslip.employee_id.id,payslip.contract_id.id,payslip.branch_id.id,payslip.id,payslip.date_from,payslip.date_to,work_hours.min_work_hours))
            if payslip.line_ids:
                self.env.cr.execute('delete from hr_payslip_line WHERE id in %s', (tuple(payslip.line_ids.ids),))
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines})
        return True
    
    @api.multi
    def cron_compute_sheet(self):
        for payslip in self:
            contract_ids = payslip.contract_id.ids
            if payslip.line_ids:
                self.env.cr.execute('delete from hr_payslip_line WHERE id in %s', (tuple(payslip.line_ids.ids),))
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.onchange_employee_id_value()
            payslip.write({'line_ids': lines})
        return True
    
    
    @api.multi
    def exit_compute_sheet(self):
        for payslip in self:
            if not payslip.contract_id:
                current_contract = self.env['hr.contract'].search([('employee_id', '=', payslip.employee_id.id),('state','=','open')])
                payslip.contract_id = current_contract.id
                payslip.struct_id = current_contract.struct_id.id
            contract_ids = payslip.contract_id.ids
            payslip.get_worked_day_lines_payslip()
            payslip.line_ids.unlink()
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines})
            payslip.refresh_payslip()
        return True
    
    @api.multi
    def refresh_payslip(self):
        for record in self:
            basic = 0.00
            alw = 0.00
            ded = 0.00
            net_id = None
            for line in record.line_ids:
                if line.amount == 0:
                    line.unlink()
                elif line.category_id.code == 'BASIC':
                    basic += line.amount
                elif line.category_id.code == 'ALW':
                    alw += line.amount
                elif line.category_id.code == 'DED':
                    ded += line.amount
                elif line.category_id.code == 'NET':
                    net_id = line
            if net_id:
                net_id.write({'amount':basic+alw - ded})
                
                    
    
class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'


    @api.multi
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note','company_id','branch_id'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        company_id = run_data.get('company_id')
        branch_id = run_data.get('branch_id')
        employee_lock_sublock_sr = self.env['employee.lock.sublock'].search([('branch_id','=', branch_id[0]),('payslip_batch_id','=',active_id),'|',('is_active','=',True),('is_active','=',False)])
        [data] = self.read()
        if not employee_lock_sublock_sr:
            raise UserError(_("You must create Lock/Sublock."))
        for lock_sublock in employee_lock_sublock_sr:
            for line_id in lock_sublock.lock_sublock_line:
                if line_id.employee_id.id != 1 and line_id.employee_id.date_of_joining <= to_date \
                        and line_id.employee_id.contract_id and line_id.employee_id.contract_id.struct_id:
                    if not line_id.is_sublock:
                        exsit_payslip_sr = self.env['hr.payslip'].search([('employee_id','=',line_id.employee_id.id),
                                                                            ('payslip_run_id','=',active_id),
                                                                            ('date_from','=',from_date),
                                                                            ('date_to','=',to_date),
                                                                            ])
                        if not exsit_payslip_sr:
                            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, line_id.employee_id.id, contract_id=False)
                            res = {
                                'employee_id': line_id.employee_id.id,
                                'name': slip_data['value'].get('name'),
                                'struct_id': slip_data['value'].get('struct_id'),
                                'contract_id': slip_data['value'].get('contract_id'),
                                'payslip_run_id': active_id,
                                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                                'date_from': from_date,
                                'date_to': to_date,
                                'credit_note': run_data.get('credit_note'),
                                'company_id': line_id.employee_id.company_id.id,
                                'is_lock':line_id.is_lock,
                                'number' : self.env['ir.sequence'].sudo().next_by_code('salary.slip')
                            }
                            payslips += self.env['hr.payslip'].create(res)
                        else:
                            exsit_payslip_sr.write({'is_lock':line_id.is_lock})
                            payslips += exsit_payslip_sr
                            
                    else:
                        unlink_payslip_sr = self.env['hr.payslip'].search([('employee_id','=',line_id.employee_id.id),
                                                                            ('payslip_run_id','=',active_id),
                                                                            ('date_from','=',from_date),
                                                                            ('date_to','=',to_date),
                                                                            ])
                        for unlink_payslip in unlink_payslip_sr:
                            unlink_payslip.sudo().unlink()
        for slip in payslips:
            slip.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
    
    
    
    
    
class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Payslip Batches'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('close', 'Payslip Verification'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    
    
    
    @api.multi
    def close_payslip_run(self):
        if self.slip_ids:
            for slip in self.slip_ids:
                if slip.state == 'draft':
                    slip.action_payslip_done_modification()
        return self.write({'state': 'close'})
    
    
    @api.multi
    def bulk_payslip_in_done(self):
            in_progress_branch_batch =  self.search([('state','=','in_progress')],limit=1)
            for batch_branch in in_progress_branch_batch:
                _logger.info("HR and Payroll Payslip Generation Process Start for : %s", batch_branch.name)
                batch_branch.compute_sheet()
                batch_branch.write({'state':'done'})
                _logger.info("HR and Payroll Payslip Generation Process End for : %s", batch_branch.name)
            return True
        
    
    def create_and_update_payslip_function_one(self):
        self.env.cr.execute(""" 
                                CREATE OR REPLACE FUNCTION create_payslip_lines(employeeId INTEGER, contractId INTEGER, branchId INTEGER, paySlipID INTEGER, startDate DATE, endDate DATE, min_work_hours FLOAT)
                                   RETURNS text AS $$
                                DECLARE  
                                lastPresentDate DATE;  
                                lastLeave DATE;
                                hrCalendarId INTEGER;
                                numberWeeklyOff FLOAT;
                                numberHoliday FLOAT;
                                reversableLeaveDays FLOAT;
                                
                                
                                numberDaysPresent INTEGER;
                                numberDaysPartialPresent INTEGER;
                                --numberHoursPresent FLOAT;
                                --numberHoursPartialPresent FLOAT;
                                
                                numberLeaves FLOAT;
                                workedDaysCounter INTEGER;
                                leaveEncashment   FLOAT;
                                inputCounter INTEGER;
                                advanceAmount FLOAT;
                                loanAmount FLOAT;
                                otherAloowancesAndDeductions FLOAT;
                                otherAllowancesDeductions RECORD;
                                otherAllowancesDeductions_Cursor CURSOR (from_date DATE, to_date DATE) FOR select * from other_allowance_and_deduction where date_From >= from_Date and date_to <= to_date and state='done'; 
                                otherAllowancesDeductionsLine RECORD;
                                otherAllowancesDeductionsLine_Cursor CURSOR (empId INTEGER, otherId INTEGER) FOR select * from other_allowance_and_dedution_line where employee_id = empId and other_allowance_and_deduction_id = otherId; 
                                salaryRuleCode VARCHAR;
                                salaryRuleName VARCHAR;
                                
                                
                                
                                BEGIN
SELECT
        HR_HCL.date INTO lastLeave
    FROM
        hr_holidays hr_ho,
        hr_holidays_calendar_line HR_HCL
    WHERE ((hr_ho.date_from >= startDate
            AND hr_ho.date_from <= endDate)
        OR (hr_ho.date_to >= startDate
            AND hr_ho.date_to <= endDate))
    AND employee_id = employeeId
    AND TYPE = 'remove'
    AND HR_HCL.holidays_id = HR_HO.id
    AND HR_HCL.DATE >= startDate
    AND HR_HCL.DATE <= endDate
    AND HR_HO.state = 'validate'
ORDER BY
    HR_HCL.date DESC
LIMIT 1;

                                     select attendance_date into lastPresentDate   from hr_daily_attendance_line where attendance_date  >= startDate and attendance_date <= endDate and attendance_status in ('present','partial') and employee_id = employeeId and state = 'done' order by 
                                attendance_date desc limit 1;

IF lastPresentDate IS NOT NULL AND lastLeave IS NOT NULL THEN
        lastPresentDate = GREATEST (lastPresentDate::date,
            lastLeave::date);
    ELSIF lastPresentDate IS NULL THEN
        lastPresentDate = lastLeave;
    END IF;


                                raise notice 'start Date % %', startDate,lastPresentDate;
                                IF lastPresentDate   is not null THEN
                                     select id INTO hrCalendarId from hr_calendar where branch_id = branchId and date_from = startDate and date_to = endDate order by startDate  desc  limit 1;
                                     select count(1) into numberWeeklyOff  from hr_calendar_line hrc where calendar_id = hrCalendarId and hrc.date >= startDate  and hrc.date <= lastPresentDate   and work_type ='week_off' AND HRC.DATE NOT IN (
                SELECT
                    HR_HCL.DATE
                FROM
                    hr_holidays hr_ho,
                    hr_holidays_calendar_line HR_HCL
                WHERE ((hr_ho.date_from >= startDate
                        AND hr_ho.date_from <= endDate)
                    OR (hr_ho.date_to >= startDate
                        AND hr_ho.date_to <= endDate))
                AND employee_id = employeeId
                AND TYPE = 'remove'
                AND HR_HCL.holidays_id = HR_HO.id
                AND HR_HCL.DATE >= startDate
                AND HR_HCL.DATE <= endDate
                AND HR_HO.state = 'validate');
                                     select count(1) into numberHoliday from hr_calendar_line hrc where calendar_id = hrCalendarId and hrc.date >= startDate  and hrc.date <= lastPresentDate   and work_type ='holiday' AND HRC.DATE NOT IN (
                SELECT
                    HR_HCL.DATE
                FROM
                    hr_holidays hr_ho,
                    hr_holidays_calendar_line HR_HCL
                WHERE ((hr_ho.date_from >= startDate
                        AND hr_ho.date_from <= endDate)
                    OR (hr_ho.date_to >= startDate
                        AND hr_ho.date_to <= endDate))
                AND employee_id = employeeId
                AND TYPE = 'remove'
                AND HR_HCL.holidays_id = HR_HO.id
                AND HR_HCL.DATE >= startDate
                AND HR_HCL.DATE <= endDate
                AND HR_HO.state = 'validate'); 
                                     
                                     select COALESCE(count(*),0) INTO numberDaysPresent  from hr_daily_attendance_line where employee_id = employeeId  and attendance_date >= startDate  and attendance_date  <= lastPresentDate and attendance_status = 'present' and  state = 'done' and 
                                                                             attendance_date  in  (select hrc.date from hr_calendar_line hrc where calendar_id = hrCalendarId and hrc.date >= startDate  and hrc.date <= lastPresentDate   and work_type ='work')  ;
                                     select COALESCE(count(*),0) INTO numberDaysPartialPresent  from hr_daily_attendance_line where employee_id = employeeId  and attendance_date >= startDate  and attendance_date  <= lastPresentDate and attendance_status = 'partial' and  state = 'done' and 
                                                                             attendance_date  in  (select hrc.date from hr_calendar_line hrc where calendar_id = hrCalendarId and hrc.date >= startDate  and hrc.date <= lastPresentDate   and work_type ='work')  ;
                                     
                                     RAISE NOTICE 'numberDaysPresent %', numberDaysPresent;
reversableLeaveDays  = 0;

   SELECT
            COALESCE(SUM(
                    CASE WHEN (HR_HCL.parts_of_the_day = 'full_day'
                            OR HR_HCL.parts_of_the_day = 'half_full_day')
                        AND attendance_status = 'present' THEN
                        1
                    WHEN HR_HCL.parts_of_the_day = 'half_day'
                        AND attendance_status = 'present' THEN
                        0.5
                    WHEN (HR_HCL.parts_of_the_day = 'full_day'
                            OR HR_HCL.parts_of_the_day = 'half_full_day')
                        AND attendance_status = 'partial' THEN
                        0.5
                    END), 0) INTO reversableLeaveDays
        FROM
            hr_holidays hr_ho,
            hr_holidays_calendar_line HR_HCL,
            hr_daily_attendance_line hr_at_ln
        WHERE ((hr_ho.date_from >= startDate
                AND hr_ho.date_from <= endDate)
            OR (hr_ho.date_to >= startDate
                AND hr_ho.date_to <= endDate))
        AND hr_ho.employee_id = employeeId
        AND TYPE = 'remove'
        AND HR_HCL.holidays_id = HR_HO.id
        AND HR_HCL.DATE >= startDate
        AND HR_HCL.DATE <= endDate
        AND HR_HO.state = 'validate'
        AND hr_at_ln.employee_id = employeeId
        AND hr_at_ln.state = 'done'
        AND HR_HCL.DATE = attendance_date
        AND attendance_date IN (
            SELECT
                HRC.DATE
            FROM
                hr_calendar_line hrc
            WHERE
                calendar_id = hrCalendarId
                AND HRC.DATE >= startDate
                AND HRC.DATE <= lastPresentDate
                AND work_type = 'work');

 numberDaysPresent =  numberDaysPresent - reversableLeaveDays  ;

                                     select COALESCE(sum(CASE WHEN HR_HCL.parts_of_the_day = 'half_day' THEN (min_work_hours/2) else min_work_hours END ),0) INTO numberLeaves  
                                                                from hr_holidays hr_ho, hr_holidays_calendar_line HR_HCL where 
                                    (
                                       ( 
                                             hr_ho.date_from >= startDate and hr_ho.date_from <= endDate
                                       ) or 
                                      (
                                             hr_ho.date_to >= startDate and hr_ho.date_to <= endDate
                                      )
                                    ) 
                                                                    and employee_id = employeeId and type='remove' and HR_HCL.holidays_id = HR_HO.id and  
                                                                    HR_HCL.date >= startDate and HR_HCL.date <= endDate and  HR_HO.state='validate';
                                    
                                    workedDaysCounter =0;
                                    RAISE NOTICE 'Updating weekly off % %',contractId,paySlipID;
                                    select COALESCE(count(1),0) INTO workedDaysCounter from hr_payslip_worked_days where payslip_id = paySlipID and contract_id = contractId and code = 'WF';
                                    if ( workedDaysCounter > 0 ) THEN
                                    
                                            RAISE NOTICE 'Updating weekly off';
                                            update hr_payslip_worked_days set number_of_days = numberWeeklyOff, number_of_hours = numberWeeklyOff * min_work_hours where payslip_id = paySlipID and contract_id = contractId and code = 'WF';
                                    
                                    ELSE
                                         RAISE NOTICE 'Inserting weekly off  contractId=%,%', contractId,employeeId ;
                                         insert into hr_payslip_worked_days (id, name, sequence, code, number_of_days, number_of_hours, contract_id, payslip_id, create_uid, create_date, write_uid, write_date ) values ((select COALESCE (max(id + 1 ),1) from 
                                                                     hr_payslip_worked_days ), 'Weekly Off',3, 'WF', numberWeeklyOff,  numberWeeklyOff * min_work_hours, contractId, paySlipID, 1, now(),1,now()  );
                                    END IF;
                                         
                                    workedDaysCounter =0;
                                    select COALESCE(count(1),0) INTO workedDaysCounter from hr_payslip_worked_days where payslip_id = paySlipID and contract_id = contractId and code = 'PH';
                                    if ( workedDaysCounter > 0 ) THEN
                                            update hr_payslip_worked_days set number_of_days = numberHoliday , number_of_hours = numberHoliday * min_work_hours where payslip_id = paySlipID and contract_id = contractId and code = 'PH';
                                    
                                    ELSE
                                         insert into hr_payslip_worked_days (id, name, sequence, code, number_of_days, number_of_hours, contract_id, payslip_id, create_uid, create_date, write_uid, write_date ) values ((select COALESCE (max(id + 1 ),1) from 
                                                                     hr_payslip_worked_days ), 'Public Holiday', 3, 'PH', numberHoliday ,  numberHoliday * min_work_hours, contractId, paySlipID, 1, now(),1,now()  );
                                    END IF;
                                    
                                    workedDaysCounter =0;
                                    select COALESCE(count(1),0) INTO workedDaysCounter from hr_payslip_worked_days where payslip_id = paySlipID and contract_id = contractId and code = 'Leave';
                                    if ( workedDaysCounter > 0 ) THEN
                                            update hr_payslip_worked_days set number_of_days = numberLeaves / min_work_hours, number_of_hours = numberLeaves  where payslip_id = paySlipID and contract_id = contractId and code = 'Leave';
                                    
                                    ELSE
                                         insert into hr_payslip_worked_days (id, name, sequence, code, number_of_days, number_of_hours, contract_id, payslip_id, create_uid, create_date, write_uid, write_date ) values ((select COALESCE (max(id + 1 ),1) from 
                                                                     hr_payslip_worked_days ), 'Leaves', 3, 'Leave', numberLeaves / min_work_hours ,  numberLeaves  , contractId, paySlipID, 1, now(),1,now()  );
                                    END IF;
                                    
                                    workedDaysCounter =0;
                                    select COALESCE(count(1),0) INTO workedDaysCounter from hr_payslip_worked_days where payslip_id = paySlipID and contract_id = contractId and code = 'PR';
                                    if ( workedDaysCounter > 0 ) THEN
                                            update hr_payslip_worked_days set number_of_days = numberDaysPresent , number_of_hours = numberDaysPresent * min_work_hours  where payslip_id = paySlipID and contract_id = contractId and code = 'PR';
                                    
                                    ELSE
                                          insert into hr_payslip_worked_days (id, name, sequence, code, number_of_days, number_of_hours, contract_id, payslip_id, create_uid, create_date, write_uid, write_date ) values ((select COALESCE (max(id + 1 ),1) from 
                                                                     hr_payslip_worked_days ), 'Present', 3, 'PR', numberDaysPresent,  numberDaysPresent * min_work_hours  , contractId, paySlipID, 1, now(),1,now()  );
                                    END IF;
                                    
                                    
                                    workedDaysCounter =0;
                                    select COALESCE(count(1),0) INTO workedDaysCounter from hr_payslip_worked_days where payslip_id = paySlipID and contract_id = contractId and code = 'PPR';
                                    if ( workedDaysCounter > 0 ) THEN
                                            update hr_payslip_worked_days set number_of_days = numberDaysPartialPresent / 2 , number_of_hours = numberDaysPartialPresent * (min_work_hours/2)  where payslip_id = paySlipID and contract_id = contractId and code = 'PPR';
                                    
                                    ELSE
                                          insert into hr_payslip_worked_days (id, name, sequence, code, number_of_days, number_of_hours, contract_id, payslip_id, create_uid, create_date, write_uid, write_date ) values ((select COALESCE (max(id + 1 ),1) from 
                                                                     hr_payslip_worked_days ), 'Partial Present', 3, 'PPR', numberDaysPartialPresent / 2,  numberDaysPartialPresent * (min_work_hours/2)  , contractId, paySlipID, 1, now(),1,now()  );
                                    END IF;
                                
                                END IF;
                                
                                select encashment_amount INTO leaveEncashment  from leave_encashment_request where employee_id = employeeId and requested_date >= startDate and requested_date <= endDate and state='approved' and type='encashment';
                                
                                inputCounter =0;
                                select COALESCE(count(1),0) INTO inputCounter from hr_payslip_input where payslip_id = paySlipID and contract_id = contractId and code = 'LE';
                                if ( inputCounter > 0 ) THEN
                                        update hr_payslip_input set amount= leaveEncashment  where payslip_id = paySlipID and contract_id = contractId and code = 'LE';
                                
                                ELSE
                                      insert into hr_payslip_input (id, name, sequence, code, amount, contract_id, payslip_id, create_uid, create_date, write_uid, write_date ) values ((select COALESCE (max(id + 1 ),1) from 
                                                                 hr_payslip_input ), 'Leave Encashment', 10, 'LE', leaveEncashment, contractId, paySlipID, 1, now(),1,now()  );
                                END IF;
                                
                                select amount INTO loanAmount  from hr_loan_line where employee_id = employeeId and date >= startDate and date <= endDate and paid!=True;
                                
                                inputCounter =0;
                                select COALESCE(count(1),0) INTO inputCounter from hr_payslip_input where payslip_id = paySlipID and contract_id = contractId and code = 'LOAN';
                                if ( inputCounter > 0 ) THEN
                                        update hr_payslip_input set amount= loanAmount  where payslip_id = paySlipID and contract_id = contractId and code = 'LOAN';
                                
                                ELSE
                                      insert into hr_payslip_input (id, name, sequence, code, amount, contract_id, payslip_id, create_uid, create_date, write_uid, write_date ) values ((select COALESCE (max(id + 1 ),1) from 
                                                                 hr_payslip_input ), 'Loan Recovery', 10, 'LE', loanAmount, contractId, paySlipID, 1, now(),1,now()  );
                                END IF;
                                ---------------------
                                
                                select requested_amount INTO advanceAmount from hr_advance where employee_id = employeeId and date >= startDate and date <= endDate and state='approve';
                                
                                inputCounter =0;
                                select COALESCE(count(1),0) INTO inputCounter from hr_payslip_input where payslip_id = paySlipID and contract_id = contractId and code = 'ADV';
                                if ( inputCounter > 0 ) THEN
                                        update hr_payslip_input set amount= advanceAmount where payslip_id = paySlipID and contract_id = contractId and code = 'ADV';
                                
                                ELSE
                                      insert into hr_payslip_input (id, name, sequence, code, amount, contract_id, payslip_id, create_uid, create_date, write_uid, write_date ) values ((select COALESCE (max(id + 1 ),1) from 
                                                                 hr_payslip_input ), 'Salary Advance', 10, 'ADV', advanceAmount , contractId, paySlipID, 1, now(),1,now()  );
                                END IF;
                                
                                    OPEN otherAllowancesDeductions_Cursor (startDate, endDate);
                                           LOOP   
                                                FETCH otherAllowancesDeductions_Cursor INTO otherAllowancesDeductions ; 
                                                EXIT WHEN NOT FOUND;
                                                
                                                OPEN otherAllowancesDeductionsLine_Cursor (employeeId , otherAllowancesDeductions.id);
                                                     LOOP   
                                                         FETCH otherAllowancesDeductionsLine_Cursor INTO otherAllowancesDeductionsLine ; 
                                                         EXIT WHEN NOT FOUND;
                                                          inputCounter =0;
                                
                                
                                select code INTO salaryRuleCode from hr_salary_rule where id =  otherAllowancesDeductions.salary_rule_id;
                                select name INTO salaryRuleName    from hr_salary_rule where id =  otherAllowancesDeductions.salary_rule_id;
                                
                                select COALESCE(count(1),0) INTO inputCounter from hr_payslip_input where payslip_id = paySlipID and contract_id = contractId and code = salaryRuleCode;
                                if ( inputCounter > 0 ) THEN
                                        update hr_payslip_input set amount= otherAllowancesDeductionsLine.amount where payslip_id = paySlipID and contract_id = contractId and code = salaryRuleCode;
                                
                                ELSE
                                      insert into hr_payslip_input (id, name, sequence, code, amount, contract_id, payslip_id, create_uid, create_date, write_uid, write_date ) values ((select COALESCE (max(id + 1 ),1) from 
                                                                 hr_payslip_input ), salaryRuleName, 10, salaryRuleCode, otherAllowancesDeductionsLine.amount , contractId, paySlipID, 1, now(),1,now()  );
                                END IF;  
                                                          
                                                          
                                
                                                         
                                
                                                     END LOOP;
                                                CLOSE otherAllowancesDeductionsLine_Cursor ;  
                                
                                                      
                                           
                                
                                           END LOOP;
                                    CLOSE otherAllowancesDeductions_Cursor ;
                                     
                                
                                
                                    PERFORM setval('hr_payslip_input_id_seq', COALESCE((SELECT MAX(id)+1 FROM hr_payslip_input), 1), false);
                                    PERFORM setval('hr_payslip_worked_days_id_seq', COALESCE((SELECT MAX(id)+1 FROM hr_payslip_worked_days), 1), false);
                                    
                                   RETURN 0;
                                END;    $$
                                LANGUAGE plpgsql;
                            """)
        
        
    
    def create_and_update_payslip_function_two(self):
        self.env.cr.execute("""
                               CREATE OR REPLACE FUNCTION create_payslip(startdate DATE, endDate DATE,branch_id INTEGER,employee_id INTEGER)
                               RETURNS text AS $$
                                DECLARE  
                                  cur_branch RECORD;
                                  cur_employee RECORD;
                                  empl_payslip_Count INTEGER;
                                  already_empl_payslip_Count INTEGER;
                                  empl_payslip_Id INTEGER;
                                  emp_payslip_ref_num INTEGER; 
                                  emp_payslip_prefix TEXT;
                                  emp_payslip_padding INTEGER;  
                                  empContractId INTEGER;
                                  Minwork_hours FLOAT;
                                  --Branch_id INTEGER;
                                  --Employee_id INTEGER;
                                  
                                  branch_cursor CURSOR  FOR select id from operating_unit where type = 'branch';-- and id= 12970 ; --12970 amalapuram
                                  branch_cursor1 CURSOR (Branch_id INTEGER) FOR select id from operating_unit where type = 'branch' and id=Branch_id;
                                  employee_cursor CURSOR (Branchid INTEGER) FOR select * from hr_employee he where he.branch_id =  Branchid;
                                  employee_cursor1 CURSOR (Branchid INTEGER,employee_id INTEGER) FOR select * from hr_employee he where he.branch_id =  Branchid and he.id=Employee_id;
                                
                                BEGIN
                                    select prefix into emp_payslip_prefix from ir_sequence where code = 'salary.slip';
                                    select number_next into emp_payslip_ref_num   from ir_sequence where code = 'salary.slip';
                                    select padding  into emp_payslip_padding from ir_sequence where code = 'salary.slip';
                                       -- Open the branch cursor
                                   
                                   
                                   IF branch_id > 0 THEN
                                        OPEN branch_cursor1(Branch_id) ;
                                    ELSE
                                        OPEN branch_cursor ;
                                    END IF; 
                                    
                                   LOOP
                                        IF branch_id > 0 THEN
                                           FETCH branch_cursor1 INTO cur_branch ;
                                        ELSE
                                            FETCH branch_cursor INTO cur_branch ;
                                        END IF;
                                        
                                        -- exit when no more row to fetch
                                       EXIT WHEN NOT FOUND;
                                       
                                        IF employee_id > 0 THEN
                                            OPEN employee_cursor1 (cur_branch.id,Employee_id);
                                        ELSE
                                            OPEN employee_cursor (cur_branch.id);
                                        END IF;
                                       
                                           LOOP
                                           empl_payslip_Count = 0;
                                           
                                            IF employee_id > 0 THEN
                                               FETCH employee_cursor1  INTO cur_employee ;
                                            ELSE
                                                FETCH employee_cursor  INTO cur_employee ;
                                            END IF;
                                           
                                           
                                           
                                           EXIT WHEN NOT FOUND;
                                           select count(1) into  empl_payslip_Count from hr_payslip hp where hp.employee_id = cur_employee .id and hp.date_from =  startDate and hp.date_to = endDate; --and hp.branch_id = cur_branch.id;
                                           select id INTO empContractId from hr_contract hc where hc.employee_id = cur_employee.ID;
                                            IF  empl_payslip_Count > 0 THEN
                                                  select id  INTO empl_payslip_Id from hr_payslip hp where hp.employee_id = cur_employee .id and hp.date_from =  startDate and hp.date_to = endDate;-- and hp.branch_id = cur_branch.id;
                                            ELSE
                                                  select COALESCE (max(id + 1 ),1) INTO empl_payslip_Id from hr_payslip ;
                                                  
                                                  insert into hr_payslip(id, struct_id, name,number,
                                                                          employee_id,date_from,date_to,state,company_id,paid,note,
                                                                          contract_id, credit_note, payslip_run_id, create_uid,
                                                                          create_date, write_uid, write_date, date, journal_id, move_id,
                                                                          branch_id,is_lock, is_sublock, exist_slip, employee_lock_sublock,
                                                                          partial_move_id, partial_date, payslip_bank_id)
                                                   values 
                                                                          ( empl_payslip_Id , cur_employee.struct_id, 'Pay Slip of - ' || cur_employee.name || ' - ' || to_char(endDate,'month - YYYY'), emp_payslip_prefix || LPAD(emp_payslip_ref_num::text,emp_payslip_padding,'0'),
                                                                            cur_employee.ID,startDate, endDate,'draft',1,FALSE,null,
                                                                            empContractId ,FALSE,(select id from hr_payslip_run hpr where hpr.branch_id = cur_employee.branch_id and hpr.date_start = startDate and hpr.date_end = endDate order by id desc LIMIT 1), 1,
                                                                            now(),1, now(),null, (select id from account_journal aj where aj.name ='Miscellaneous Operations'), null,
                                                                            cur_employee.branch_id, FALSE,FALSE,FALSE,null,
                                                                            null,null,null
                                
                                                      );
                                                  emp_payslip_ref_num = emp_payslip_ref_num + 1;
                                                  raise notice 'emp_payslip_ref_num %',emp_payslip_ref_num;
                                            END IF;
                                            raise notice 'Inserting weekly off aaaaaaaaaaaaa %',(select count(*) from hr_payslip hp where hp.id=empl_payslip_Id and hp.state='draft');
                                                IF COALESCE((select count(*) from hr_payslip hp where hp.id=empl_payslip_Id and hp.state='draft'), 0) > 0 THEN
                                                    raise notice 'payslip LINE START %',(empl_payslip_Id);
                                                    select COALESCE(min_work_hours,'0') into Minwork_hours from branch_officetype_workhours_line bowl where bowl.branch_id = cur_employee.branch_id and bowl.status_type = 'present' limit 1;
                                                    PERFORM create_payslip_lines(cur_employee.id , empContractId , cur_employee.branch_id, empl_payslip_Id , startDate , endDate, Minwork_hours);
                                                END IF;
                                           END LOOP;  
                                       --close the employee cursor.
                                       --CLOSE employee_cursor ;
                                       IF employee_id > 0 THEN
                                            CLOSE employee_cursor1;
                                        ELSE
                                            CLOSE employee_cursor;
                                        END IF;
                                
                                   END LOOP;
                                  
                                   -- Close the cursor
                                   --CLOSE branch_cursor ;
                                   IF branch_id > 0 THEN
                                       CLOSE branch_cursor1;
                                   ELSE
                                       CLOSE branch_cursor;
                                   END IF;
                                 update ir_sequence set number_next = emp_payslip_ref_num where code = 'salary.slip';
                                 PERFORM setval('hr_payslip_id_seq', COALESCE((SELECT MAX(id)+1 FROM hr_payslip), 1), false);
                                   RETURN 0;
                                END; $$
                                LANGUAGE plpgsql;  
                            """)
    
    
    def current_month_create_and_update_payslip_one(self,start_date,end_date,branch_id,employee_id):
#         if start_date and end_date and branch_id and employee_id:
#             self.env.cr.execute("""select create_payslip(%s,%s,%S,%S);""",(str(month_start_date),str(month_end_date),branch_id,employee_id))
#         else:
        print (start_date,end_date,branch_id,employee_id,"wwwwwwwwwwwwwwwwwww")
        today               = datetime.now().date()
        month_start_date    = today.replace(day=1)
        month_end_date      = month_start_date + relativedelta(months=+1, day=1, days=-1)
        print (month_start_date,month_end_date,"month_start_date , month_end_date")
        self.env.cr.execute("""select create_payslip(%s,%s,%s,%s);""",(start_date if start_date else str(month_start_date),
                                                                 end_date if end_date else str(month_end_date), 
                                                                 branch_id if branch_id else 0,
                                                                 employee_id if employee_id else 0
                                                                 ))
    
    
    
    def current_month_create_and_update_payslip_lines_two(self,start_date,end_date,branch_id):
        today               = datetime.now().date()
        month_start_date    = today.replace(day=1)
        month_end_date      = month_start_date + relativedelta(months=+1, day=1, days=-1)
        
        date_from           = month_start_date
        date_to             = month_end_date
        
        hr_batch_ids = []
        if start_date and end_date:
            date_from           = start_date
            date_to             = end_date
        if branch_id:
            hr_batch_ids = self.env['hr.payslip.run'].search([('date_start','=',date_from),('date_end','=',date_to),('branch_id','=',branch_id)])
        else:
            hr_batch_ids = self.env['hr.payslip.run'].search([('date_start','=',date_from),('date_end','=',date_to)])
        hr_payslip_ids = self.env['hr.payslip'].search([('payslip_run_id','in',hr_batch_ids.ids),('state','=','draft')],order = "payslip_run_id")
        for slip in hr_payslip_ids:
            slip.cron_compute_sheet()
        return True
            
        
            
    @api.multi       
    def current_month_create_and_update_payslip_sechedule_function(self,start_date,end_date,branch_id,employee_id):
        self.current_month_create_and_update_payslip_one(start_date,end_date,branch_id,employee_id)
        return True
    
    @api.multi
    def compute_sheet(self):
        print ("222222222333333333333333333333333333333333333333333333333")
        payslips = self.env['hr.payslip']
        from_date   = self.date_start
        to_date     = self.date_end
        branch_id   = self.branch_id
        # Name 
        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(to_date, "%Y-%m-%d")))
        locale = self.env.context.get('lang') or 'en_US'
        employee_lock_sublock_sr = self.env['employee.lock.sublock'].search([('branch_id','=', branch_id.id),
                                                                             ('payslip_batch_id','=',self.id),
                                                                             ('lock_state','=','approved'),('sublock_state','=','approved'),
                                                                             '|',('is_active','=',True),('is_active','=',False)])
        if not employee_lock_sublock_sr:
            raise UserError(_("You must create or approve Lock/Sublock."))
        for lock_sublock in employee_lock_sublock_sr:
            for line_id in lock_sublock.lock_sublock_line:
                if line_id.employee_id.id != 1 and line_id.employee_id.date_of_joining <= to_date \
                        and line_id.employee_id.contract_id and line_id.employee_id.contract_id.struct_id:
                    
                    exsit_payslip_sr = self.env['hr.payslip'].search([('employee_id','=',line_id.employee_id.id),
                                                                        ('date_from','=',from_date),
                                                                        ('date_to','=',to_date),
                                                                        ])
                    if not exsit_payslip_sr:
                        slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, line_id.employee_id.id, contract_id=False)
                        res = {
                            'employee_id': line_id.employee_id.id,
                            'name': _('Salary Slip of %s for %s') % (line_id.employee_id.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),
                            'struct_id': line_id.employee_id.struct_id.id,
                            'payslip_run_id': self.id,
                            'contract_id': line_id.employee_id.contract_id.id,
                            'date_from': from_date,
                            'date_to': to_date,
                            'credit_note': self.credit_note,
                            'company_id': line_id.employee_id.company_id.id,
                            'branch_id': line_id.employee_id.branch_id.id,
                            'is_lock':line_id.is_lock,
                            'is_sublock':line_id.is_sublock,
                            'employee_lock_sublock':line_id.id,
                            'number' : self.env['ir.sequence'].sudo().next_by_code('salary.slip')
                        }
                        new_slip = self.env['hr.payslip'].create(res)
                        line_id.slip_id = new_slip.id
                        payslips += new_slip
                         
                    else:
                        exsit_payslip_sr.write({'is_lock':line_id.is_lock,'is_sublock':line_id.is_sublock})
                            
                            # Temp comments
                        payslips += exsit_payslip_sr
#                     else:
#                         unlink_payslip_sr = self.env['hr.payslip'].search([('employee_id','=',line_id.employee_id.id),
#                                                                             ('payslip_run_id','=',self.id),
#                                                                             ('date_from','=',from_date),
#                                                                             ('date_to','=',to_date),('state','=','draft')
#                                                                             ])
#                         for unlink_payslip in unlink_payslip_sr:
#                             unlink_payslip.sudo().unlink()
        count = 1
        total_count = len(payslips.ids)
        for slip in payslips:
            if slip.state == 'draft':
                slip.compute_sheet()
                _logger.info("HR and Payroll Payslip Generation completed  :  %s, %s, %s, %s/%s", slip.id,slip.employee_id.name,slip.employee_id.emp_id,str(count),str(total_count))
                count += 1
    
    
    
    @api.multi
    def get_is_sublock_created(self):
        for record in self:
            if record.branch_id and record.id:
                employee_lock_sublock_sr = self.env['employee.lock.sublock'].search([('branch_id', '=', record.branch_id.id), ('payslip_batch_id', '=', record.id)])
                print (employee_lock_sublock_sr,'11111')
                if employee_lock_sublock_sr:
                    record.is_sublock_created = True


    # def _get_payslip_counts(self):
    #     for record in self:
    #         if record.slip_ids.ids != []:
    #             record.payslips_count = len(record.slip_ids)
    #         else:
    #             record.payslips_count = 0
    
    company_id = fields.Many2one('res.company',string='Organization')
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    # payslips_countF = fields.Integer('Total Payslips', compute='_get_payslip_counts')
    is_sublock_created = fields.Boolean('Is Lock/Sublock Created?', compute='get_is_sublock_created')

#     @api.constrains('date_start', 'date_end')
#     def check_date_from(self):
#         for record in self:
#             date_start = dateutil.parser.parse(record.date_start).date()
#             if date_start > datetime.today().date():
#                 raise ValidationError("Start Date must be less than or equal to Current Date")
#             date_end = dateutil.parser.parse(record.date_end).date()
#             if date_end > datetime.today().date():
#                 raise ValidationError("End Date must be less than or equal to Current Date")
    
    
    
class HrPayslipAttendanceDays(models.Model):
    _name = 'hr.payslip.attendance_days'
    _description = 'Payslip Attendance Days'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Description', required=True,size=40)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(required=True, index=True, default=10)
    code = fields.Char(required=True,size=50, help="The code that can be used in the salary rules")
    number_of_days = fields.Float(string='Number of Days')
    number_of_hours = fields.Float(string='Number of Hours')
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True,
        help="The contract for which applied this input") 

class HRSalaryRuleInherit(models.Model):
    _inherit = 'hr.salary.rule'
    
    is_statutory = fields.Boolean(string='Is statutory compliance?')
    name = fields.Char(required=True, translate=True,size=50)
    code = fields.Char(required=True,
                       help="The code of salary rules can be used as reference in computation of other rules. "
                            "In that case, it is case sensitive.",size=10)
    sequence = fields.Integer(required=True, index=True, default=5,
                              help='Use to arrange calculation sequence')
    quantity = fields.Char(default='1.0',
                           help="It is used in computation for percentage and fixed amount. "
                                "For e.g. A rule for Meal Voucher having fixed amount of "
                                u"1€ per worked day can have its quantity defined in expression "
                                "like worked_days.WORK100.number_of_days.",size=10)
    amount_fix = fields.Float(string='Fixed Amount', digits=dp.get_precision('Payroll'))

    @api.constrains('sequence')
    def check_sequence(self):
        for record in self:
            if record.sequence and record.sequence < 0:
                raise ValidationError("Sequence should not be Negative (-ve)")
            if record.sequence == 0:
                raise ValidationError("Sequence should not be Zero '0' ")
            # rule = record.env['hr.salary.rule'].search([('sequence','=',record.sequence)])
            # if len(rule) > 1:
            #     raise ValidationError("Sequence already exists")

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'
    
    account_move = fields.Boolean(string='Account Move')
    
    
    
class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'
    
    company_id = fields.Many2one('res.company', string='Organization', required=True,
        copy=False, default=lambda self: self.env['res.company']._company_default_get())
    name = fields.Char(required=True,size=30)
    
    
class HrContributionRegister(models.Model):
    _inherit = 'hr.contribution.register'
    
    company_id = fields.Many2one('res.company', string='Organization',default=lambda self: self.env['res.company']._company_default_get())
    
class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'
    
    company_id = fields.Many2one('res.company', string='Organization',default=lambda self: self.env['res.company']._company_default_get())
    
class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    company_id = fields.Many2one('res.company', string='Organization',default=lambda self: self.env['res.company']._company_default_get())
