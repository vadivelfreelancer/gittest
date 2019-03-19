from odoo import api, fields, models, tools
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import babel
import threading

    
class EmployeeLockSublock(models.Model):
    _name = 'employee.lock.sublock'
    _inherit = 'mail.thread'
    _order = "lock_state desc"

    @api.depends('payslip_batch_id')
    def _get_active_status(self):
        for record in self:
            last_month = (datetime.now() + relativedelta(months=-1, day=1)).strftime("%Y-%m-%d")
            if record.payslip_batch_id:
                if record.payslip_batch_id.date_start >= last_month:
                    record.is_active = True
            else:
                record.is_active = False

    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    name = fields.Char(string='Name',size=100)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    payslip_batch_id = fields.Many2one('hr.payslip.run', string='Payslip Batch')
    lock_sublock_line = fields.One2many('employee.lock.sublock.line', 'lock_id', string='Lock Sublock Line')
    lock_state = fields.Selection([('draft', 'Draft'),('requested', 'Requested'),('approved', 'Approved')], default='draft',string='Lock Status')
    sublock_state = fields.Selection([('draft', 'Draft'),('requested', 'Requested'),('approved', 'Approved')], default='draft',string='Sublock Status')
    is_active = fields.Boolean('Active', compute='_get_active_status', store=True)
    date_start = fields.Date(string='Date From')
    date_end = fields.Date(string='Date To')
    month_id = fields.Many2one('calendar.generation.line',string='Month')

    @api.multi
    def lock_sublock_update(self):
        for record in self:
            if record.branch_id and record.date_start and record.date_end:
                already_employee_list = []
                for line in record.lock_sublock_line:
                    already_employee_list.append(line.employee_id.id)
                
                
                employee_val = self.env['hr.employee'].search([('branch_id','=',record.branch_id.id),('date_of_joining','<=',record.date_end)])
                employee_exit = self.env['hr.exit'].search([('state','not in',['cancel','reject']),('employee_id','in',employee_val.ids)])
                employee_exit = already_employee_list + employee_exit.ids
                employees_list = []
                for employee in self.env['hr.employee'].search([('id','in',employee_val.ids),('id','not in',employee_exit)]):
                     employees_list.append((0,0,{
                         'employee_id'      : employee.id,
                         'emp_id'           : employee.emp_id,
                         'date_of_joining'  : employee.date_of_joining,
                         'is_lock'          : True,
                         'is_sublock'       : True,
                         'lock_state'       : 'draft',
                         'sublock_state'    : 'draft',
                     }))
                record.sudo().lock_sublock_line = employees_list
            
    
    
    @api.onchange('month_id')
    def onchange_month_id(self):
        for record in self:
            if record.month_id:
                record.date_start   = record.month_id.date_start
                record.date_end     = record.month_id.date_end
                record.onchange_name()
    
    @api.model
    def create(self, vals):
        print (vals,"11111111111111111111")
        res = super(EmployeeLockSublock, self).create(vals)
        print (res,res.name,res.date_start,res.date_end,res.branch_id.id,"rrrrrrrrrrrrrrrrrr")
        payslip_batch = self.env['hr.payslip.run'].create({
                                            'name'          : res.name,
                                            'date_start'    : res.date_start,
                                            'date_end'      : res.date_end,
                                            'branch_id'     : res.branch_id.id
                                            })
        res['payslip_batch_id'] = payslip_batch.id
        return res
    
    @api.multi
    def write(self, vals):
        res = super(EmployeeLockSublock, self).write(vals)
        return res
    
    @api.onchange('branch_id','date_end')
    def onchange_name(self):
        for record in self:
            name = ''
            if record.branch_id.name:
                name += record.branch_id.name
            if record.date_end and record.branch_id:
                ttyme = datetime.fromtimestamp(time.mktime(time.strptime(record.date_end, "%Y-%m-%d")))
                locale = self.env.context.get('lang') or 'en_US'
                name += ' - ' + tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))
            record.name = name
    
    @api.multi
    def lock_button_request(self):
        for record in self:
            monthly_calender = self.env['hr.calendar'].search([('branch_id','=',record.branch_id.id),
                                                               ('date_from','=',record.date_start),
                                                               ('date_to','=',record.date_end),
                                                               ('state','!=','approve')
                                                               ])
            if monthly_calender:
                raise ValidationError('Please Approve calendar for the selected Branch')
            record.lock_sublock_line.search([('is_lock','=',True),('lock_state','=','draft')]).sudo().write({'lock_state':'requested'})
            record.sudo().lock_state = 'requested'
                
    @api.multi
    def lock_button_approve(self):
        for record in self:
            record.lock_sublock_line.search([('is_lock','=',True),('lock_state','=','requested')]).sudo().write({'lock_state':'approved'})
            record.sudo().lock_state = 'approved'
            if record.lock_state == 'approved' and record.sublock_state == 'approved':
                record.payslip_batch_id.sudo().write({'state':'confirm'})

    @api.multi
    def lock_button_reset(self):
        for record in self:
            record.lock_sublock_line.search([('slip_id','=',False),('lock_state','=','approved')]).sudo().write({'lock_state':'draft'})
            record.sudo().lock_state = 'draft'
            
    @api.multi
    def sublock_button_request(self):
        for record in self:
            monthly_calender = self.env['hr.calendar'].search([('branch_id','=',record.branch_id.id),
                                                               ('date_from','=',record.date_start),
                                                               ('date_to','=',record.date_end),
                                                               ('state','!=','approve')
                                                               ])
            if monthly_calender:
                raise ValidationError(_('Please Approve calendar for the selected Branch'))
            for line in record.lock_sublock_line:
                if line.is_lock or line.is_sublock:
                    line.sudo().sublock_state = 'requested'
            record.sudo().sublock_state = 'requested'
                
    @api.multi
    def sublock_button_approve(self):
        for record in self:
            for line in record.lock_sublock_line:
                if line.is_lock or line.is_sublock:
                    line.sublock_state = 'approved'
            record.sudo().sublock_state = 'approved'
            if record.lock_state == 'approved' and record.sublock_state == 'approved':
                record.payslip_batch_id.sudo().write({'state':'confirm'})
            
            
    @api.multi
    def sublock_button_reset(self):
        for record in self:
            record.lock_sublock_line.search([('account_entry','=',False),('sublock_state','=','approved')]).sudo().write({'sublock_state':'draft'})
            record.sudo().sublock_state = 'draft'
                    

    @api.onchange('branch_id','date_start','date_end')
    def onchange_branch_id(self):
        for record in self:
            record.lock_sublock_line = None
            if record.branch_id and record.date_start and record.date_end:
                employee_val = self.env['hr.employee'].search([('branch_id','=',record.branch_id.id),('date_of_joining','<=',record.date_end)])
                employee_exit = self.env['hr.exit'].search([('state','not in',['cancel','reject']),('employee_id','in',employee_val.ids)])
                employees_list = []
                for employee in self.env['hr.employee'].search([('id','in',employee_val.ids),('id','not in',employee_exit.ids)]):
                     employees_list.append((0,0,{
                         'employee_id'      : employee.id,
                         'emp_id'           : employee.emp_id,
                         'date_of_joining'  : employee.date_of_joining,
                         'is_lock'          : True,
                         'is_sublock'       : True,
                         'lock_state'       : 'draft',
                         'sublock_state'    : 'draft',
                     }))
                record.sudo().lock_sublock_line = employees_list

    @api.multi
    def execute_lock_and_sublock_create_thread_function(self):
        self.execute_create_lock_and_sublock_function_query()
        return True
    
    
    @api.multi
    def execute_create_lock_and_sublock_manually(self,start_date,end_date,branch_id):
        if start_date and end_date:
            month_start_date    = start_date
            month_end_date      = end_date
            calendar_generation_line_id = self.env['calendar.generation.line'].search([('date_start','=',month_start_date),('date_end','=',month_end_date)])
            if calendar_generation_line_id:
                employee_lock_sublock = self.env['employee.lock.sublock'].search([('date_start','=',calendar_generation_line_id.date_start),('date_end','=',calendar_generation_line_id.date_end)])
                already_branch_ids = [] 
                for already_branch in employee_lock_sublock:
                    already_branch_ids.append(already_branch.branch_id.id)
                all_branch_ids = []
                if branch_id:
                    all_branch_ids =  self.env['operating.unit'].search([('type','=','branch'),('id','not in',already_branch_ids),('id','=',branch_id)])
                else:
                    all_branch_ids =  self.env['operating.unit'].search([('type','=','branch'),('id','not in',already_branch_ids)])
                for branch in all_branch_ids:
                    name = ''
                    if branch.name:
                        name += branch.name
                    if calendar_generation_line_id.date_end:
                        ttyme   = datetime.fromtimestamp(time.mktime(time.strptime(calendar_generation_line_id.date_end, "%Y-%m-%d")))
                        locale  = self.env.context.get('lang') or 'en_US'
                        name    += ' - ' + tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))
                    new_branch  = self.env['employee.lock.sublock'].create({'month_id':calendar_generation_line_id.id,
                                                                            'branch_id': branch.id,
                                                                            'date_start':calendar_generation_line_id.date_start,
                                                                            'date_end':calendar_generation_line_id.date_end,
                                                                            'name':name,
                                                                            'lock_state'       : 'draft',
                                                                            'sublock_state'    : 'draft',
                                                                            
                                                                            })
                    new_branch.onchange_branch_id()
                print ("Manually lock and sub lock created")
        
    @api.multi
    def execute_create_lock_and_sublock_function_query(self):
        today               = datetime.now().date()
        month_start_date    = today.replace(day=1)
        month_end_date      = month_start_date + relativedelta(months=+1, day=1, days=-1)
        calendar_generation_line_id = self.env['calendar.generation.line'].search([('date_start','=',month_start_date),('date_end','=',month_end_date)])
        if calendar_generation_line_id:
            employee_lock_sublock = self.env['employee.lock.sublock'].search([('date_start','=',calendar_generation_line_id.date_start),('date_end','=',calendar_generation_line_id.date_end)])
            already_branch_ids = [] 
            for already_branch in employee_lock_sublock:
                already_branch_ids.append(already_branch.branch_id.id)
            all_branch_ids =  self.env['operating.unit'].search([('type','=','branch'),('id','not in',already_branch_ids)])
            for branch in all_branch_ids:
                name = ''
                if branch.name:
                    name += branch.name
                if calendar_generation_line_id.date_end:
                    ttyme   = datetime.fromtimestamp(time.mktime(time.strptime(calendar_generation_line_id.date_end, "%Y-%m-%d")))
                    locale  = self.env.context.get('lang') or 'en_US'
                    name    += ' - ' + tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))
                new_branch  = self.env['employee.lock.sublock'].create({'month_id':calendar_generation_line_id.id,
                                                                        'branch_id': branch.id,
                                                                        'date_start':calendar_generation_line_id.date_start,
                                                                        'date_end':calendar_generation_line_id.date_end,
                                                                        'name':name,
                                                                        'lock_state'       : 'draft',
                                                                        'sublock_state'    : 'draft',
                                                                        })
                new_branch.onchange_branch_id()
            
            

