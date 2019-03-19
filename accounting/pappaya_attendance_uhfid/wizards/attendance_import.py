# -*- coding: utf-8 -*-
###############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech-Receptives(<http://www.techreceptives.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, fields, api


class PappayaAllStudentWizard(models.TransientModel):
    _name = 'pappaya.all.student'

    course_id = fields.Many2one(
        'pappaya.course', 'Course',
        default=lambda self: self.env['pappaya.attendance.sheet'].browse(
            self.env.context['active_id']).register_id.course_id.id or False,
        readonly=True)
    batch_id = fields.Many2one(
        'pappaya.batch', 'Batch',
        default=lambda self: self.env['pappaya.attendance.sheet'].browse(
            self.env.context['active_id']).register_id.batch_id.id or False,
        readonly=True)
    student_ids = fields.Many2many('res.partner', string='Add Student(s)', domain=[('user_type','=','student')])

    @api.one
    def confirm_student(self):
        for sheet in self.env.context.get('active_ids', []):
            sheet_browse = self.env['pappaya.attendance.sheet'].browse(sheet)
            absent_list = [
                x.student_id for x in sheet_browse.attendance_line]
            all_student_search = self.env['pappaya.student'].search(
                [('course_id', '=', sheet_browse.register_id.course_id.id),
                 ('batch_id', '=', sheet_browse.register_id.batch_id.id),('user_type','=','student')]
            )
            all_student_search = list(
                set(all_student_search) - set(absent_list))
            for student_data in all_student_search:
                vals = {'student_id': student_data.id, 'present': True,
                        'attendance_id': sheet}
                if student_data.id in self.student_ids.ids:
                    vals.update({'present': False})
                self.env['pappaya.attendance.line'].create(vals)
