from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import babel

    
class PayrollCycle(models.Model):
    _name = 'payroll.cycle'
    _inherit = 'mail.thread'
    _order = "id desc"
    _rec_name = 'month_id'
    
    cycle                   = fields.Selection([('cycle1','Cycle 1'),('cycle2','Cycle 2'),('cycle3','Cycle 3')],string='Cycle')
    month_id                = fields.Many2one('calendar.generation.line',string='Month')
    date_start              = fields.Date(string='Date From')
    date_end                = fields.Date(string='Date To')
    region_id               = fields.Many2one('pappaya.region')
    state_id                = fields.Many2one('res.country.state',domain=[('country_id.is_active','=',True)])
    district_id             = fields.Many2one("state.district", string='District')
    office_type_id          = fields.Many2one('pappaya.office.type',string="Office Type")
    branch_id               = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    
    region_ids              = fields.Many2many('pappaya.region','pappaya_region_cycle_rel','region_id','cycle_id',string="Region")
    state_ids               = fields.Many2many('res.country.state','res_country_state_cycle_rel','state_id','cycle_id',string="State",domain=[('country_id.is_active','=',True)])
    district_ids            = fields.Many2many("state.district", 'state_district_cycle_rel','state_id','cycle_id',string='District')
    office_type_ids         = fields.Many2many('pappaya.office.type','office_type_cycle_rel','state_id','cycle_id',string="Office Type")
    branch_ids              = fields.Many2many('operating.unit', 'branch_cycle_rel','branch_id','cycle_id',string='Branch',domain=[('type','=','branch')])
    state                   = fields.Selection([('draft', 'Draft'), ('request', 'Requested'), ('approve', 'Approved')]
                                , string="Status", default='draft', track_visibility='onchange', copy=False)
    hr_payslip_batch_ids    = fields.Many2many('hr.payslip.run','hr_payslip_run_cycle_rel','batch_id','cycle_id',string="Branch")
    
    
    
    @api.onchange('month_id')
    def onchange_month_id(self):
        for record in self:
            if record.month_id:
                record.date_start   = record.month_id.date_start
                record.date_end     = record.month_id.date_end
    
                
    @api.onchange('region_ids')
    def onchange_region_id(self):
        for record in self:
            domain = []
            region_domain = []
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
                state_ids = []
                for region_id in record.region_ids:
                    state_ids += region_id.state_id.ids
                region_domain.append(('id', 'in', state_ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
            domain.append(('type','=','branch'))
            record.state_ids = record.district_ids = record.branch_ids = None
            return {'domain': {'state_ids': region_domain,'branch_ids': domain}}
    
    @api.onchange('state_ids')
    def onchange_state_id(self):
        for record in self:
            domain = []
            state_domain = []
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
                state_domain.append(('state_id', 'in', record.state_ids.ids))
            domain.append(('type','=','branch'))
            record.district_ids = record.branch_ids = None
            return {'domain': {'district_ids': state_domain,'branch_ids': domain}}
            
            
    @api.onchange('district_ids')
    def onchange_district_id(self):
        for record in self:
            domain = []
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            domain.append(('type','=','branch'))
            record.branch_ids = None
            return {'domain': {'branch_ids': domain}}


    
    @api.constrains('cycle', 'month_id', 'date_start', 'date_end', 'branch_ids','state_ids','region_ids','district_ids','office_type_ids')
    def check_cycle_month_branch(self):
        domain = []
        for record in self:
            if record.state_ids:
                domain.append(('state_ids','in',record.state_ids.ids))
            else:
                domain.append(('state_ids','=',False))
            if record.region_ids:
                domain.append(('region_ids','in',record.region_ids.ids))
            else:
                domain.append(('region_ids','=',False))
            if record.district_ids:
                domain.append(('district_ids','in',record.district_ids.ids))
            else:
                domain.append(('district_ids','=',False))
            if record.office_type_ids:
                domain.append(('office_type_ids','in',record.office_type_ids.ids))
            else:
                domain.append(('office_type_ids','=',False))
            if record.branch_ids:
                domain.append(('branch_ids','in',record.branch_ids.ids))
            else:
                domain.append(('branch_ids','=',False))
            domain.append(('cycle', '=', record.cycle))
            domain.append(('month_id', '=', record.month_id.id))
            domain.append(('date_start', '=', record.date_start))
            domain.append(('date_end', '=', record.date_end))    
            exit_id = self.search(domain)
            if len(exit_id) > 1:
                raise ValidationError(_("Record already exists for this Payroll Cycle"))
            for payroll_batch in record.hr_payslip_batch_ids:
                attendance_not_confirm = self.env['hr.daily.attendance'].search([('branch_id','=',payroll_batch.branch_id.id),
                                                                                 ('attendance_date','>=',payroll_batch.date_start),
                                                                                 ('attendance_date','<=',payroll_batch.date_end),
                                                                                 ('state','=','draft')],limit=1)
                if attendance_not_confirm:
                    raise ValidationError(_('Please Approve Attendance for the selected Branch : %s')% (payroll_batch.branch_id.name))
                monthly_calender = self.env['hr.calendar'].search([('branch_id','=',payroll_batch.branch_id.id),
                                                                   ('date_from','=',payroll_batch.date_start),
                                                                   ('date_to','=',payroll_batch.date_end),
                                                                   ('state','!=','approve')
                                                                   ])
                if monthly_calender:
                    raise ValidationError(_('Please Approve calendar for the selected Branch : %s')% (payroll_batch.branch_id.name))
            

    @api.onchange('office_type_ids')
    def onchange_office_type_id(self):
        for record in self:
            domain = []
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            domain.append(('type','=','branch'))
            record.state_ids = record.district_ids = record.branch_ids = None
            return {'domain': {'branch_ids': domain}}
            
    
    @api.onchange('cycle','date_start','date_end','region_ids','state_ids','branch_ids','office_type_ids','district_ids')
    def payslip_generation_onchnage(self):
        for record in self:
            if record.cycle and record.date_start and record.date_end:
                domain = []
                if record.state_ids:
                    domain.append(('state_id','in',record.state_ids.ids))
                if record.region_ids:
                    domain.append(('region_id','in',record.region_ids.ids))
                if record.district_ids:
                    domain.append(('district_id','in',record.district_ids.ids))
                if record.office_type_ids:
                    domain.append(('office_type_id','in',record.office_type_ids.ids))
                if record.branch_ids:
                    domain.append(('id','in',record.branch_ids.ids))
                domain.append(('type','=','branch'))
                branch_sr = self.env['operating.unit'].search(domain)
                start = datetime.strptime(record.date_start, '%Y-%m-%d').date()
                end = datetime.strptime(record.date_end, '%Y-%m-%d').date()
                lock_and_sublock_sr        =   self.env['employee.lock.sublock'].sudo().search([
                                                                                             ('branch_id','in',branch_sr.ids),
                                                                                             ('date_start','=',record.date_start),
                                                                                             ('date_end','=',record.date_end),
                                                                                             ('lock_state','=','approved'),
                                                                                             ('sublock_state','=','approved')
                                                                                            ])
                branch_ids = []
                for lock_and_sublock in lock_and_sublock_sr:
                    branch_ids.append(lock_and_sublock.branch_id.id)
                
                payslip_batch_ids = self.env['hr.payslip.run'].search([('date_start','=',start),('date_end','=',end),('branch_id','in',branch_ids),('state','=','confirm')])
                record.hr_payslip_batch_ids = None
                record.hr_payslip_batch_ids = payslip_batch_ids.ids
    
    @api.multi
    def payslip_generation(self):
        for record in self:
            for batch in record.hr_payslip_batch_ids:
                batch.write({'state':'in_progress'})
            record.state = 'approve'
                            
    @api.multi
    def action_submit(self):
        for record in self:
            record.state = 'request'
            
            
    @api.multi
    def payroll_cycle_payslip_generation_update(self):
        batch_obj           = self.env['hr.payslip.run']
        payslip_batch_ids   = batch_obj.search([('state','=','in_progress')],limit=10)
        for payslip_batch_id in payslip_batch_ids:
            if payslip_batch_id.date_start and payslip_batch_id.date_end and payslip_batch_id.branch_id:
                batch_obj.current_month_create_and_update_payslip_one(payslip_batch_id.date_start,payslip_batch_id.date_end,payslip_batch_id.branch_id.id,False)
            hr_payslip_ids = []
            if payslip_batch_id:
                hr_payslip_ids = self.env['hr.payslip'].search([('payslip_run_id','=',payslip_batch_id.id),('state','=','draft')])
            for slip in hr_payslip_ids:
                slip.cron_compute_sheet()
                slip.write({'is_payroll_cycle':True})
            payslip_batch_id.write({'state':'done'})
            
            mail_mail = self.env['mail.mail']
            email_from = ''
            outgoing_email = self.env['ir.mail_server'].search([('id', '=', 1)])
            if outgoing_email:
                email_from = outgoing_email.smtp_user
    
            for user in self.env['res.users'].browse(payslip_batch_id.create_uid.id):
                try:
                    if user.email:
                        email_to = user.email
                        email_from = email_from
                        subject = _("Payroll cycle - success - %s" % (payslip_batch_id.name))
                        body = _("Dear Payroll Team,<br/>")
                        body += _(" The payroll cycle has been successfully completed %s."%(payslip_batch_id.name))
                        footer = "This auto generated email and please do not reply.,<br/>HR<br/>"
                        mail = mail_mail.create({
                            'email_to': email_to,
                            'email_from': email_from,
                            'res_id':user[0],
                            'record_name':'Payslip Generation',
                            'subject': subject,
                            'body_html':'''<span  style="font-size:14px"><br/>
                            <br/>%s<br/>
                            <br/>%s</span>''' %(body,footer),
                            })
                        mail.send(mail)
                        mail.mail_message_id.write({'res_id':user[0]})
                except :
                    print ("Exception")
        return True
        