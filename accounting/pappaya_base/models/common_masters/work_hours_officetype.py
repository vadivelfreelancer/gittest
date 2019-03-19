# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PappayaWorkHoursOfficeType(models.Model):
    _name = 'work.hours.officetype'
    _rec_name = 'office_type_id'

    entity_id = fields.Many2one('operating.unit', 'Entity')
    employee_type = fields.Many2one('hr.contract.type', string='Type of Employment')
    office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    work_hours_line = fields.One2many('work.hours.officetype.line', 'work_hour_id', 'Work Hours Line')
    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')
    start_duration = fields.Selection([('am', 'AM'), ('pm', 'PM')], string='Start Duration', default='am')
    end_duration = fields.Selection([('am', 'AM'), ('pm', 'PM')], string='End Duration', default='pm')

    @api.onchange('office_type_id')
    def onchange_office_type_id(self):
        for record in self:
            if record.office_type_id:
                work_lines = []
                work_lines.append(
                    (0, 0, { 'status_type': 'present'}))
                work_lines.append(
                    (0, 0, {'status_type': 'partial'}))
                work_lines.append(
                    (0, 0, {'status_type': 'absent'}))
                record.work_hours_line = work_lines

    @api.constrains('office_type_id')
    def check_office_type_id(self):
        for record in self:
            if len(record.sudo().search([('office_type_id', '=', self.office_type_id.id),('employee_type','=',self.employee_type.id)]).ids) > 1:
                raise ValidationError("Work Hour configuration for given Office Type and Type of Employment already exists.")

    @api.constrains('start_time','end_time')
    def check_start_end_time(self):
        for record in self:
            if record.start_time and record.start_time > 12.0:
                raise ValidationError("Please enter valid Start Time.")
            if record.end_time and record.end_time > 12.0:
                raise ValidationError("Please enter valid End Time.")

    @api.model
    def create(self, vals):
        new_id = super(PappayaWorkHoursOfficeType, self).create(vals)
        self._update_work_hours_on_branches(new_id.office_type_id.id, new_id.id)
        return new_id

    @api.multi
    def write(self, vals):
        if 'entity_id' in vals or 'office_type_id' in vals or 'employee_type' in vals:
            raise ValidationError("You cannot change Entity, Office type and Type of Employment.")
        res = super(PappayaWorkHoursOfficeType, self).write(vals)
        self._update_work_hours_on_branches(self.office_type_id.id, self.id)
        return res
    
    @api.multi
    def unlink(self):
        raise ValidationError("You cannot remove workhours.")
        return super(PappayaWorkHoursOfficeType, self).unlink()
    
    def _update_work_hours_on_branches(self, office_type_id, work_hours_id):
        self._cr.execute("""
            CREATE OR REPLACE FUNCTION createBranchWorkHours( officeTypeID INTEGER, officeTypeWorkHoursID INTEGER ) RETURNS text AS $$
            DECLARE
            
                cur_branch RECORD;
                cur_work_hours_officetype  RECORD;
                cur_work_hours_officetype_line  RECORD;
                cur_branch_officetype_workhours_line  RECORD;
                branch_cursor CURSOR  (officeType INTEGER) FOR select id from operating_unit where type = 'branch' and office_type_id = officeType;
                officetype_line_cur CURSOR (parentID INTEGER) for select * from work_hours_officetype_line where work_hour_ID = parentID;
            BEGIN
            
                   
                select * from work_hours_officetype INTO cur_work_hours_officetype where id = officeTypeWorkHoursID ;
                OPEN branch_cursor (officeTypeID );
            
                    LOOP 
                        FETCH branch_cursor INTO cur_branch ;
                        -- exit when no more row to fetch
                        EXIT WHEN NOT FOUND;
                         
                        OPEN officetype_line_cur (officeTypeWorkHoursID  );
            
                        LOOP 
                                 FETCH officetype_line_cur INTO cur_work_hours_officetype_line;
                                 -- exit when no more row to fetch
                                 EXIT WHEN NOT FOUND;
                                 SELECT * from branch_officetype_workhours_line   INTO cur_branch_officetype_workhours_line  
                                        where branch_id = cur_branch.ID and status_type = cur_work_hours_officetype_line.status_type 
                                        and  employee_type = cur_work_hours_officetype.employee_type;
                                IF(cur_branch_officetype_workhours_line IS NOT NULL ) THEN
                                        IF (cur_branch_officetype_workhours_line.is_wrk_hrs_changed is FALSE )  THEN                      
                                            UPDATE branch_officetype_workhours_line   
                                            SET  
                                                    min_work_hours = cur_work_hours_officetype_line.min_work_hours, 
                                                    max_work_hours = cur_work_hours_officetype_line.max_work_hours,
                                                    start_time = cur_work_hours_officetype.start_time ,
                                                    end_time =cur_work_hours_officetype.end_time , 
                                                    start_duration=cur_work_hours_officetype.start_duration,
                                                    end_duration = cur_work_hours_officetype.end_duration
                                            where ID = cur_branch_officetype_workhours_line.ID;
            
                                        END IF;
                                ELSE
            
                                    INSERT INTO branch_officetype_workhours_line  
                                                ("id","branch_id","status_type","min_work_hours","max_work_hours",
                                                 "create_uid","create_date","write_uid","write_date","employee_type",
                                                 "start_time","end_time","start_duration","end_duration","work_hours_officetype",is_wrk_hrs_changed)
                                    VALUES (      nextval('branch_officetype_workhours_line_id_seq'::regclass),cur_branch.ID,
                                                  cur_work_hours_officetype_line.status_type,cur_work_hours_officetype_line.min_work_hours,
                                                  cur_work_hours_officetype_line.max_work_hours,1,now(),1,now(),
                                                   cur_work_hours_officetype.employee_type,cur_work_hours_officetype.start_time,
                                                   cur_work_hours_officetype.end_time,cur_work_hours_officetype.start_duration,
                                                   cur_work_hours_officetype.end_duration,cur_work_hours_officetype.ID,False);
                                END IF ;
            
            
                        END LOOP;
                         --close the officetype_line_cur.
                    CLOSE officetype_line_cur ;
                    END LOOP;
                   --close the branch_cursor.
                   CLOSE branch_cursor ;
             RETURN 0;
            END; $$ LANGUAGE PLPGSQL;        
        """)
        self._cr.execute("""select createBranchWorkHours(%s, %s);""",(office_type_id, work_hours_id))    
        return True
    
    
    
    

