# Copyright 2011 Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2012-2013 Guewen Baconnier (Camptocamp)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from datetime import datetime

class HrandPayrollUpdate(models.TransientModel):
    _name = "hr.and.payroll.update"
    _description = "hr.and.payroll.update"
    
    
    branch_id = fields.Many2many('res.company',string='Branch Name')


    
    @api.multi
    def action_update(self):
        for record in self:
            for employee in self.env['hr.employee'].search([('active','=',True)]):
                employee.onchange_branch_id()
            
            
            #for branch in self.env['operating.unit'].search([('type','=','branch')]):
                
#                 hours = []
#                 hours.append((0,0,{'branch_id':branch.id,'work_type':'8 Hours','total_work_hours':8,'start_time':09.00,'end_time':06.00,'start_duration':'am','end_duration':'pm'}))
#                 hours.append((0,0,{'branch_id':branch.id,'work_type':'9 Hours','total_work_hours':9,'start_time':09.00,'end_time':07.00,'start_duration':'am','end_duration':'pm'}))
#                 hours.append((0,0,{'is_any_9hours':True,'branch_id':branch.id,'work_type':'Is Any 9 Hours','total_work_hours':9,'start_time':09.00,'end_time':07.00,'start_duration':'am','end_duration':'pm'}))
#                 print (branch,"22333333333333333333")
#                 branch.worked_hours_line = hours
                
#                 segment = []
#                 segment.append((0,0,{'academic_year_id':28,
#                                 'programme_id':17,
#                                 'segment_id':7,
#                                 'course_package_ids':[(6, 0, [1,2])]
#                                 }))
#                 segment.append((0,0,{'academic_year_id':28,
#                                 'programme_id':17,
#                                 'segment_id':8,
#                                 'course_package_ids':[(6, 0, [1,2])]
#                                 }))
#                 segment.append((0,0,{'academic_year_id':28,
#                                 'programme_id':17,
#                                 'segment_id':9,
#                                 'course_package_ids':[(6, 0, [1,2])]
#                                 }))
#                 segment.append((0,0,{'academic_year_id':28,
#                                 'programme_id':17,
#                                 'segment_id':10,
#                                 'course_package_ids':[(6, 0, [1,2])]
#                                 }))
                
                
                #branch.write({'segment_cource_mapping_ids':segment})
            
#             employee_all_sr = None
#             if record.branch_id:
#                 employee_all_sr = self.env['hr.employee'].search([('branch_id','in',record.branch_id.ids)])
#             else:
#                 employee_all_sr = self.env['hr.employee'].search([('branch_id','!=',False)])
#             count = 0
#             for employee in employee_all_sr:
#                 
#                 count += 1
#                 print (employee.id,"EMployeee",count)
#                 
#                 date_of_joining = None
#                 if employee.date_of_joining: 
#                     date_of_joining = datetime.strptime(employee.date_of_joining, "%Y-%m-%d").date()
#                 else:
#                     date_of_joining = datetime.today().date()
#                     date_of_joining = date_of_joining.replace(day=15,month=1),
#                 gross_salary = None
#                 if employee.gross_salary:
#                     gross_salary = employee.gross_salary
#                 else:
#                     gross_salary = 30000
#                 
#                 employee.write({
#                                 'gross_salary': gross_salary,
#                                 'company_id':employee.branch_id.id,
#                                 'date_of_joining': date_of_joining,
#                                 'emp_work_hours': employee.branch_id.worked_hours_line[0].id,
#                                 'employee_type':4
#                                 })
#                 print (employee.gross_salary, employee.date_of_joining,"111111111111111")
#                 contract = self.env['hr.contract'].search([('employee_id','=',employee.id),('state','=','open')])
#                 if not contract:
#                     employee.job_id.write({'company_id':employee.branch_id.id,'department_id':employee.department_id.id,'salary_struct':2})
#                     employee.job_id.department_id.write({'company_id':employee.job_id.company_id.id})
#                     contract_vals = {
#                                         'name':'Contract for ' + employee.name and employee.name.title(),
#                                         'employee_id':employee.id,
#                                         'department_id':employee.department_id.id,
#                                         'job_id':employee.job_id.id,
#                                         'date_start':date_of_joining,
#                                         'wage':employee.gross_salary,
#                                         'company_id':employee.branch_id.id,
#                                         'type_id':4,
#                                         'state':'open',
#                                         'struct_id':2
#                                         }
#                     if contract_vals:
#                         contract = self.env['hr.contract'].create(contract_vals)
        return True
