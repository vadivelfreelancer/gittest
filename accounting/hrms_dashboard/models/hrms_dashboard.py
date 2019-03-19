# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Aswani PC, Saritha Sahadevan (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd
from odoo import models, fields, api, _
from odoo.http import request
from odoo.tools import float_utils


class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_user_employee_details(self):
        uid = request.session.uid
        employee = self.env['hr.employee'].search([('user_id', '=', uid)], limit=1)

        today = datetime.strftime(datetime.today(), '%Y-%m-%d')
        sql = """update hr_payslip_line set total=0.0 where total < 0"""
        self.env.cr.execute(sql)
        query = """ select count(id)
                    from hr_holidays
                    WHERE (hr_holidays.date_from <= '%s' and hr_holidays.date_to >= '%s') and type='remove' 
                    and  state='validate' """ % (today, today)
        cr = self._cr
        cr.execute(query)
        leaves_today = cr.fetchall()

        first_day = date.today().replace(day=1)
        last_day = (date.today() + relativedelta(months=1, day=1)) - timedelta(1)
        query = """ select count(id)
                    from hr_holidays
                    WHERE (hr_holidays.date_from <= '%s' and hr_holidays.date_to >= '%s') and type='remove' 
                    and  state='validate' """ % (last_day, first_day)
        cr = self._cr
        cr.execute(query)
        leaves_this_month = cr.fetchall()

        leaves_alloc_req = self.env['hr.holidays'].sudo().search_count([('state', 'in', ['confirm', 'validate1']),
                                                                        ('type', '=', 'add')])

        job_applications = self.env['hr.applicant'].sudo().search_count([('short_list', '=', True)])

        if employee:
            if employee.birthday:
                diff = relativedelta(datetime.today(), datetime.strptime(employee.birthday, '%Y-%m-%d'))
                age = diff.years
            else:
                age = False

            if employee.date_of_joining:
                diff = relativedelta(datetime.today(), datetime.strptime(employee.date_of_joining, '%Y-%m-%d'))
                years = diff.years
                months = diff.months
                days = diff.days
                experience = '{} years {} months {} days'.format(years, months, days)
            else:
                experience = False

            if employee:
                data = {
                    'employee_count':employee.employee_count,
                    'payslip_count':employee.payslip_amount,
                    'recruitment_count':employee.recruitment_count,
                    'leaves_today': leaves_today,
                    'leaves_this_month':leaves_this_month,
                    'leaves_alloc_req': leaves_alloc_req,
                    'job_applications': job_applications,
                    'experience': experience,
                    'age': age
                }
            return data
        else:
            return False

    @api.model
    def get_upcoming(self):
        cr = self._cr
        uid = request.session.uid

        employee = self.env['hr.employee'].search([('user_id', '=', uid)], limit=1)
        department = employee.department_id
        job_id = employee.job_id

        cr.execute("""select *, 
        (to_char(dob,'ddd')::int-to_char(now(),'ddd')::int+total_days)%total_days as dif
        from (select he.id, he.name, to_char(he.birthday, 'Month dd') as birthday,
        hj.name as job_id , he.birthday as dob,
        (to_char((to_char(now(),'yyyy')||'-12-31')::date,'ddd')::int) as total_days
        FROM hr_employee he
        join hr_job hj
        on hj.id = he.job_id
        ) birth
        where (to_char(dob,'ddd')::int-to_char(now(),'DDD')::int+total_days)%total_days between 0 and 15
        order by dif;""")
        birthday = cr.fetchall()

        cr.execute("""select e.name, e.date_begin, e.date_end, rc.name as location , e.is_online 
        from event_event e
        left join res_partner rp
        on e.address_id = rp.id
        left join res_country rc
        on rc.id = rp.country_id
        where state ='confirm'
        and (e.date_begin >= now()
        and e.date_begin <= now() + interval '15 day')
        or (e.date_end >= now()
        and e.date_end <= now() + interval '15 day')
        order by e.date_begin """)
        event = cr.fetchall()

        return {
            'birthday': birthday,
            'event': event,
        }

    @api.model
    def get_dept_employee(self):
        cr = self._cr
        cr.execute(
            'select department_id, hr_department.name,count(*) from hr_employee join hr_department on hr_department.id=hr_employee.department_id where hr_employee.active = true group by hr_employee.department_id,hr_department.name order by count desc limit 10')
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][1], 'value': dat[i][2]})
        return data

    @api.model
    def get_branch_student(self):
        cr = self._cr
        cr.execute(
            'select school_id, operating_unit.name,count(*) from res_partner join operating_unit on operating_unit.id=res_partner.school_id where res_partner.active = true group by res_partner.school_id,operating_unit.name order by count desc limit 10')
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][1], 'value': dat[i][2]})
        return data


    def get_work_days_dashboard(self, from_datetime, to_datetime, calendar=None):
        days_count = 0.0
        total_work_time = timedelta()
        calendar = calendar or self.resource_calendar_id
        for day_intervals in calendar._iter_work_intervals(
                from_datetime, to_datetime, self.resource_id.id,
                compute_leaves=False):
            theoric_hours = self.get_day_work_hours_count(day_intervals[0][0].date(), calendar=calendar)
            work_time = sum((interval[1] - interval[0] for interval in day_intervals), timedelta())
            total_work_time += work_time
            if theoric_hours:
                days_count += float_utils.round((work_time.total_seconds() / 3600 / theoric_hours) * 4) / 4
        return days_count
