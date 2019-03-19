from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)

class DayBookWizard(models.TransientModel):
    _name = "day.book.wizard"

    state_ids = fields.Many2many('res.country.state', string='State')
    entity_ids = fields.Many2many('operating.unit', string='Entity')
    branch_ids = fields.Many2many('operating.unit', string='Branch')
    academic_year_id = fields.Many2one('academic.year', string='Academic Year')
    payment_mode_ids = fields.Many2many('pappaya.paymode', string='Payment Mode')
    order_by = fields.Selection([('receipt_no','Receipt No')], default='receipt_no' , string='Order By')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    status = fields.Selection([('paid','Paid'),('cancel','Cancel')], string='Status')

    @api.multi
    @api.constrains('start_date','end_date')
    def _check_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('End-date must be greater than Start-date')

    @api.onchange('entity_ids')
    def onchange_entity(self):
        if self.entity_ids:
            return {'domain': {'branch_ids': [('parent_id', 'in', self.entity_ids.ids),('type','=','branch')]}}

    @api.onchange('branch_ids')
    def onchange_branch(self):
        domain, paymode = [], []
        if self.branch_ids:
            for branch in self.branch_ids:
                for pay in branch.paymode_ids:
                    paymode.append((pay.id))
                for academic in branch.course_config_ids:
                    domain.append(academic.academic_year_id.id)
        return {'domain': {'academic_year_id': [('id', 'in', domain)]}}

    @api.multi
    def get_data(self):
        domain, data_list, receipt_dict = [], [], {}
        if self.entity_ids:
            domain.append(('school_id.parent_id', 'in', self.entity_ids.ids))
        if self.branch_ids:
            domain.append(('school_id', 'in', self.branch_ids.ids))
        if self.start_date:
            domain.append(('receipt_date', '>=', self.start_date))
        if self.end_date:
            domain.append(('receipt_date', '<=', self.end_date))
        if self.payment_mode_ids:
            domain.append(('payment_mode_id', 'in', self.payment_mode_ids.ids))
        if self.status:
            domain.append(('state', '=', self.status))
        receipt_obj = self.env['pappaya.fees.receipt'].sudo().search(domain)
        pay_list = []
        for obj in receipt_obj:
            pay_list.append(obj.payment_mode_id.name)
        entity_list = []
        for ent in self.branch_ids:
            if ent.parent_id:
                entity_list.append(ent.parent_id.name)
        branch_list = []
        for br in self.branch_ids:
            if br:
                branch_list.append(br.name)
        for entity in set(entity_list):
            for brch in set(branch_list):
                s_no = 0
                vals = {}
                vals['receipt_line'] = []
                vals['paymode_total_line'] = []
                vals['entity'] = entity
                vals['branch'] = brch
                total_payment = 0.0
                for pay in set(pay_list):
                    pay_total = 0.0
                    for objs in self.env['pappaya.fees.receipt'].sudo().search([('school_id', '=', brch), ('school_id.parent_id.name', '=', entity),('payment_mode_id', 'in', pay),
                                                                                ('receipt_date', '>=', self.start_date), ('receipt_date', '<=', self.end_date),('state', '=', self.status)]):
                        for ob_line in self.env['pappaya.fees.receipt.line'].search([('receipt_id', '=', objs.id)]):
                            if ob_line.total_paid > 0 and not ob_line.name.is_course_fee:
                                s_no += 1
                                rvals = {}
                                rvals['s_no'] = s_no
                                rvals['adm_no'] = objs.admission_number if objs.admission_number else objs.name.application_no
                                rvals['student_name'] = str(objs.name.sur_name or '') + ' ' + str(objs.name.name)
                                rvals['code'] = objs.name.package_id.name if objs.name.package_id.name else ''
                                rvals['payment_mode'] = objs.payment_mode_id.name if objs.payment_mode_id.name else ''
                                rvals['trans_type'] = objs.transaction_type.name if objs.transaction_type.name else ''
                                rvals['fee_head'] = ob_line.name.name if ob_line.name.name else ''
                                rvals['receipt_date'] = datetime.strptime(str(objs.receipt_date),DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y") if objs.receipt_date else ''
                                rvals['amount'] = ob_line.total_paid if ob_line.total_paid else 0.0
                                rvals['status'] = ob_line.fees_coll_line_id.term_state if ob_line.fees_coll_line_id.term_state else ''
                                pay_total += ob_line.total_paid
                                vals['receipt_line'].append(rvals)
                    pvals = {}
                    pvals['pay_mode'] = pay
                    pvals['pay_total'] = pay_total
                    vals['paymode_total_line'].append(pvals)
                    vals['pay_total'] = pay_total
                    vals['pay_mode'] = pay
                    total_payment += pay_total
                vals['total_payment'] = total_payment
                data_list.append(vals)
        return data_list

    @api.multi
    def generate_pdf_report(self):
        return self.env.ref('pappaya_fees.print_template_daybook').get_report_action(self)