class EmployeeLockSublockLine(models.Model):
    _name = 'employee.lock.sublock.line'

    lock_id = fields.Many2one('employee.lock.sublock', string='Lock ID', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    emp_id = fields.Char('Employee ID',size=10)
    date_of_joining = fields.Date('Date of Joining')
    is_lock = fields.Boolean('Process Salary', default=True)
    is_sublock = fields.Boolean('Release Payment', default=True)
    slip_id = fields.Many2one('hr.payslip')
    slip_number = fields.Char(related='slip_id.number',string='Payslip') 
    partial_account_entry = fields.Many2one('account.move')
    account_entry = fields.Many2one('account.move')
    
    lock_state = fields.Selection([('draft', 'Draft'),('requested', 'Requested'),('approved', 'Approved')], default='draft',string='Status')
    sublock_state = fields.Selection([('draft', 'Draft'),('requested', 'Requested'),('approved', 'Approved')], default='draft',string='Status')

    remarks = fields.Char('Remarks', size=50)
    is_remarks_required = fields.Boolean('Is Remarks Required?')
    lock_remarks_line = fields.One2many('employee.lock.remarks.line', 'lock_sublock_id', string='Lock Remarks Line', ondelete='cascade')
    sublock_remarks_line = fields.One2many('employee.sublock.remarks.line', 'lock_sublock_id', string='Sublock Remarks Line', ondelete='cascade')
    is_remarks_generated = fields.Boolean('Is Remarks Generated', compute='get_remarks_status')

    def get_remarks_status(self):
        for record in self:
            if record.lock_remarks_line.ids or record.sublock_remarks_line.ids != []:
                record.is_remarks_generated = True
            else:
                record.is_remarks_generated = False

    
#     @api.onchange('is_lock','is_sublock')
#     def onchange_lock_sublock(self):
#         for record in self:
#             if not record.is_lock:
#                 record.is_sublock = True
#             elif not record.is_sublock:
#                 record.is_lock = True
# 
#     @api.constrains('is_lock','is_sublock')
#     def validate_of_is_lock(self):
#         for record in self:
#             if not record.is_lock and not record.is_sublock:
#                 raise ValidationError("You can't choose Both Lock and Sublock for an Employee.")

    @api.onchange('is_lock','is_sublock')
    def onchange_is_lock(self):
        for record in self:
            record.is_remarks_required = True
            record.remarks = None

    @api.model
    def create(self, vals):
        res = super(EmployeeLockSublockLine, self).create(vals)
        if not res.is_lock:
            res.write(vals)
        return res

    @api.multi
    def write(self, vals):
        if 'remarks' in vals and 'is_lock' in vals:
            remarks_line = self.env['employee.lock.remarks.line']
            remarks_line.create({
                'lock_sublock_id': self.id,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'generated_by': self.env.user.id,
                'remarks': vals['remarks'],
                'process_salary': vals['is_lock'],
            })
            # vals['remarks'] = None
            vals['is_remarks_required'] = False
        if 'remarks' in vals and 'is_sublock' in vals:
            remarks_line = self.env['employee.sublock.remarks.line']
            remarks_line.create({
                'lock_sublock_id': self.id,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'generated_by': self.env.user.id,
                'remarks': vals['remarks'],
                'release_payment': vals['is_sublock'],
            })
            # vals['remarks'] = None
            vals['is_remarks_required'] = False
        return super(EmployeeLockSublockLine, self).write(vals)


    def open_lock_remarks(self):
        for record in self:
            return {
                'name': 'Remarks for Lock',
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'employee.lock.remarks.line',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': [('lock_sublock_id', '=', record.id)],
                # 'target': 'current',
            }

    def open_sublock_remarks(self):
        for record in self:
            return {
                'name': 'Remarks for Sublock',
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'employee.sublock.remarks.line',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': [('lock_sublock_id', '=', record.id)]
            }


class EmployeeLockRemarksLine(models.Model):
    _name = 'employee.lock.remarks.line'

    lock_sublock_id = fields.Many2one('employee.lock.sublock.line', string='Lock ID', ondelete='cascade')
    date = fields.Datetime('Date')
    generated_by = fields.Many2one('res.users', string='Generated By')
    remarks = fields.Char('Remarks', size=50)
    process_salary = fields.Boolean('Process Salary')


class EmployeeSublockRemarksLine(models.Model):
    _name = 'employee.sublock.remarks.line'

    lock_sublock_id = fields.Many2one('employee.lock.sublock.line', string='Lock ID', ondelete='cascade')
    date = fields.Datetime('Date')
    generated_by = fields.Many2one('res.users', string='Generated By')
    remarks = fields.Char('Remarks', size=50)
    release_payment = fields.Boolean('Release Payment')
