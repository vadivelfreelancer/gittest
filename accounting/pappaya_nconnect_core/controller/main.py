from odoo import http
from odoo.exceptions import UserError
from odoo.addons.web.controllers.main import Session
from odoo.http import content_disposition, dispatch_rpc, request, \
    serialize_exception as _serialize_exception, Response
from odoo.tools.translate import _
import random


def throwError(msg):
    return {
        'response': 'fail',
        'error': {
            'message': msg
        }
    }


class nconnectSession(Session):
    @http.route('/web/session/nConnect/setPassword', type='json', auth='none')
    def setPassword(self, user_token, password):
        if not user_token or not password:
            return throwError("Both user token and password are mandatory!")

        user = request.env['res.users'].sudo().browse(user_token)
        if not user:
            return throwError("Invalid user!")
        vals = {'user_id': user_token, 'new_passwd': password}
        
        dialog = request.env['change.password.wizard'].create({
            'user_ids': [(0, 0, vals)]
        })
        dialog.sudo().change_password_button()

        user_info = user.read(['name', 'login', 'address'])
        return {
            'response': 'success',
            'name': user_info['name'],
            'mobile': user.parent_id.mobile,
            'email': user_info['login'],
            'Address': user_info['address'],
            'session_id': Session().authenticate(db=request.session.db, login=user_info['login'], password=password)
        }


    @http.route('/web/session/nConnect/download', type='json', auth='user')
    def getURL(self, model, field, dbid, filename):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not request.env[model].sudo().browse(dbid).read([field])[0][field]:
            return ""
        return base_url + "/web/content?model=%s&field=%s&id=%s&filename_field=%s" % (model, field, dbid, filename)


    @http.route('/web/session/nConnect/login', type='json', auth='none')
    def login(self, login, password):
        if not login or not password:
            return throwError("Both login and password are mandatory!")
        user = request.env['res.users'].sudo().search([('login', '=', login)])
        if not user:
            return throwError("Invalid login!")
        return Session().authenticate(db=request.session.db, login=login, password=password)['session_id']


    @http.route('/web/session/nConnect/registerParent', type='json', auth='none')
    def registerParent(self, student_id, reg_mobile):
        result = {'response': "success", 'login_status': []}
        if not student_id or not reg_mobile:
            return throwError("Both mobile number and student ids can not be empty!")
        parent_id = request.env['pappaya.parent'].sudo().search([('mobile', '=', reg_mobile)])
        if parent_id:
            if parent_id.user_id:
                return throwError("Already registered with this mobile number. Please go to login page.")
            child_student_ids = [child.student_id for child in parent_id.children_ids]
            for stud_id in student_id:
                if stud_id not in child_student_ids:
                    return throwError("Student ID - %s is not registered as your child in nConnect!" % (stud_id))

            user_parent = request.env['res.users'].sudo().create({
                'name': parent_id.name,
                'login': parent_id.email or (parent_id.name.lower().replace(" ", "") + "@nconnect.com"),
                'lang': 'en_US',
                'parent_id': parent_id.id
            })
            parent_id.user_id = user_parent.id

            # otp = str(int( random.randint(1001, 9999) + random.randint(100001, 999999) ))
            fcfs = student_id.pop(0)
            stud_fcfs_id = request.env['pappaya.student'].sudo().search([('student_id', '=', fcfs)])
            stud_fcfs_detail = {
                'status': True,
                'student_id': fcfs,
                'student_token': stud_fcfs_id.id,
                'Profile_image': Session().getURL(model='pappaya.student', field='image', 
                                                  dbid=stud_fcfs_id.id, filename='StudentImage_' + fcfs),
                "user_token": user_parent.id,
                "user_name": user_parent.login,
                "user_type": parent_id.parent_type,
                "Otp": "123" # int(str(otp)[0:7])
            }
            result['login_status'].append(stud_fcfs_detail)
            # Session().sendOTP(mobile_number, otp)

            for stud_id in student_id:
                vals = {
                    'status': True,
                    'student_id': stud_id,
                    'student_token': request.env['pappaya.student'].sudo().search([('student_id', '=', stud_id)], limit=1).id
                }
                result['login_status'].append(vals)
            return result
        else:
            return throwError("Not a registered Parent in nConnect!")


    @http.route('/web/session/nConnect/homeParent', type='json', auth='user')
    def homeParent(self, user_token, student_token):
        issues_count = len(request.env['pappaya.issue'].search([('student_id', '=', student_token)]))

        student = request.env['pappaya.student'].browse(student_token)
        student_profile = [{'student_name': student.name}]
        student_profile += [{
            'profile_image': Session().getURL('pappaya.student', 'image', student_token, "StudentImage_" + student.student_id)
            }]

        return {
            'response': 'success',
            'issues_count': issues_count,
            'student_profile': student_profile
        }


    @http.route('/web/session/nConnect/viewAttendance', type='json', auth='user')
    def viewAttendance(self, user_token, student_token, from_date, to_date):
        present_ids = request.env['pappaya.attendance'].search([('student_id', '=', student_token), ('is_present', '=', True)], order="date ASC")
        absent_ids = request.env['pappaya.attendance'].search([('student_id', '=', student_token), ('is_present', '=', False)], order="date ASC")

        return {
            'response': 'success',
            'present_dates': [p.date for p in present_ids],
            'absent_dates': [a.date for a in absent_ids]
        }
        

    @http.route('/web/session/nConnect/changePassword', type='json', auth='user')
    def changePassword(self, user_token, password, student_token=False):
        user = request.env['res.users'].sudo().browse(user_token)
        if not user:
            return throwError("Invalid user!")
        vals = {'user_id': user_token, 'new_passwd': password}
        
        dialog = request.env['change.password.wizard'].create({
            'user_ids': [(0, 0, vals)]
        })
        dialog.change_password_button()
        return {'response': 'success'}

    
    @http.route('/web/session/nConnect/profileRefresh', type='json', auth='user')
    def profileRefresh(self, user_token):
        user = request.env['res.users'].browse(user_token)
        response = {
            'response': "success",
            'name': user.name,
            'email': user.login
        }
        if user.parent_id:
            response.update({
                'mobile': user.parent_id.mobile,
                'Address': user.parent_id.address if user.parent_id.address else ""
            })
        return response





