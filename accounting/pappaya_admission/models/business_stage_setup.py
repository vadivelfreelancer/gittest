# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
import odoo
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class pappaya_workflow_grade_doc_config(models.Model):
    """ Workflow config document   """
    _name = "pappaya.workflow.grade_doc_config"
    _order = "id asc"
    _description = "Enquiry grade document config ..."

    document_name = fields.Char('Document Name')
    business_stage_id = fields.Many2one('pappaya.business.stage')
    description = fields.Char('Description')
    required = fields.Boolean('Required')

class pappaya_business_stage(models.Model):
    """ Workflow Definition  """
    _name = "pappaya.business.stage"
    _order = "school_id,sequence asc"
    _description = "Classify the workflow definition, ..."
    
    @api.model
    def _default_school(self):
        user_id = self.env['res.users'].sudo().browse(self.env.uid)
        if user_id.company_id and user_id.company_id.type == 'school':
            return user_id.company_id.id
 
    school_id = fields.Many2one('operating.unit', 'Branch')
    name = fields.Char(string = 'Admission Stage Name')
    code = fields.Char(string = 'Admission Stage Code')
    sequence = fields.Integer(string = 'Sequence Number')
    is_active = fields.Boolean(default=True, string = 'Enable the following Stage?')
    notification_required = fields.Boolean('Notification Required')
    notification_mails = fields.Text('Notification Mails')
    grade_ids = fields.Many2many('pappaya.course',string="Course Names")
    is_final_stage = fields.Boolean(string = 'Is Final Stage?', default=False)
    is_fin_short_list_stage = fields.Boolean('Is Final Shortlisted Stage', default=False)
    grade_join_doc_o2m = fields.One2many('pappaya.workflow.grade_doc_config','business_stage_id','Grade Joining Document')
    is_fees_applicable = fields.Boolean('Is Fees Applicable for the Current Stage?', default=False)
    fees_id = fields.Many2many('pappaya.fees.head', string='Fee')
    is_report_applicable = fields.Boolean('If any Report/Approval required?')
    email_content = fields.Text('Email Template')
    transaction_type_ids = fields.Many2many('pappaya.master', string='Transaction Type')
    
    @api.one
    @api.constrains('name', 'code','is_final_stage')
    def _check_unique_name(self):
        if self.name:
            if len(self.search(
                    [('name', '=', (self.name).strip()), ('school_id', '=', self.school_id.id)])) > 1:
                raise ValidationError("Admission Stage Name has already been defined.")
        if self.code:
            if len(self.search([('code', '=', self.code), ('school_id', '=', self.school_id.id)])) > 1:
                raise ValidationError("Admission Stage Code has already been defined.")
        if self.is_final_stage:
            if len(self.search([('is_final_stage', '=', True), ('school_id', '=', self.school_id.id)])) > 1:
                raise ValidationError("The Final Stage has already been defined. Please do note that a Branch can only have one Final Stage")

    @api.onchange('is_final_stage')
    def onchange_final_stage(self):
        if self.is_final_stage:
            grade_ids = self.env['pappaya.course'].search([('branch_id','=',self.school_id.id)])
            if grade_ids:
                self.grade_ids = grade_ids.ids
            self.is_fees_applicable = None


    @api.onchange('school_id')
    def get_fees_filter(self):
        if self.school_id:
            fee_list, fee_head_list = [], []
            for head in self.env['pappaya.fees.head'].search([]):
                fee_head_list.append(head.id)
            for rec in self.search([('school_id','=',self.school_id.id)]):
                for fees in rec.fees_id:
                    fee_list.append(fees.id)
            final_list = list(set(fee_head_list) - set(fee_list))
            return {'domain': {'fees_id': [('id', 'in', final_list)]}}

#     @api.onchange('is_final_stage')
#     def onchange_final_stage(self):
#         if self.is_final_stage:
#             self.fee_applicable_rte = None

    # def create(self, cr, uid, vals, context=None):
    #     print ("=====================================================")
    #     if vals.get('name'):
    #         self.pool.get('res.company')._validate_name(vals.get('name'))
    #         vals['name'] = ((vals.get('name')).strip()).title()
    #     self.validate(cr, uid, [], vals, context=context)
    #     new_Id = super(pappaya_business_stage, self).create(cr, uid, vals, context=context)
    #     return new_Id
    #
    # def write(self, cr, uid, ids, vals, context=None):
    #     if 'name' in vals and vals.get('name'):
    #         self.pool.get('res.company')._validate_name(vals.get('name'))
    #         vals['name'] = ((vals.get('name')).strip()).title()
    #     self.validate(cr, uid, ids, vals, context=context)
    #     new_Id = super(pappaya_business_stage, self).write(cr, uid, ids, vals, context=context)
    #     return new_Id

    @api.model
    def create(self, vals):
        if vals.get('name'):
            self.env['res.company']._validate_name(vals.get('name'))
            vals['name'] =  ((vals.get('name')).strip()).title()
        self.validate(self.env.cr, self.env.uid, [], vals, context=None)
        new_Id = super(pappaya_business_stage, self).create(vals)
        return new_Id

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            self.env['res.company']._validate_name(vals.get('name'))
            vals['name'] =  ((vals.get('name')).strip()).title()
        self.validate(self.env.cr, self.env.uid, self.ids, vals, context=None)
        new_Id = super(pappaya_business_stage, self).write(vals)
        return new_Id

    def validate(self, cr, uid, ids, vals, context=None):
        if ids:
            if isinstance(ids, (int, float, complex)):
                definition_obj = self.browse( ids)
            elif isinstance(ids, (tuple, list, dict, set)):
                definition_obj = self.browse(ids[0])
        else:
            definition_obj = False
        dynamic_query = ""
        validation_query = ""

        if 'school_id' in vals:
            school_id = vals['school_id']
        else:
            school_id = definition_obj.school_id.id

        if 'sequence' in vals:
            sequence = vals['sequence']
        else:
            sequence = definition_obj.sequence
        dynamic_query += " select id from pappaya_business_stage where is_active = TRUE "

        if school_id:
            dynamic_query += " and school_id = " + str(school_id)
        # if process_type_id:
        #             dynamic_query += " and process_type_id = "+str(process_type_id)
        if definition_obj:
            dynamic_query += " and id != " + str(definition_obj.id)
        validation_query += dynamic_query
        dynamic_query += " and sequence=" + str(sequence)
        validation_query += " and sequence <" + str(sequence)
        cr.execute(dynamic_query, ())
        res = cr.fetchall()
        #         if is_level_based and no_of_levels < 1:
        #             raise ValidationError('Please enter no. of levels greater than 0.')
        if not sequence > 0:
            raise ValidationError('Please enter sequence greater than 0.')
        if res:
            raise ValidationError('Please enter unique sequence.')
        cr.execute(validation_query, ())
        validation_res = cr.fetchall()
        if len(validation_res) != 0 and len(validation_res) != (sequence - 1):
            raise ValidationError('Please enter sequence in sequential order starting from 1.')
        elif len(validation_res) == 0 and sequence > 1:
            raise ValidationError('Please enter sequence in sequential order starting from 1.')
        return True