class PappayaWorkHoursOfficeTypeLine(models.Model):
    _name = 'work.hours.officetype.line'

    work_hour_id = fields.Many2one('work.hours.officetype', string='Budget ID')
    status_type = fields.Selection([('present', 'Present'), ('partial', 'Partial Present'), ('absent', 'Absent')], string='Status')
    min_work_hours = fields.Integer('Min. Work Hours')
    max_work_hours = fields.Integer('Max. Work Hours')


class BranchOfficeTypeWorkHoursLine(models.Model):
    _name = 'branch.officetype.workhours.line'

    employee_type = fields.Many2one('hr.contract.type', string='Type of Employment')
    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')
    start_duration = fields.Selection([('am', 'AM'), ('pm', 'PM')], string='Start Duration', default='am')
    end_duration = fields.Selection([('am', 'AM'), ('pm', 'PM')], string='End Duration', default='pm')
    work_hours_officetype = fields.Many2one('work.hours.officetype', 'Work Hours Office Type')
    

    branch_id = fields.Many2one('operating.unit',string='Branch',domain=[('type','=','branch')])
    status_type = fields.Selection([('present', 'Present'), ('partial', 'Partial Present'), ('absent', 'Absent')],string='Status')
    min_work_hours = fields.Integer('Min. Work Hours')
    max_work_hours = fields.Integer('Max. Work Hours')
    is_wrk_hrs_changed = fields.Boolean(string='Is Work hours changed at branch?', default=False)
    
    
    @api.multi
    def write(self, vals):
        if vals:
            vals.update({'is_wrk_hrs_changed':True})
        return super(BranchOfficeTypeWorkHoursLine, self).write(vals)