"""
********************* Trash *********************

    @http.route('/web/session/nConnect/registerParent', type='json', auth='none')
    def registerParent(self, mobile_number, student_ids):
        if not student_ids or not mobile_number:
            raise UserError(_("Both Mobile number and Student IDs can not be empty!"))
        parent_id = request.env['pappaya.parent'].sudo().search([('mobile', '=', mobile_number)])
        if parent_id:
            if parent_id.user_id:
                raise UserError(_("Already registered with this Mobile number."))
            child_student_ids = [child.student_id for child in parent_id.children_ids]
            children = parent_id.children_ids[0]
            for student_id in student_ids:
                if student_id not in child_student_ids:
                    raise UserError(_( "Student ID - %s is not registered as your child in nConnect!" % (student_id) ))   

            user_parent = request.env['res.users'].sudo().create({
                'name': parent_id.name,
                'login': parent_id.email or (parent_id.name.lower().replace(" ", "") + "@nconnect.com"),
                'company_id': children.school_id.id,
                'company_ids': [(6, 0, [children.school_id.id])],
                'lang': 'en_US'
            })
            parent_id.user_id = user_parent.id
            group_parent_id = request.env['ir.model.data'].sudo().get_object_reference('pappaya_nconnect_core', 'group_nconnect_parent')[-1]
            group_parent = request.env['res.groups'].sudo().browse(group_parent_id)
            group_parent.users = [(6, 0, group_parent.users.ids + [user_parent.id])]

            students_info = request.env['pappaya.student'].sudo().search_read([('student_id', 'in', child_student_ids)])
            otp_log = request.env['pappaya.nconnect.api'].sudo().create({
                'otp': 123,
                'response': json.dumps(students_info) if students_info else ""
            })

            return {
                'login': user_parent.login,
                'otp_log_id': otp_log.id
            }
        else:
            raise UserError(_("Student ID(s) not found in nConnect! Please contact Pappaya admin."))

    @http.route('/web/session/nConnect/confirmOTP', type='json', auth='none')
    def confirmOTP(self, otp_log_id, otp):
        print ("\n\n", otp_log_id, otp, "\n\n")
        if not otp_log_id or not otp:
            raise UserError(_("Both OTP log id and OTP are mandatory!"))
        otp_log = request.env['pappaya.nconnect.api'].sudo().browse(otp_log_id)

        if otp_log.otp_verify == True:
            raise UserError(_("Already verified!"))

        if otp_log.otp == otp:
            otp_log.otp_verify = True
            return json.loads(otp_log.response) if otp_log.response else ""
        else:
            raise UserError(_("Wrong OTP! Please try again!"))

********************* Trash *********************
"""