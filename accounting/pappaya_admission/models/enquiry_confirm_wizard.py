# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class EnquiryConfirmwizard(models.TransientModel):
    _name = 'pappaya.enquiry.confirm.wizard'

    stage = fields.Char('Next Stage', readonly=1)
    remarks_1 = fields.Char('Fees are', readonly=1)
    fees = fields.Boolean('Is Fees', default=False)
    remarks_2 = fields.Text('Remarks',size=300)

    @api.multi
    def action_confirm_msg(self):
        _logger.debug(' \n\n \t We can do some actions here\n\n\n')
        enq_id = self.env.context.get('active_id')
        enquiry=self.env['pappaya.admission'].browse(enq_id)
        print ('\n', 'enquiry', enq_id, enquiry)

        if enquiry.stage_id.sequence == 1:
            app_list = []
            for app_seq in self.env['pappaya.admission'].search([('stage_id.sequence', '=', 1)]):
                app_list.append(app_seq)
            sequence = len(app_list)
            enquiry.write({'application_no': ("{0:07d}".format(sequence+1))})
        if enquiry.stage_id.sequence == 2 and enquiry.old_new == 'new' and enquiry.branch_id.office_type_id.type == 'school':
            seq_list = []
            for school_seq in self.env['pappaya.admission'].search([('stage_id.sequence', '>', 2),('office_type_id.type','=','school')]):
                seq_list.append(school_seq)
            sequence = len(seq_list)
            enquiry.write({'res_no': '5' + str("{0:06d}".format(sequence+1)), 'admission_no': '5' + str("{0:06d}".format(sequence+1))})
        elif enquiry.stage_id.sequence == 2 and enquiry.old_new == 'new' and enquiry.branch_id.office_type_id.type != 'school':
            coll_list = []
            for college_seq in self.env['pappaya.admission'].search([('stage_id.sequence', '>', 2),('office_type_id.type','!=','school')]):
                coll_list.append(college_seq)
            sequence = len(coll_list)
            enquiry.write({'res_no': '1' + str("{0:06d}".format(sequence+1)), 'admission_no': '1' + str("{0:06d}".format(sequence+1))})
        enquiry.conform_stage()


    @api.multi
    def action_approve(self):
        enq_id = self.env.context.get('active_id')
        enquiry = self.env['pappaya.admission'].browse(enq_id)
        enquiry.stage_approval(self.remarks_2)

    @api.multi
    def action_cancel(self):
        enq_id = self.env.context.get('active_id')
        enquiry = self.env['pappaya.admission'].browse(enq_id)
        enquiry.cancel_approval(self.remarks_2)

    @api.multi
    def action_stage_cancel(self):
        enq_id = self.env.context.get('active_id')
        enquiry = self.env['pappaya.admission'].browse(enq_id)
        enquiry.cancel_stage(self.remarks_2)

    @api.multi
    def action_shortlist_confirm(self):
        enq_id = self.env.context.get('active_id')
        enquiry = self.env['pappaya.admission'].browse(enq_id)
        enquiry.s_confirm(self.remarks_2)