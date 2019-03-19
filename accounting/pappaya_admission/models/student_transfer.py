# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

class student_fees_collection(models.Model):
    _inherit='student.fees.collection'
    
    student_transfer_id = fields.Many2one('pappaya.student.transfer', 'Student Transfer Ref')
    
class pappaya_nslate_item_inherit(models.Model):
    _inherit='pappaya.nslate.item'
    
    student_transfer_id = fields.Many2one('pappaya.student.transfer', 'Student Transfer Ref')

class student_transfer_deduction_line(models.Model):
    _name = 'student.transfer.deduction.line'
    _rec_name = 'student_transfer_id'
    
    student_transfer_id = fields.Many2one('pappaya.student.transfer', 'Student Transfer Ref')
    deduction_head_id = fields.Many2one('pappaya.master', 'Deduction', domain="[('type','=','deduction')]")
    amount = fields.Float('Amount')
    reason = fields.Char('Reason')

class PappayaStudentTransfer(models.Model):
    _name = 'pappaya.student.transfer'
    _rec_name = 'pappaya_student_id'
    _order = "id desc"
    
    @api.multi
    @api.depends('student_transfer_deduction_line')
    def _compute_total_deductions(self):
        for record in self:
            total = 0.0
            for line in record.student_transfer_deduction_line:
                total += line.amount
            record.total_deductions = total
            
    @api.multi
    @api.depends('nslate_item_ids.price_subtotal')
    def compute_nslate_amount(self):
        for record in self:
            amount = 0.0
            for item in record.nslate_item_ids:
                amount += item.price_subtotal
            record.nslate_amount = amount
            record.to_course_fee_total += amount
            
    @api.multi
    @api.depends('material_set_ids.price_subtotal')
    def compute_material_amount(self):
        for record in self:
            amount = 0.0
            for item in record.material_set_ids:
                amount += item.price_subtotal
            record.material_amt = amount

    state = fields.Selection([('draft','Draft'),('request','Request'),('approve', 'Approved'),
                              ('rejected', 'Rejected'),('transfered', 'Transfered')], default="draft")
    transfer_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], default="internal",string='Transfer Type')
    school_id = fields.Many2one('operating.unit', 'Branch')
    father_name = fields.Char(string="Father")
    medium_id = fields.Many2one('pappaya.master', string='Medium')
    pappaya_student_id = fields.Many2one('res.partner', string="Student", domain=[('user_type','=','student')])
    
    for_branch_id = fields.Many2one('operating.unit', string='For Branch')
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    current_date = fields.Date('Date',default=datetime.today().date())
    # From
    from_course_id = fields.Many2one('pappaya.course', string='Course/Class')
    from_group_id = fields.Many2one('pappaya.group', string='Group')
    from_batch_id = fields.Many2one('pappaya.batch', string='Batch')
    from_package_id = fields.Many2one('pappaya.package', string='Package')
    from_course_package_id = fields.Many2one('pappaya.course.package')
    from_residential_type_id = fields.Many2one('residential.type', string='Residential Type')
      
    # To
    course_id = fields.Many2one('pappaya.course', string='Course/Class')
    group_id = fields.Many2one('pappaya.group', string='Group')
    batch_id = fields.Many2one('pappaya.batch', string='Batch')
    package_id = fields.Many2one('pappaya.package', string='Package')
    course_package_id = fields.Many2one('pappaya.course.package', string='Course Package')
    to_residential_type_id = fields.Many2one('residential.type', string='Residential Type')
    
    from_course_fee_total = fields.Float(string='Total Amount')
    from_course_fee_committed = fields.Float('Committed Amount')
    from_course_fee_less = fields.Float(string='Prev. Less Amount')
    total_fee_paid = fields.Float(string='Total Paid Amount')
    
    to_course_fee_total = fields.Float('Total Amount')
    to_course_fee_committed = fields.Float('Committed Amount')
    to_course_fee_less = fields.Float('Less Amount')
    
    total_deductions = fields.Float(string='Total Deductions', compute='_compute_total_deductions')
    
    reason = fields.Text('Reason for Transfer',size=300)
    approve_reason = fields.Text('Approved Reason',size=300)
    reject_reason = fields.Text('Rejected Reason',size=300)
    student_transfer_deduction_line = fields.One2many('student.transfer.deduction.line', 'student_transfer_id', 'Deduction Details') 
    fee_collection_ids = fields.One2many('student.fees.collection','student_transfer_id', 'Fee Collection Details')
    
    # Questionaries
    is_uniform_required = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no', string='Is Uniform Required?')
    is_uniform_fee_added = fields.Boolean('Is Uniform fee added already?')
    is_nslate_required = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no', string='Is Nslate Required?')
    is_transport = fields.Boolean('Is Show Transport Details?')
    is_transport_required = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no', string='Is Transport Required?')
    material_set_ids = fields.Many2many('branchwise.material.line', string='Material Set')
    nslate_item_ids = fields.One2many('pappaya.nslate.item', 'student_transfer_id', string='Nslate')
    nslate_amount = fields.Float(string='Nslate Amount', compute='compute_nslate_amount')
    material_amt = fields.Float(string='Material Amount', compute='compute_material_amount')
    transport_slab_id = fields.Many2one('pappaya.transport.stop', string='Transport Slab')
    service_route_id = fields.Many2one('pappaya.transport.route', string='Service Route')
    amount_transferable = fields.Float("Amount Transferable")
    total_refund_amount = fields.Float('Amount Refundable')
    is_create_refund = fields.Boolean('Is Create Refund?', default=False)
    is_refund_created = fields.Boolean('Is Refund Created?', default=False)
    excess_amount_move_to = fields.Selection([('refund_request','Refund Request'),('caution_deposit','Caution Deposit')], 'Excess Amount Move TO',
                                             default='refund_request')
    
    @api.onchange('is_nslate_required')
    def onchange_is_nslate_required(self):
        if self.is_nslate_required and self.is_nslate_required == 'no':
            self.nslate_item_ids = False
            
    @api.onchange('is_uniform_required')
    def onchange_is_uniform_required(self):
        branch_id = self.school_id if self.transfer_type == 'internal' else self.for_branch_id
        course_uniform = self.env['pappaya.uniform'].search([('academic_year_id', '=', self.academic_year_id.id),
                                                                 ('school_id', '=', branch_id.id),
                                                                 ('course_id', '=', self.course_id.id),
                                                                 ('gender', '=', self.pappaya_student_id.gender)])  
                
        if course_uniform and self.is_uniform_required == 'yes':        
            self.to_course_fee_total += course_uniform.total_amount
            self.is_uniform_fee_added = True
        elif course_uniform and self.is_uniform_required == 'no':
            if self.is_uniform_fee_added:
                self.to_course_fee_total -= course_uniform.total_amount
                self.is_uniform_fee_added = False
        else:
            if self.is_uniform_required == 'yes' and not course_uniform:
                self.is_uniform_required = 'no'
                return {
                        'warning': {'title': _('User Error'), 'message': _('No Uniform set defined for given branch, course and gender!'),},
                         }            
    
    @api.onchange('transfer_type','school_id')
    def onchange_transfer_type(self):
        if self.transfer_type == 'internal':
            self.for_branch_id = self.school_id.id
        else:
            self.for_branch_id = False
            
    @api.onchange('for_branch_id','to_residential_type_id')
    def onchange_branch_id(self):
        if self.for_branch_id.is_transport and self.to_residential_type_id and self.to_residential_type_id.code != 'hostel':
            self.is_transport = True
        else:
            self.is_transport = False
        
    @api.model
    def create(self, vals):
        course_info = {}        
        student_obj = self.env['res.partner'].search([('id','=',vals['pappaya_student_id'])])
        course_info.update({
            'father_name': student_obj.father_name,
            'from_course_id' : student_obj.course_id.id,
            'from_group_id' : student_obj.group_id.id,
            'from_batch_id' : student_obj.batch_id.id,
            'from_package_id' : student_obj.package_id.id,
            'from_course_package_id' : student_obj.course_package_id.id,
            'from_residential_type_id':student_obj.residential_type_id.id,
            'medium_id': student_obj.medium_id.id
            })
        fee_collection_ids = []
        total_fee = 0.0; total_course_fee = 0.0; total_paid = 0.0
        
        fee_structure_id = self.env['pappaya.fees.structure'].search([('course_id','=',student_obj.course_package_id.course_id.id),
                                                ('group_id','=',student_obj.course_package_id.group_id.id),('academic_year_id','=',student_obj.admission_id.academic_year.id),
                                                ('school_id','=',student_obj.school_id.id), ('batch_id','=',student_obj.course_package_id.batch_id.id),
                                                ('package_id','=',student_obj.course_package_id.package_id.id),('residential_type_id','=',student_obj.residential_type_id.id)])
                
        course_fee_id = self.env['pappaya.fees.structure.line'].search([('structure_id','=',fee_structure_id.id),
                                                                ('fees_id.is_course_fee','=',True)], limit=1)
        total_course_fee = course_fee_id.total if self.pappaya_student_id.admission_id.old_new == 'old' else course_fee_id.new_total           

        fee_collection_id = self.env['pappaya.fees.collection'].sudo().search([('enquiry_id','=',student_obj.admission_id.id),('admission_cancel','=',False)])
        for fee_line in fee_collection_id.fees_collection_line:
            if not fee_line.name.is_reservation_fee and not fee_line.name.is_course_fee:
                total_fee += fee_line.amount
                
            if not fee_line.name.is_course_fee:
                total_paid += fee_line.total_paid
                         
            fee_collection_ids.append((0,0, {
                'student_transfer_id' : self.id,
                'name': fee_line.name.id,
                'gst_total': fee_line.gst_total,
                'cgst': fee_line.cgst,
                'sgst': fee_line.sgst,
                'amount': fee_line.amount,
                'res_adj_amt': fee_line.res_adj_amt,
                'concession_amount': fee_line.concession_amount,
                'due_amount': fee_line.due_amount,
                'total_paid': fee_line.total_paid,
                'term_state': fee_line.term_state,
                }))
        course_info.update({'fee_collection_ids':fee_collection_ids, 'from_course_fee_total': total_fee, 
                            'from_course_fee_committed': student_obj.admission_id.res_comm_amount,
                            'total_fee_paid': total_paid})
        vals.update(course_info)
        return super(PappayaStudentTransfer, self).create(vals)
    
    @api.multi
    def write(self, vals):
        if 'pappaya_student_id' in vals:
            course_info = {}
            student_obj = self.env['res.partner'].search([('id','=',vals['pappaya_student_id'])])
            course_info.update({
                'father_name': student_obj.father_name,
                'from_course_id' : student_obj.course_id.id,
                'from_group_id' : student_obj.group_id.id,
                'from_batch_id' : student_obj.batch_id.id,
                'from_package_id' : student_obj.package_id.id,
                'from_course_package_id' : student_obj.course_package_id.id,
                'from_residential_type_id':student_obj.residential_type_id.id,
                'medium_id': student_obj.medium_id.id
                })
            fee_collection_ids = []
            total_fee = 0.0; total_course_fee = 0.0; total_paid = 0.0
            
            fee_structure_id = self.env['pappaya.fees.structure'].search([('course_id','=',self.from_course_package_id.course_id.id),
                                                    ('group_id','=',self.from_course_package_id.group_id.id),('academic_year_id','=',self.academic_year_id.id),
                                                    ('school_id','=',self.school_id.id), ('batch_id','=',self.from_course_package_id.batch_id.id),
                                                    ('package_id','=',self.from_course_package_id.package_id.id),('residential_type_id','=',self.from_residential_type_id.id)])
                    
            course_fee_id = self.env['pappaya.fees.structure.line'].search([('structure_id','=',fee_structure_id.id),
                                                                    ('fees_id.is_course_fee','=',True)], limit=1)
            total_course_fee = course_fee_id.total if self.pappaya_student_id.admission_id.old_new == 'old' else course_fee_id.new_total
                          
            fee_collection_id = self.env['pappaya.fees.collection'].sudo().search([('enquiry_id','=',student_obj.admission_id.id),('admission_cancel','=',False)])
            for fee_line in fee_collection_id.fees_collection_line:
                if not fee_line.name.is_reservation_fee and not fee_line.name.is_course_fee:
                    total_fee += fee_line.amount
                if not fee_line.name.is_course_fee:
                    total_paid += fee_line.total_paid
                
                fee_collection_ids.append((0,0, {
                    'student_transfer_id' : self._origin.id,
                    'name': fee_line.name.id,
                    'gst_total': fee_line.gst_total,
                    'cgst': fee_line.cgst,
                    'sgst': fee_line.sgst,
                    'amount': fee_line.amount,
                    'res_adj_amt': fee_line.res_adj_amt,
                    'concession_amount': fee_line.concession_amount,
                    'due_amount': fee_line.due_amount,
                    'total_paid': fee_line.total_paid,
                    'term_state': fee_line.term_state,
                    }))
            course_info.update({'fee_collection_ids':fee_collection_ids, 'from_course_fee_total': total_fee, 
                                'from_course_fee_committed': student_obj.admission_id.res_comm_amount,
                                'total_fee_paid': total_paid})

            course_info.update({'to_course_fee_total':self._get_to_course_fee_total(fee_structure_id)})                       

            vals.update(course_info)
        return super(PappayaStudentTransfer, self).write(vals)
    
    @api.constrains('pappaya_student_id','from_course_package_id', 'course_package_id','to_residential_type_id')
    def validate_record(self):
        if self.transfer_type =='internal' and (self.from_course_package_id.id == self.course_package_id.id and self.from_residential_type_id.id == self.to_residential_type_id.id):
            raise ValidationError("For internal transfer From CGBP and To CGBP should not be same.")
        elif self.transfer_type =='external' and self.from_course_id and self.course_id and not (self.from_course_id.id == self.course_id.id):
            raise ValidationError("For External Transfer From Course and To Course should be same.")
        # Check for pending cheques
        if self.pappaya_student_id:
            fee_collection_id = self.env['pappaya.fees.collection'].sudo().search([('enquiry_id','=',self.pappaya_student_id.admission_id.id),
                                                                                    ('admission_cancel','=',False)])
            processing = False
            if fee_collection_id:
                for line in fee_collection_id.fees_collection_line:
                    if line.term_state == 'processing':
                        processing = True
                if processing:
                    raise ValidationError("For chosen student, paid non cash deposit still in processing, \n Please try again once deposit is cleared.")        
        # Less Amount
        if self.from_course_fee_less < self.to_course_fee_less:
            raise ValidationError("Less amount should not be exceeded than previous less amount.")
        elif not self.to_course_fee_less >= 0.0:
            raise ValidationError("Less amount should not be lesser than 0.0")

        return True
    
    @api.onchange('student_transfer_deduction_line')
    @api.constrains('student_transfer_deduction_line')
    @api.depends('student_transfer_deduction_line')
    def onchange_student_transfer_deduction_line(self):
        total_amount = 0.0
        if student_transfer_deduction_line:
            for line in self.student_transfer_deduction_line:
                if self.student_transfer_deduction_line.search_count([('student_transfer_id','=',self.id),('deduction_head_id','=',line.deduction_head_id.id)]) > 1:
                    raise ValidationError(_("Deduction head already exists. (%s)") % line.deduction_head_id.name)
                if not line.amount >= 0.0:
                    raise ValidationError(_("Deduction amount should be greated than 0.00 for (%s)") % line.deduction_head_id.name)
                    raise ValidationError
                total_amount += line.amount         
            if total_amount > self.total_fee_paid:
                raise ValidationError("Deduction amount should not be excced than total fee paid.")
        
        transferable = (self.total_fee_paid - total_amount)
        self.update({'amount_transferable': transferable, 
                     'total_refund_amount': transferable - self.to_course_fee_total })
        
    @api.multi
    def create_refund(self):
        for record in self:
            if record.is_refund_created:
                raise ValidationError("Refund Request Already Created.")
            
            fee_collection_id = self.env['pappaya.fees.collection'].sudo().search([('enquiry_id','=',record.pappaya_student_id.admission_id.id),
                                                                                   ('admission_cancel','=',False)])
                
            if fee_collection_id:
                course_fee_line_id = self.env['student.fees.collection'].search([('collection_id','=',fee_collection_id.id), ('name.is_course_fee','=',True)])
                refund_line_ids = []
                refund_id = self.env['pappaya.fees.refund'].create({'student_id': record.pappaya_student_id.id if record.pappaya_student_id else False,
                                               'branch_id': record.school_id.id,
                                               'admission_id': record.pappaya_student_id.admission_id.id,
                                               'course_package_id': record.from_course_package_id.id,
                                               'admission_no': record.pappaya_student_id.admission_id.admission_no if record.pappaya_student_id.admission_id.old_new == 'old' else record.pappaya_student_id.admission_id.res_no,
                                               'father_name': record.father_name,
                                               'fees_collection_id': fee_collection_id.id,
                                               'is_update': True,
                                               'refund_type': 'internal_transfer' if record.transfer_type == 'internal' else 'external_transfer',
                                               'refund_reason': record.transfer_type.title()+' Transfer Refund'})            
            
                refund_line_ids.append((0, 0, {'fees_head_id': course_fee_line_id.name.id,
                                             'amount': record.total_refund_amount,
                                             'due_amount': 0.0,
                                             'res_adj_amt': 0.0,
                                             'total_paid': record.total_refund_amount,
                                             'cgst': 0.0,
                                             'is_select':True,
                                             'sgst': 0.0,
                                             'term_state': 'paid',
                                             'gst_total': record.total_refund_amount}))
                refund_id.write({'refund_amount':record.total_refund_amount,'refund_line_ids':refund_line_ids})
            record.is_refund_created = True
            
            transferable = (record.total_fee_paid - record.total_deductions)
            record.amount_transferable = ( transferable - record.total_refund_amount)
            return True

    @api.onchange('to_course_fee_less')
    def onchange_to_course_fee_less(self):
        if self.from_course_fee_less < self.to_course_fee_less:
            raise ValidationError("Less amount should not be exceeded than previous less amount.")
            
    @api.onchange('pappaya_student_id')
    def _onchange_student(self):
        # Check for pending cheques
        if self.pappaya_student_id:
            fee_collection_id = self.env['pappaya.fees.collection'].sudo().search([('enquiry_id','=',self.pappaya_student_id.admission_id.id),
                                                                                   ('admission_cancel','=',False)])
            processing = False
            if fee_collection_id:
                for line in fee_collection_id.fees_collection_line:
                    if line.term_state == 'processing':
                        processing = True
                if processing:
                    raise ValidationError("For chosen student, paid non cash deposit still in processing, \n Please try again once deposit is cleared.")

        if self.pappaya_student_id:
            course_info = {}
            if self.search([('pappaya_student_id','=', self.pappaya_student_id.id),('academic_year_id','=',self.academic_year_id.id)]):
                raise ValidationError("Transfer record is already exists selected academic year for selected admission number.")
            course_info.update({
                'father_name': self.pappaya_student_id.father_name,
                'from_course_id' : self.pappaya_student_id.course_id,
                'from_group_id' : self.pappaya_student_id.group_id,
                'from_batch_id' : self.pappaya_student_id.batch_id,
                'from_package_id' : self.pappaya_student_id.package_id.id,
                'from_course_package_id' : self.pappaya_student_id.course_package_id.id,
                'from_residential_type_id':self.pappaya_student_id.residential_type_id.id,
                'medium_id': self.pappaya_student_id.medium_id.id
                })
            self.update(course_info)
            # Default deductions
            student_transfer_deduction_line = []
            for deduction in self.env['pappaya.master'].search([('type','=','deduction')]):
                student_transfer_deduction_line.append((0,0,{'deduction_head_id':deduction.id,'reason':deduction.name}))
            self.student_transfer_deduction_line = student_transfer_deduction_line
            fee_collection_ids = []
            # Update fees collection details
            total_fee = 0.0; total_course_fee = 0.0; total_paid = 0.0; committed_amount = 0.0; less_amount = 0.0
            concession_amount = 0.0
            fee_structure_id = self.env['pappaya.fees.structure'].search([('course_id','=',self.from_course_package_id.course_id.id),
                                                    ('group_id','=',self.from_course_package_id.group_id.id),('academic_year_id','=',self.academic_year_id.id),
                                                    ('school_id','=',self.school_id.id), ('batch_id','=',self.from_course_package_id.batch_id.id),
                                                    ('package_id','=',self.from_course_package_id.package_id.id),('residential_type_id','=',self.from_residential_type_id.id)])
                    
            course_fee_id = self.env['pappaya.fees.structure.line'].search([('structure_id','=',fee_structure_id.id),
                                                                    ('fees_id.is_course_fee','=',True)], limit=1)
                                                                    
            total_course_fee = course_fee_id.total if self.pappaya_student_id.admission_id.old_new == 'old' else course_fee_id.new_total       

            for fee_line in fee_collection_id.fees_collection_line:
                if fee_line.name.is_course_fee:
                    concession_amount = fee_line.concession_amount
                if not fee_line.name.is_reservation_fee and not fee_line.name.is_course_fee:
                    total_fee += fee_line.amount
                if not fee_line.name.is_course_fee:
                    total_paid += fee_line.total_paid
                    
                fee_collection_ids.append((0,0, {
                    'student_transfer_id' : self._origin.id,
                    'name': fee_line.name.id,
                    'gst_total': fee_line.gst_total,
                    'cgst': fee_line.cgst,
                    'sgst': fee_line.sgst,
                    'amount': fee_line.amount,
                    'res_adj_amt': fee_line.res_adj_amt,
                    'concession_amount': fee_line.concession_amount,
                    'due_amount': fee_line.due_amount,
                    'total_paid': fee_line.total_paid,
                    'term_state': fee_line.term_state,
                    }))
            
            self.fee_collection_ids = fee_collection_ids
            self.from_course_fee_total = total_fee
            self.from_course_fee_committed = self.pappaya_student_id.admission_id.res_comm_amount
            self.from_course_fee_less = ((total_course_fee - self.pappaya_student_id.admission_id.res_comm_amount)+concession_amount)
            self.total_fee_paid = total_paid
            
            course_domain = []
            if self.academic_year_id and self.school_id and self.transfer_type == 'internal':
                for academic in self.school_id.course_config_ids:
                    if academic.academic_year_id.id == self.academic_year_id.id:
                        course_domain = academic.course_package_ids.mapped('course_id').ids
                        break
            elif self.academic_year_id and self.for_branch_id and self.transfer_type == 'external':
                self.write({'group_id':False,'batch_id':False,'course_package_id':False,'package_id':False,'medium_id':False})
                for academic in self.for_branch_id.course_config_ids:
                    if academic.academic_year_id.id == self.academic_year_id.id:
                        for course_package in academic.course_package_ids:
                            if course_package.course_id.id == self.from_course_id.id:
                                course_domain.append(course_package.course_id.id)
            return {'domain': {'course_id': [('id', 'in', course_domain)]}}

    @api.onchange('academic_year_id', 'school_id', 'for_branch_id')
    def onchange_academic_year_id(self):
        domain = {}
        domain['for_branch_id'] = [('id','in',[])]; domain['pappaya_student_id'] = [('id','in',[])]
        course_domain = [];pappaya_student_ids = []
        branch_ids = []
        self.update({'course_id': False,'group_id':False,'batch_id':False,'course_package_id':False,
                    'package_id':False,'medium_id':False})
        if self.school_id:
            self.env.cr.execute("""
                Select 
                    stu.id 
                from                
                    res_partner stu join 
                    pappaya_admission adm on (adm.partner_id = stu.id) join
                    pappaya_business_stage pbs on (adm.stage_id = pbs.id)
                where
                    stu.school_id = %s and stu.user_type='student' and stu.active=True and pbs.sequence='4'
                order by stu.admission_no asc
                                    
            """ % self.school_id.id)
            results = self.env.cr.dictfetchall()
            for result in results:
                pappaya_student_ids.append(result['id'])
            branch_ids = self.env['operating.unit'].sudo().search([('parent_id', '=', self.school_id.parent_id.id),('office_type_id','=',self.school_id.office_type_id.id),
                            ('id', '!=', self.school_id.id)]).ids                                                                                                    
            domain['pappaya_student_id'] = [('id','in',list(set(pappaya_student_ids)))]
        domain['for_branch_id'] = [('id', 'in', branch_ids)]
        return {'domain': domain}

    @api.onchange('course_id')
    def onchange_course_id(self):
        domain = []; self.tc_fees_structure_line = None; self.diff_fee_collection_line = None
        if self.academic_year_id and self.school_id and self.transfer_type == 'internal':
            self.group_id = None;
            self.batch_id = None;
            self.package_id = None;
            self.course_package_id = None
            for academic in self.school_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id:
                            domain.append(course_package.group_id.id)
        elif self.academic_year_id and self.for_branch_id and self.transfer_type == 'external':
            self.group_id = None;
            self.batch_id = None;
            self.package_id = None;
            self.course_package_id = None
            for academic in self.for_branch_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id:
                            domain.append(course_package.group_id.id)
        return {'domain': {'group_id': [('id', 'in', domain)]}}

    @api.onchange('group_id')
    def onchange_group_id(self):
        domain = []; self.tc_fees_structure_line = None; self.diff_fee_collection_line = None
        if self.academic_year_id and self.school_id and self.transfer_type == 'internal':
            self.batch_id = None;
            self.package_id = None;
            self.course_package_id = None
            for academic in self.school_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id:
                            domain.append(course_package.batch_id.id)
        elif self.academic_year_id and self.for_branch_id and self.transfer_type == 'external':
            self.batch_id = None;
            self.package_id = None;
            self.course_package_id = None
            for academic in self.for_branch_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id:
                            domain.append(course_package.batch_id.id)
        return {'domain': {'batch_id': [('id', 'in', domain)]}}

    @api.onchange('batch_id')
    def onchange_batch_id(self):
        domain = []; self.tc_fees_structure_line = None; self.diff_fee_collection_line = None
        if self.academic_year_id and self.school_id and self.transfer_type == 'internal':
            self.course_package_id = None;
            self.package_id = None
            for academic in self.school_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id and course_package.batch_id.id == self.batch_id.id:
                            domain.append(course_package.package_id.id)
        elif self.academic_year_id and self.for_branch_id and self.transfer_type == 'external':
            self.course_package_id = None;
            self.package_id = None
            for academic in self.for_branch_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id and course_package.batch_id.id == self.batch_id.id:
                            domain.append(course_package.package_id.id)
        return {'domain': {'package_id': [('id', 'in', domain)]}}

    @api.onchange('package_id')
    def onchange_package(self):
        domain = []; self.tc_fees_structure_line = None; self.diff_fee_collection_line = None
        if self.academic_year_id and self.school_id and self.transfer_type == 'internal':
            self.course_package_id = None
            for academic in self.school_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id and course_package.batch_id.id == self.batch_id.id and course_package.package_id.id == self.package_id.id:
                            domain.append(course_package.id)
        elif self.academic_year_id and self.for_branch_id and self.transfer_type == 'external':
            self.course_package_id = None
            for academic in self.for_branch_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year_id.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id and course_package.batch_id.id == self.batch_id.id and course_package.package_id.id == self.package_id.id:
                            domain.append(course_package.id)
        return {'domain': {'course_package_id': [('id', 'in', domain)]}}

    @api.onchange('course_package_id', 'is_uniform_required','nslate_item_ids','transport_slab_id','material_set_ids')
    def onchange_to_course_package_id(self):
        if self.course_package_id and self.from_course_package_id:
            if self.transfer_type == 'internal':
                if self.transfer_type =='internal' and (self.from_course_package_id.id == self.course_package_id.id and self.from_residential_type_id.id == self.to_residential_type_id.id):
                    raise ValidationError("For internal transfer From CGBP and To CGBP should not be same.")
                
                fee_structure_id = self.env['pappaya.fees.structure'].search([('course_id','=',self.course_package_id.course_id.id),
                                                                              ('group_id','=',self.course_package_id.group_id.id),
                                                                              ('batch_id','=',self.course_package_id.batch_id.id),
                                                                              ('package_id','=',self.course_package_id.package_id.id),
                                                                              ('school_id','=',self.school_id.id),
                                                                              ('academic_year_id','=',self.academic_year_id.id),
                                                                              ('residential_type_id','=', self.to_residential_type_id.id)])                
            elif self.transfer_type == 'external':
                if self.transfer_type =='external' and self.from_course_id and self.course_id and not (self.from_course_id.id == self.course_id.id):
                    raise ValidationError("For External Transfer From Course and To Course should be same.")
                fee_structure_id = self.env['pappaya.fees.structure'].search([('course_id','=',self.course_package_id.course_id.id),
                                                                              ('group_id','=',self.course_package_id.group_id.id),
                                                                              ('batch_id','=',self.course_package_id.batch_id.id),
                                                                              ('package_id','=',self.course_package_id.package_id.id),
                                                                              ('school_id','=',self.for_branch_id.id),
                                                                              ('academic_year_id','=',self.academic_year_id.id),
                                                                              ('residential_type_id','=', self.to_residential_type_id.id)])
            
            if not fee_structure_id:
                raise ValidationError("No fee structure available for given course and student residential type combination.")
            
            course_fee_total = self._get_to_course_fee_total(fee_structure_id)
            self.update({'to_course_fee_total': course_fee_total})
            
            refund_amount = (self.amount_transferable - course_fee_total)
            if refund_amount > 0.0:
                self.is_create_refund = True
                self.update({'total_refund_amount': refund_amount})
            else:
                self.is_create_refund = False
                self.update({'total_refund_amount': 0.0})
        else:
            self.to_course_fee_total = 0.0
            self.is_create_refund = False; self.total_refund_amount = 0.0
            
    @api.onchange('total_refund_amount')
    def onchange_total_refund_amount(self):
        if self.total_refund_amount > 0.0:
            self.is_create_refund = True
        else:
            self.is_create_refund = False
                                                                    
    def _get_to_course_fee_total(self, fee_structure_id):
        total_fees = 0.0
        branch_id = self.school_id if self.transfer_type == 'internal' else self.for_branch_id
        # Uniform Fee
        course_uniform = self.env['pappaya.uniform'].search([('academic_year_id', '=', self.academic_year_id.id),
                                                                 ('school_id', '=', branch_id.id),
                                                                 ('course_id', '=', self.course_id.id),
                                                                 ('gender', '=', self.pappaya_student_id.gender)])
        for fee_line in fee_structure_id.structure_line_ids:
            
            fee_line_amount = 0.0
            if self.pappaya_student_id.admission_id.old_new == 'old':
                fee_line_amount = fee_line.total
            else:
                fee_line_amount = fee_line.new_total
                
            # Uniform Fee
            if not course_uniform and fee_line.fees_id.is_uniform_fee and self.is_uniform_required == 'no':
                continue
            if fee_line.fees_id.is_uniform_fee and course_uniform and self.is_uniform_required == 'yes':
                fee_line_amount = course_uniform.total_amount
                
            # Nslate Fee
            if fee_line.fees_id.is_nslate_fee and self.is_nslate_required == 'no':
                continue
            if self.nslate_item_ids and self.is_nslate_required == 'yes' and fee_line.fees_id.is_nslate_fee:
                fee_line_amount = self.nslate_amount
            
            # Library Fee
            if fee_line.fees_id.is_library_fee and not branch_id.is_library_fee:
                continue
            if fee_line.fees_id.is_library_fee and branch_id.is_library_fee:
                fee_line_amount = branch_id.library_fee_amount
            
            # Material Fee
            if not self.material_set_ids and fee_line.fees_id.is_material_fee:
                continue
            if self.material_set_ids:
                if fee_line.fees_id.is_material_fee:
                    fee_line_amount = self.material_amt
                    
            # Transport fee
            if fee_line.fees_id.is_transport_fee and self.is_transport_required == 'no':
                continue
            if self.to_residential_type_id.code != 'hostel' and self.is_transport_required == 'yes' and fee_line.fees_id.is_transport_fee: 
                fee_line_amount = self.transport_slab_id.amount           
            
            # Final Fee Line CREATION
            if not fee_line.fees_id.is_course_fee and not fee_line.fees_id.is_reservation_fee:
                if (fee_line.fees_id.gender == 'both' or self.pappaya_student_id.gender == fee_line.fees_id.gender) \
                    and (self.to_residential_type_id.id in fee_line.fees_id.residential_type_ids.ids) \
                    and (self.pappaya_student_id.admission_id.medium_id.id in fee_line.fees_id.medium_ids.ids):
                    total_fees += fee_line_amount 
                    
        return total_fees
    
    def update_fee_collection(self, fee_structure_id):
        refund_amount = (self.amount_transferable - self.to_course_fee_total)
        if refund_amount > 0.0 and self.excess_amount_move_to == 'refund_request':
            self.create_refund()
        student_history = {}; soa_amount = 0.0
        #### tracking history creation #######33
        movement_stage = self.pappaya_student_id.admission_id.stage_id.name+" -> "+self.transfer_type+' transfer'
        hist_obj = self.env['pappaya.enq.workflow.history']
        branch_id = self.for_branch_id if self.transfer_type == 'external' else self.school_id
        value = {'document_number':'',
                 'movement_stage':movement_stage,
                 'user_id':self.env.uid,
                 'updated_on':datetime.today(),
                 'enquiry_id':self.pappaya_student_id.admission_id.id,
                 'description': (str(self.pappaya_student_id.school_id.name) + ' -> ' +str(branch_id.name)),
                 'course_id':self.course_id.id,
                 'group_id':self.group_id.id,
                 'batch_id':self.batch_id.id,
                 'package_id':self.package_id.id,
                 'course_package_id':self.course_package_id.id,
                 'medium_id':self.medium_id.id,
                 'amount': self.total_fee_paid
                 }
        hist_obj.create(value)
        ######## END - tracking history ################         

        """ Update Admission details """
        admission_info_dict = {};ledger_info_dict = {}
        if self.transfer_type == 'external':
            ledger_info_dict.update({'school_id': self.for_branch_id.id})
            admission_info_dict.update({'branch_id': self.for_branch_id.id})
            
        # lockin amount
        course_fee_line = self.env['pappaya.fees.structure.line'].search([('structure_id','=',fee_structure_id.id),
                                                                ('fees_id.is_course_fee','=',True)], limit=1)
        if course_fee_line:
            total_course_fee = course_fee_line.amount if self.pappaya_student_id.admission_id.old_new == 'old' else course_fee_line.new_total
        committed_amount = (total_course_fee - self.to_course_fee_less)
        
        stage_id = self.env['pappaya.business.stage'].search([('school_id','=',self.for_branch_id.id),('sequence','=',1)])
        if not stage_id:
            raise ValidationError(_("Please configure Admission Stage setup for branch (%s)")%self.for_branch_id.name)
        
        admission_info_dict.update({
            'stage_id': stage_id.id,
            'course_id': self.course_id.id,
            'group_id': self.group_id.id,
            'batch_id': self.batch_id.id,
            'package':self.package_id.id,
            'package_id':self.course_package_id.id,
            'residential_type_id':self.to_residential_type_id.id,
#             'res_comm_amount':committed_amount,
#             'comm_place_holder':"Course Amount is Rs. %s"%total_course_fee
            })
        
        ledger_info_dict.update({
            'course_id': self.course_id.id,'group_id': self.group_id.id,'batch_id': self.batch_id.id,
            'package':self.package_id.id, 'package_id':self.course_package_id.id,
            })
        if self.is_transport_required == 'yes':
            admission_info_dict.update({
                'is_transport_required':'yes',
                'service_route_id': self.service_route_id.id,
                'transport_slab_id': self.transport_slab_id.id
                })
        if self.is_nslate_required == 'yes':
            for nslate_line in self.nslate_item_ids:
                if not nslate_line.admission_id.id == self.pappaya_student_id.admission_id.id: 
                    nslate_line.update({'admission_id':self.pappaya_student_id.admission_id.id})
        if self.is_uniform_required == 'yes':
            admission_info_dict.update({'is_uniform_required':'yes'})
        if self.material_set_ids:
            admission_info_dict.update({'material_set_ids':[(6,0,self.material_set_ids.ids)]})
        
        self.pappaya_student_id.admission_id.write(admission_info_dict) 
        
        """ Update Student  Details"""
        self.pappaya_student_id.admission_id.existing_old_student()
        self.pappaya_student_id.write({'caution_deposit':0.0, 'student_wallet_amount':0.0})
        
        comm_place_holder = "Course Amount is Rs. %s"%total_course_fee
        self._cr.execute("""
            update pappaya_admission set res_comm_amount = %s, comm_place_holder=%s where id = %s
        """, (committed_amount,comm_place_holder,self.pappaya_student_id.admission_id.id ))
        self._cr.commit()
        
        """ Update Fee collection Details """
        fee_collection_id = self.env['pappaya.fees.collection'].sudo().search([('enquiry_id','=',self.pappaya_student_id.admission_id.id),
                                                                               ('admission_cancel','=',False)])        
        fee_collection_id.write({
            'school_id' : self.school_id.id,
            'collection_date': str(datetime.now().date()),            
            })
        fee_collection_id.fees_collection_line.sudo().unlink()
        
        """ Fee Ledger Update """
        ledger_id = self.env['pappaya.fees.ledger'].sudo().search([('enquiry_id','=',self.pappaya_student_id.admission_id.id)])
        ledger_id.fee_ledger_line.sudo().unlink(); ledger_id.fee_receipt_ledger_line.sudo().unlink()
        ledger_id.write(ledger_info_dict)
        
        """ Fee Collection Line Update """
        
        fee_pay_yr = {'one_year' :1, 'two_year':2,'three_year':3}
        branch_id = self.school_id if self.transfer_type == 'internal' else self.for_branch_id
        # Uniform Fee
        course_uniform = self.env['pappaya.uniform'].search([('academic_year_id', '=', self.academic_year_id.id),
                                                                 ('school_id', '=', branch_id.id),
                                                                 ('course_id', '=', self.course_id.id),
                                                                 ('gender', '=', self.pappaya_student_id.gender)])
        less_amount = self.to_course_fee_less
        les_next_sequence = 1
        
        for fee_line in fee_structure_id.structure_line_ids:
            fee_line_amount = 0.0
            if self.pappaya_student_id.admission_id.old_new == 'old':
                fee_line_amount = fee_line.total
            else:
                fee_line_amount = fee_line.new_total
                
            # Uniform Fee
            if not course_uniform and fee_line.fees_id.is_uniform_fee and self.is_uniform_required == 'no':
                continue
            if fee_line.fees_id.is_uniform_fee and course_uniform and self.is_uniform_required == 'yes':
                fee_line_amount = course_uniform.total_amount
                
            # Nslate Fee
            if fee_line.fees_id.is_nslate_fee and self.is_nslate_required == 'no':
                continue
            if self.nslate_item_ids and self.is_nslate_required == 'yes' and fee_line.fees_id.is_nslate_fee:
                fee_line_amount = self.nslate_amount
            
            # Library Fee
            if fee_line.fees_id.is_library_fee and not branch_id.is_library_fee:
                continue
            if fee_line.fees_id.is_library_fee and branch_id.is_library_fee:
                fee_line_amount = branch_id.library_fee_amount
            
            # Material Fee
            if not self.material_set_ids and fee_line.fees_id.is_material_fee:
                continue
            if self.material_set_ids:
                if fee_line.fees_id.is_material_fee:
                    fee_line_amount = self.material_amt
                    
            # Transport fee
            if fee_line.fees_id.is_transport_fee and self.is_transport_required == 'no':
                continue
            if self.to_residential_type_id.code != 'hostel' and self.is_transport_required == 'yes' and fee_line.fees_id.is_transport_fee: 
                fee_line_amount = self.transport_slab_id.amount
                                                                    
            # Final Fee Line CREATION
            if not fee_line.fees_id.is_course_fee:
                if (fee_line.fees_id.gender == 'both' or self.pappaya_student_id.gender == fee_line.fees_id.gender) \
                    and (self.to_residential_type_id.id in fee_line.fees_id.residential_type_ids.ids) \
                    and (self.pappaya_student_id.admission_id.medium_id.id in fee_line.fees_id.medium_ids.ids):
                    # Less Sequence
                    if less_amount > 0.0 and fee_line.less_sequence == les_next_sequence:
                        les_next_sequence += 1
                        if fee_line_amount <= less_amount:
                            fee_line_amount = 0.0; less_amount -= fee_line_amount
                        else:
                            fee_line_amount -= less_amount 
                    # Two years Scenario
                    if fee_line.fees_id.is_course_fee_component:
                        fee_line_amount = fee_line_amount * fee_pay_yr[self.pappaya_student_id.admission_id.fees_opt_for]
                    
                    if fee_line.fees_id.is_soa_fee:
                        soa_amount += fee_line_amount

                    collection_line = fee_collection_id.fees_collection_line.create({
                        'collection_id': fee_collection_id.id,
                        'name': fee_line.fees_id.id,
                        'gst_total': fee_line_amount,
                        'cgst': fee_line.cgst if self.pappaya_student_id.admission_id.old_new == 'old' else fee_line.n_cgst,
                        'sgst': fee_line.sgst if self.pappaya_student_id.admission_id.old_new == 'old' else fee_line.n_sgst,
                        'amount': fee_line_amount,
                        'res_adj_amt': 0.0,
                        'due_amount': 0.00,
                        'total_paid': 0.00,
                        'term_state': 'due',
                        'enquiry_id': self.pappaya_student_id.admission_id.id,
                        'less_sequence': fee_line.less_sequence,                       
                        })

                    ledger_id.fee_ledger_line.create({
                        'fee_line_id': collection_line.id,
                        'credit': collection_line.amount,
                        'concession_amount': collection_line.concession_amount,
                        'concession_type_id': collection_line.concession_type_id.id,
                        'debit': collection_line.total_paid,
                        'balance': collection_line.amount - (collection_line.total_paid + collection_line.concession_amount),
                        'fees_ledger_id': ledger_id.id,
                        'res_adj_amt': collection_line.res_adj_amt,
                    })
            else:
                if (fee_line.fees_id.gender == 'both' or self.gender == fee_line.fees_id.gender) \
                    and (self.to_residential_type_id.id in fee_line.fees_id.residential_type_ids.ids) \
                    and (self.medium_id.id in fee_line.fees_id.medium_ids.ids):
                    if fee_line.fees_id.is_course_fee:
                         
                        course_fee_total = 0.0; course_fee_paid_total = 0.0
                        for line in fee_collection_id.fees_collection_line:
                            if line.name.is_course_fee_component:
                                course_fee_total += line.amount
                                course_fee_paid_total += line.total_paid + line.res_adj_amt                
                
                        collection_line = fee_collection_id.fees_collection_line.create({
                            'collection_id': fee_collection_id.id,
                            'name': fee_line.fees_id.id,
                            'amount': course_fee_total,
                            'total_paid': course_fee_paid_total,
                            'due_amount': course_fee_total - course_fee_paid_total,
                            'term_state': 'due',
                            'enquiry_id': self.pappaya_student_id.admission_id.id,
                            'res_adj_amt': 0.0,
                            'gst_total': course_fee_total , #self.res_comm_amount - gst_total,
                            'sgst': 0.0,
                            'cgst': 0.0,
                            'less_sequence': fee_line.less_sequence,
                        })                     
        
                        ledger_id.fee_ledger_line.create({
                            'fee_line_id': collection_line.id,
                            'credit': collection_line.amount,
                            'concession_amount': collection_line.concession_amount,
                            'concession_type_id': collection_line.concession_type_id.id,
                            'debit': collection_line.total_paid,
                            'balance': collection_line.amount - (collection_line.total_paid + collection_line.concession_amount),
                            'fees_ledger_id': ledger_id.id,
                            'res_adj_amt': collection_line.res_adj_amt,
                        })
                        
        cash_pay_id = self.env['pappaya.paymode'].search([('is_cash','=',True)])
        fee_collection_id.write({
            'pay_amount': self.amount_transferable,
            'payment_mode_id': cash_pay_id.id
            })
        if self.amount_transferable >= soa_amount:
            return fee_collection_id.fee_pay()
        else:
            return True          

    @api.multi
    def transfer_request(self):
        self.state = 'request'

    @api.multi
    def transfer_approve(self):
        self.state = 'approve'
        
    @api.multi
    def transfer_reject(self):
        self.state = 'rejected'
    
    @api.multi
    def transfer_transfered(self):
        if self.course_package_id and self.from_course_package_id:
            if self.transfer_type == 'internal':
                if self.transfer_type =='internal' and (self.from_course_package_id.id == self.course_package_id.id and self.from_residential_type_id.id == self.to_residential_type_id.id):
                    raise ValidationError("For internal transfer From CGBP and To CGBP should not be same.")
                
                fee_structure_id = self.env['pappaya.fees.structure'].search([('course_id','=',self.course_package_id.course_id.id),
                                                                              ('group_id','=',self.course_package_id.group_id.id),
                                                                              ('batch_id','=',self.course_package_id.batch_id.id),
                                                                              ('package_id','=',self.course_package_id.package_id.id),
                                                                              ('school_id','=',self.school_id.id),
                                                                              ('academic_year_id','=',self.academic_year_id.id),
                                                                              ('residential_type_id','=', self.to_residential_type_id.id)])                
            elif self.transfer_type == 'external':
                if self.transfer_type =='external' and self.from_course_id and self.course_id and not (self.from_course_id.id == self.course_id.id):
                    raise ValidationError("For External Transfer From Course and To Course should be same.")
                fee_structure_id = self.env['pappaya.fees.structure'].search([('course_id','=',self.course_package_id.course_id.id),
                                                                              ('group_id','=',self.course_package_id.group_id.id),
                                                                              ('batch_id','=',self.course_package_id.batch_id.id),
                                                                              ('package_id','=',self.course_package_id.package_id.id),
                                                                              ('school_id','=',self.for_branch_id.id),
                                                                              ('academic_year_id','=',self.academic_year_id.id),
                                                                              ('residential_type_id','=', self.to_residential_type_id.id)])
            if fee_structure_id:
                self.update_fee_collection(fee_structure_id)
                self.state = 'transfered'
        
#     @api.multi
#     def unlink(self):
#         raise ValidationError('Sorry, Transfer record can not be deleted.')
