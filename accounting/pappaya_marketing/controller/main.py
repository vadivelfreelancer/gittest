import odoo
from odoo import http
from odoo.http import request
from odoo.api import Environment
from odoo import SUPERUSER_ID
from odoo.addons.web.controllers.main import ensure_db
import datetime
import json
import logging
# from openpyxl.pivot import record
from datetime import datetime
# from docutils.languages import fa
_logger = logging.getLogger(__name__)
from odoo.addons.web.controllers.main import Home,serialize_exception,content_disposition
from odoo.tools.translate import _
import base64

class Binary(http.Controller):
    """Common controller to download file"""
    
    @http.route('/web/binary/download_document', type='http', auth="public")
    @serialize_exception
    def download_document(self,model,field,id,filename=None, **kw):
        env = Environment(request.cr, SUPERUSER_ID, {})
        res = env[str(model)].search([('id','=',int(id))]).sudo().read()[0]
        filecontent = base64.b64decode(res.get(field) or '')
        if not filename:
            filename = '%s_%s' % (model.replace('.', '_'), id)
        if not filecontent:
            return request.not_found()
        return request.make_response(filecontent,
                [('Content-Type', 'application/octet-stream'),
                 ('Content-Disposition', content_disposition(filename))])

# class HomeExtend(Home):

#     @http.route('/web/login', type='http', auth="none", sitemap=False)
#     def web_login(self, redirect=None, **kw):
#         ensure_db()
#         request.params['login_success'] = False
#         if request.httprequest.method == 'GET' and redirect and request.session.uid:
#             return http.redirect_with_hash(redirect)
#         if not request.uid:
#             request.uid = odoo.SUPERUSER_ID
#         values = request.params.copy()
#         try:
#             values['databases'] = http.db_list()
#         except odoo.exceptions.AccessDenied:
#             values['databases'] = None
#         if request.httprequest.method == 'POST':
#             old_uid = request.uid
#             uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
#             if uid is not False:
#                 env = Environment(request.cr, SUPERUSER_ID, {})
#                 pro_user = False; pro_admin = False
#                 for i in env['res.groups'].search([('users','in',uid)]):
#                     if not uid == SUPERUSER_ID and i.name == 'PRO':
#                         pro_user = True
#                     if i.name == 'PRO ADMIN':
#                         pro_admin = True
#                         # Temp comments
# #                 if pro_user and not pro_admin:
# #                     request.session.logout()
# #                     values['error'] = "You are not an Application User."
# #                     response = request.render('web.login', values)
# #                     response.headers['X-Frame-Options'] = 'DENY'
# #                     return response                 
#                 request.params['login_success'] = True
#                 return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
#             request.uid = old_uid
#             values['error'] = _("Invalid User ID/Password")
#         else:
#             if 'error' in request.params and request.params.get('error') == 'access':
#                 values['error'] = _('Only employee can access this database. Please contact the administrator.')
#         if 'login' not in values and request.session.get('auth_login'):
#             values['login'] = request.session.get('auth_login')
#         if not odoo.tools.config['list_db']:
#             values['disable_database_manager'] = True
#         response = request.render('web.login', values)
#         response.headers['X-Frame-Options'] = 'DENY'
#         return response

class MobileController(http.Controller):

    @http.route('/mobile/rest/prologin', type='json', auth="none")
    def mob_login(self, redirect=None, **kw):
        ensure_db()
        request.params['status'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)
        if not request.uid:
            request.uid = odoo.SUPERUSER_ID
        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        if request.httprequest.method == 'POST':
            old_uid = request.uid
            env = Environment(request.cr, SUPERUSER_ID, {})
            user_br = env['res.users'].search([('login','=',request.params['login'])])
            log_uid = request.session.authenticate(request.session.db, request.params['login'],
                                                   request.params['password'])
            if log_uid is not False:
                request.params['status'] = True
                if user_br.login_date and user_br.mobile_user_login_status != 1:
                    user_br.write({'mobile_user_login_status':0})
                request.params['user_id'] = log_uid
                request.params['user_name'] = user_br.name or ''
                request.params['user_image'] = user_br.image or ''
                request.params['login_status'] = user_br.mobile_user_login_status
                for emp_obj in env['hr.employee'].search([('user_id','=',log_uid)]):
                    request.params['emp_db_id'] = emp_obj.id or ''
                    request.params['employee_id'] = emp_obj.emp_id or ''
                    request.params['employee_email'] = emp_obj.work_email or ''
                    request.params['employee_mobile'] = emp_obj.work_mobile or ''
                return request.params  # request.params #http.redirect_with_hash(redirect)
            request.uid = old_uid
            values['login_status'] = user_br.mobile_user_login_status
            if user_br.mobile_user_login_status == 2:
                values['error_msg'] = "Your credentials have been changed. Please contact Pro Admin."
                return values
            values['error_msg'] = "Invalid User ID/Password"
        return values
    
    @http.route('/mobile/rest/change_password', type='json', auth="none")
    def change_password(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {})
                new_password = False
                if 'new_password' in request.params:
                    new_password = request.params['new_password']
                if not new_password:
                    values['error_msg'] = "422 - Unprocessable Entity - New password is mandatory."
                    return values
                if env['res.users'].search([('login','=',request.params['login'])], limit=1):
                    env['res.users'].search([('login','=',request.params['login'])],limit=1).write({'mobile_user_login_status':0,'password': new_password})
                    values['status'] = "200 - Password has been changed successfully."
                    return values
            else:
                values['error_msg'] = "401 - Unauthorized - Invalid user name or password."
            return values
                
# Inputs
    @http.route('/mobile/rest/get_admission_branch_data', type='json', auth="none")
    def get_admission_branch_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                # valid_user is for mobile default logout functionality
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {}); branch_data = []
                user_id = env['res.users'].search([('login','=',request.params['login'])])
                employee_id = env['hr.employee'].search([('user_id','=',user_id.id)], limit=1)
                academic_year_id = env['academic.year'].search([('is_active','=',True)])
                for branch_obj in env['res.company'].search([('id','!=',1),('tem_state_id','=',employee_id.payroll_branch_id.state_id.id)], order='name asc'):
                    branch_data.append({'id':branch_obj.id, 'name':branch_obj.name})
                if branch_data:
                    request.params['branch_data'] = {'branch_data': branch_data}
                    request.params['status'] = "Branch data list has been fetched successfully."
                    return request.params
                else:
                    request.params['branch_data'] = {'branch_data': branch_data}
                    request.params['status'] = "Couldn't find any branch data for given employee."
                    return request.params
            else:
                values['valid_user'] = False
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values

    @http.route('/mobile/rest/get_pro_states', type='json', auth="none")
    def get_pro_states(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {}); state_data = []
                emp_db_id = request.params['emp_db_id']
                employee_obj = env['hr.employee'].search([('id','=',emp_db_id)])
                request.params['total_count'] = env['pappaya.lead.stud.address'].search_count([('employee_id','=',emp_db_id)])
                for state_obj in env['res.country.state'].search([('country_id','in',env['res.country'].search([('is_active','=',True)]).ids)]):
                        state_data.append({'id': state_obj.id, 'name': state_obj.name})
                if state_data:
                    request.params['states'] = {'state_data': state_data}
                    request.params['status'] = "Received state list successfully..!"
                    return request.params
                else:
                    request.params['states'] = {'state_data': state_data}
                    request.params['status'] = "Could not found any state list for current PRO."
                    return request.params
            else:
                values['valid_user'] = False
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_pro_districts', type='json', auth="none")
    def get_pro_districts(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {}); district_data = []
                state_id = request.params['state_id']
                for district_obj in env['state.district'].search([('state_id','=',state_id)]):
                    district_data.append({'id': district_obj.id, 'name': district_obj.name})
                if district_data:
                    request.params['districts'] = {'district_data': district_data}
                    request.params['status'] = "Received district list successfully..!"
                    return request.params
                else:
                    request.params['districts'] = {'district_data': district_data}
                    request.params['status'] = "Could not found any district list for given state."
                    return request.params
            else:
                values['valid_user'] = False
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_pro_cities', type='json', auth="none")
    def get_pro_cities(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {}); city_data = []
                district_id = request.params['district_id']
                for city_obj in env['pappaya.city'].search([('district_id','=',district_id)]):
                    city_data.append({'id': city_obj.id, 'name': city_obj.name})
                if city_data:
                    request.params['cities'] = {'city_data': city_data}
                    request.params['status'] = "Received city list successfully..!"
                    return request.params
                else:
                    request.params['cities'] = {'city_data': city_data}
                    request.params['status'] = "Could not found any city list for given district."
                    return request.params
            else:
                values['valid_user'] = False
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_pro_ward', type='json', auth="none")
    def get_pro_ward(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {}); ward_data = []
                city_id = request.params['city_id']
                for ward_obj in env['pappaya.ward'].search([('city_id','=',city_id)]):
                    ward_data.append({'id': ward_obj.id, 'name': ward_obj.name})
                if ward_data:
                    request.params['ward'] = {'ward_data': ward_data}
                    request.params['status'] = "Received city list successfully..!"
                    return request.params
                else:
                    request.params['ward'] = {'ward_data': ward_data}
                    request.params['status'] = "Could not found any ward list for given city."
                    return request.params
            else:
                values['valid_user'] = False
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_pro_area', type='json', auth="none")
    def get_pro_area(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {}); area_data = []
                ward_id = request.params['ward_id']
                for area_obj in env['pappaya.area'].search([('ward_id','=',ward_id)]):
                    area_data.append({'id': area_obj.id, 'name': area_obj.name})
                if area_data:
                    request.params['area'] = {'area_data': area_data}
                    request.params['status'] = "Received city list successfully..!"
                    return request.params
                else:
                    request.params['area'] = {'area_data': area_data}
                    request.params['status'] = "Could not found any area list for given ward."
                    return request.params
            else:
                values['valid_user'] = False
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_pro_mandal', type='json', auth="none")
    def get_pro_mandal(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {}); mandal_data = []
                district_id = request.params['district_id']
                for mandal_obj in env['pappaya.mandal.marketing'].search([('district_id','=',district_id)]):
                    mandal_data.append({'id': mandal_obj.id, 'name': mandal_obj.name})
                if mandal_data:
                    request.params['mandal'] = {'mandal_data': mandal_data}
                    request.params['status'] = "Received city list successfully..!"
                    return request.params
                else:
                    request.params['mandal'] = {'mandal_data': mandal_data}
                    request.params['status'] = "Could not found any mandal list for given district."
                    return request.params
            else:
                values['valid_user'] = False
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_pro_village', type='json', auth="none")
    def get_pro_village(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {}); village_data = []
                mandal_id = request.params['mandal_id']
                for village_obj in env['pappaya.village'].search([('mandal_id','=',mandal_id)]):
                    village_data.append({'id': village_obj.id, 'name': village_obj.name})
                if village_data:
                    request.params['village'] = {'village_data': village_data}
                    request.params['status'] = "Received city list successfully..!"
                    return request.params
                else:
                    request.params['village'] = {'village_data': village_data}
                    request.params['status'] = "Could not found any village list for given mandal."
                    return request.params
            else:
                values['valid_user'] = False
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_studying_course', type='json', auth="none")
    def get_studying_course(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {}); course_data = []
                for course_obj in env['pappaya.lead.course'].search([]):
                    course_data.append({'id': course_obj.id, 'name': course_obj.name})
                if course_data:
                    request.params['courses'] = {'course_data': course_data}
                    request.params['status'] = "Received course list successfully..!"
                    return request.params
                else:
                    request.params['courses'] = {'course_data': course_data}
                    request.params['status'] = "Could not found any course list.Please contact administrator."
                    return request.params
            else:
                values['valid_user'] = False
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_school_data', type='json', auth="none")
    def get_school_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {}); school_data = []
                mandal_id = False
                if 'mandal_id' in request.params:
                    mandal_id = request.params['mandal_id']
                    if not isinstance(mandal_id, int):
                        values['error_msg'] = "mandal Id should be integer."
                        return values
                    for school_obj in env['pappaya.lead.school'].search([('mandal_id','=',mandal_id)]):
                        school_data.append({'id': school_obj.id, 'name': school_obj.name})
                    if school_data:
                        request.params['schools'] = {'school_data': school_data}
                        request.params['status'] = "Received School list successfully..!"
                        return request.params
                    else:
                        request.params['schools'] = {'school_data': school_data}
                        request.params['status'] = "Could not found any School list.Please contact administrator."
                        return request.params
                else:
                    values['error_msg'] = "mandal_id is mandatory to get school list."
            else:
                values['valid_user'] = False
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
# End
    
    @http.route('/mobile/rest/create_lead', type='json', auth="none")
    def create_admission(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                request.params['valid_user'] = True
                env = Environment(request.cr, SUPERUSER_ID, {})
                lead_data_dict = {}
                if 'branch_id' in request.params:
                    lead_data_dict.update({'branch_id':request.params['branch_id']})
                if 'name' in request.params:
                    lead_data_dict.update({'name':request.params['name']})
                if 'lead_school_id' in request.params:
                    lead_data_dict.update({'studying_school_name':request.params['lead_school_id']})
                if 'father_name' in request.params:
                    lead_data_dict.update({'father_name':request.params['father_name']})
                if 'emp_db_id' in request.params:
                    lead_data_dict.update({'employee_id':request.params['emp_db_id']})
                if 'studying_course_id' in request.params:
                    lead_data_dict.update({'studying_course_id':request.params['studying_course_id']})
#                 if 'gender' in request.params:
#                     lead_data_dict.update({'gender':request.params['gender']})
                if 'state_id' in request.params:
                    lead_data_dict.update({'state_id':request.params['state_id']})
                if 'district_id' in request.params:
                    lead_data_dict.update({'district_id':request.params['district_id']})
                if 'city_id' in request.params:
                    lead_data_dict.update({'city':request.params['city_id']})
                if 'mandal_id' in request.params:
                    lead_data_dict.update({'mandal':request.params['mandal_id']})
                if 'location_type' in request.params:
                    lead_data_dict.update({'location_type':request.params['location_type']})
                if 'village_id' in request.params:
                    lead_data_dict.update({'village':request.params['village_id']})
                if 'ward_id' in request.params:
                    lead_data_dict.update({'ward':request.params['ward_id']})
                if 'area_id' in request.params:
                    lead_data_dict.update({'area':request.params['area_id']})
                if 'mobile' in request.params:
                    lead_data_dict.update({'mobile':request.params['mobile']})
                if 'pincode' in request.params:
                    lead_data_dict.update({'pincode':request.params['pincode']})
                    
#                 if 'school_state_id' in request.params:
#                     lead_data_dict.update({'school_state_id':request.params['school_state_id']})
#                 if 'school_district_id' in request.params:
#                     lead_data_dict.update({'school_district_id':request.params['school_district_id']})
#                 if 'school_mandal_id' in request.params:
#                     lead_data_dict.update({'school_mandal_id':request.params['school_mandal_id']})
                if env['pappaya.lead.stud.address'].search([('name','=',request.params['name']),('studying_course_id','=',request.params['studying_course_id']),('mobile','=',request.params['mobile'])]):
                    values['status_code'] = "422"
                    values['error_msg'] = "Record already exists."
                    return values
                try:
                    lead_creation = env['pappaya.lead.stud.address'].create(lead_data_dict)
                    if lead_creation:
                        values['status_code'] = "201"
                        values['sequence'] = lead_creation.sequence
                        values['status'] = "Lead is created successfully."
                        return values
                except:
                    request.cr.rollback()
                    values['status_code'] = "422"
                    values['status'] = "Lead is not created."
                    return values
            else:
                values['valid_user'] = False
                values['status_code'] = "422"
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Could not created lead.Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_student_count_by_state', type='json', auth="none")
    def get_student_count_by_state(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {})
                employee_id = request.params['emp_db_id'];
                state_ids = request.params['state_ids'];
                request.params['count'] = len(env['pappaya.lead.stud.address'].search([('employee_id','=',employee_id),('state_id','in',state_ids)]).ids)
                return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_district_list_by_states', type='json', auth="none")
    def get_district_list_by_states(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}); district_data = []
                state_ids = request.params['state_ids']
                for district_obj in env['state.district'].search([('state_id','in',state_ids)]):
                    district_data.append({'id': district_obj.id, 'name': district_obj.name})
                if district_data:
                    request.params['districts'] = {'district_data': district_data}
                    request.params['status'] = "Received district list successfully..!"
                    return request.params
                else:
                    request.params['districts'] = {'district_data': district_data}
                    request.params['status'] = "Could not found any district list for given state."
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_student_count_by_district', type='json', auth="none")
    def get_student_count(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {})
                employee_id = request.params['emp_db_id'];
                # state_ids = request.params['state_ids'];
                district_ids= request.params['district_ids'];
                request.params['count'] = len(env['pappaya.lead.stud.address'].search([('employee_id','=',employee_id),('district_id','in',district_ids)]).ids)
                return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_mandal_list_by_district', type='json', auth="none")
    def get_mandal_list_by_district(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}); mandal_data = []
                district_ids = request.params['district_ids']
                for mandal_obj in env['pappaya.mandal.marketing'].search([('district_id','in',district_ids)]):
                    mandal_data.append({'id': mandal_obj.id, 'name': mandal_obj.name})
                if mandal_data:
                    request.params['mandal'] = {'mandal_data': mandal_data}
                    request.params['status'] = "Received city list successfully..!"
                    return request.params
                else:
                    request.params['mandal'] = {'mandal_data': mandal_data}
                    request.params['status'] = "Could not found any mandal list for given district."
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_student_count_by_mandal', type='json', auth="none")
    def get_student_count_by_mandal(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {})
                employee_id = request.params['emp_db_id'];
                mandal_ids = request.params['mandal_ids'];
                request.params['count'] = len(env['pappaya.lead.stud.address'].search([('employee_id','=',employee_id), ('mandal_id','in',mandal_ids)]).ids)
                return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_village_list_by_mandal', type='json', auth="none")
    def get_village_list_by_mandal(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}); village_data = []
                mandal_ids = request.params['mandal_ids']
                for village_obj in env['pappaya.village'].search([('mandal_id','in',mandal_ids)]):
                    village_data.append({'id': village_obj.id, 'name': village_obj.name})
                if village_data:
                    request.params['village'] = {'village_data': village_data}
                    request.params['status'] = "Received city list successfully..!"
                    return request.params
                else:
                    request.params['village'] = {'village_data': village_data}
                    request.params['status'] = "Could not found any village list for given mandal."
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values    
    
    @http.route('/mobile/rest/get_student_count_by_village', type='json', auth="none")
    def get_student_count_by_village(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {})
                employee_id = request.params['emp_db_id'];
                village_ids = request.params['village_ids'];
                request.params['count'] = len(env['pappaya.lead.stud.address'].search([('employee_id','=',employee_id), ('village_id','in',village_ids)]).ids)
                return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_city_list_by_district', type='json', auth="none")
    def get_city_list_by_district(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}); city_data = []
                district_ids = request.params['district_ids']
                for city_obj in env['pappaya.city'].search([('district_id','in',district_ids)]):
                    city_data.append({'id': city_obj.id, 'name': city_obj.name})
                if city_data:
                    request.params['cities'] = {'city_data': city_data}
                    request.params['status'] = "Received city list successfully..!"
                    return request.params
                else:
                    request.params['cities'] = {'city_data': city_data}
                    request.params['status'] = "Could not found any city list for given district."
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_student_count_by_city', type='json', auth="none")
    def get_student_count_by_city(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {})
                employee_id = request.params['emp_db_id'];
                city_ids = request.params['city_ids'];
                request.params['count'] = len(env['pappaya.lead.stud.address'].search([('employee_id','=',employee_id), ('city_id','in',city_ids)]).ids)
                return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_ward_list_by_city', type='json', auth="none")
    def get_ward_list_by_city(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}); ward_data = []
                city_ids = request.params['city_ids']
                for ward_obj in env['pappaya.ward'].search([('city_id','in',city_ids)]):
                    ward_data.append({'id': ward_obj.id, 'name': ward_obj.name})
                if ward_data:
                    request.params['ward'] = {'ward_data': ward_data}
                    request.params['status'] = "Received city list successfully..!"
                    return request.params
                else:
                    request.params['ward'] = {'ward_data': ward_data}
                    request.params['status'] = "Could not found any ward list for given city."
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values    
    
    @http.route('/mobile/rest/get_student_count_by_ward', type='json', auth="none")
    def get_student_count_by_ward(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {})
                employee_id = request.params['emp_db_id'];
                ward_ids = request.params['ward_ids'];
                request.params['count'] = len(env['pappaya.lead.stud.address'].search([('employee_id','=',employee_id), ('ward_id','in',ward_ids)]).ids)
                return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_area_list_by_ward', type='json', auth="none")
    def get_area_list_by_ward(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}); area_data = []
                ward_ids = request.params['ward_ids']
                for area_obj in env['pappaya.area'].search([('ward_id','in',ward_ids)]):
                    area_data.append({'id': area_obj.id, 'name': area_obj.name})
                if area_data:
                    request.params['area'] = {'area_data': area_data}
                    request.params['status'] = "Received city list successfully..!"
                    return request.params
                else:
                    request.params['area'] = {'area_data': area_data}
                    request.params['status'] = "Could not found any area list for given ward."
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values    
    
    @http.route('/mobile/rest/get_student_count_by_area', type='json', auth="none")
    def get_student_count_by_area(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {})
                employee_id = request.params['emp_db_id'];
                area_ids = request.params['area_ids'];
                request.params['count'] = len(env['pappaya.lead.stud.address'].search([('employee_id','=',employee_id), ('area_id','in',area_ids)]).ids)
                return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    """Web Services for Mobile Offline sync"""
    
    """State Data"""
    
    @http.route('/mobile/rest/get_states_for_offline', type='json', auth="none")
    def get_states_for_offline(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}) 
                data_list = []
                total_records = env['res.country.state'].search([('country_id','in',env['res.country'].search([('is_active','=',True)]).ids)])
                request.params['total_count_server'] = len(total_records.ids)
                last_sync_obj = env['res.users'].search([('login','=',request.params['login'])])
                if last_sync_obj:
                    state_last_sync = last_sync_obj.state_last_sync 
                    if len(total_records.ids) != request.params['total_count']:
                        if not state_last_sync:
                            for state_obj in total_records:
                                data_dict = {}
                                data_dict.update({'id':state_obj.id})
                                if state_obj.name:
                                    data_dict.update({'name':state_obj.name})
                                if state_obj.sequence:
                                    data_dict.update({'sequence':state_obj.sequence})
                                data_list.append(data_dict)
                            request.params['all_records'] = True
                        elif state_last_sync:
                            total_rec_after_sync = env['res.country.state'].search([('country_id','in',env['res.country'].search([('is_active','=',True)]).ids),
                                                                                          '|', ('create_date','>',state_last_sync), ('write_date','>',state_last_sync)])
                            if len(total_records.ids) == (len(total_rec_after_sync.ids)+request.params['total_count']):
                                request.params['all_records'] = False
                                for state_obj in total_rec_after_sync:
                                    data_dict = {}
                                    data_dict.update({'id':state_obj.id})
                                    if state_obj.name:
                                        data_dict.update({'name':state_obj.name})
                                    if state_obj.sequence:
                                        data_dict.update({'sequence':state_obj.sequence})                                                                        
                                    data_list.append(data_dict)
                            else:
                                request.params['all_records'] = True
                                for state_obj in total_records:
                                    data_dict = {}
                                    data_dict.update({'id':state_obj.id})
                                    if state_obj.name:
                                        data_dict.update({'name':state_obj.name})
                                    if state_obj.sequence:
                                        data_dict.update({'sequence':state_obj.sequence})                                                                        
                                    data_list.append(data_dict)
                    # last_sync_obj.write({'state_last_sync':datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")})
                    request.params['last_sync_server'] = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
                if data_list:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Received state list successfully..!"
                    return request.params
                else:
                    request.params['data_list'] = {'state_data': data_list}
                    request.params['status'] = "Could not found any state list for current PRO."
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    """Lead Course Details"""
    
    @http.route('/mobile/rest/get_lead_course_for_offline', type='json', auth="none")
    def get_lead_course_for_offline(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}) 
                data_list = []
                total_records = env['pappaya.lead.course'].search([])
                request.params['total_count_server'] = len(total_records.ids)
                last_sync_obj = env['res.users'].search([('login','=',request.params['login'])])
                if last_sync_obj:
                    last_sync = last_sync_obj.lead_course_last_sync 
                    if len(total_records.ids) != request.params['total_count']:
                        if not last_sync:
                            for rec_obj in total_records:
                                data_list.append({'id': rec_obj.id, 'name': rec_obj.name})
                            request.params['all_records'] = True
                        elif last_sync:
                            total_rec_after_sync = env['pappaya.lead.course'].search(['|',('create_date','>',last_sync), ('write_date','>',last_sync)])
                            if len(total_records.ids) == (len(total_rec_after_sync.ids)+request.params['total_count']):
                                request.params['all_records'] = False
                                for rec_obj in total_rec_after_sync:
                                    data_list.append({'id': rec_obj.id, 'name': rec_obj.name})
                            else:
                                request.params['all_records'] = True
                                for rec_obj in total_records:
                                    data_list.append({'id': rec_obj.id, 'name': rec_obj.name})
                    # last_sync_obj.write({'lead_course_last_sync':datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")})
                    request.params['last_sync_server'] = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
                if data_list:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Received Lead Course Data successfully..!"
                    return request.params
                else:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Could not found any Lead Course Data list for current PRO."
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    """Lead School"""
    @http.route('/mobile/rest/get_lead_school_for_offline', type='json', auth="none")
    def get_lead_school_for_offline(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}) 
                data_list = []
                total_records = env['pappaya.lead.school'].search([])
                request.params['total_count_server'] = len(total_records.ids)
                last_sync_obj = env['res.users'].search([('login','=',request.params['login'])])
                if last_sync_obj:
                    last_sync = last_sync_obj.lead_school_last_sync 
                    if len(total_records.ids) != request.params['total_count']:
                        if not last_sync:
                            for rec_obj in total_records:
                                data_dict = {}
                                data_dict.update({'id': rec_obj.id})
                                if rec_obj.name:
                                    data_dict.update({'name': rec_obj.name})
                                if rec_obj.state_id:
                                    data_dict.update({'state_id':rec_obj.state_id.id})
                                if rec_obj.district_id:
                                    data_dict.update({'district_id':rec_obj.district_id.id})
                                if rec_obj.mandal_id:
                                    data_dict.update({'mandal_id':rec_obj.mandal_id.id})
                                data_list.append(data_dict)
                            request.params['all_records'] = True
                        elif last_sync:
                            total_rec_after_sync = env['pappaya.lead.school'].search(['|',('create_date','>',last_sync), ('write_date','>',last_sync)])
                            if len(total_records.ids) == (len(total_rec_after_sync.ids)+request.params['total_count']):
                                request.params['all_records'] = False
                                for rec_obj in total_rec_after_sync:
                                    data_dict = {}
                                    data_dict.update({'id': rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name': rec_obj.name})
                                    if rec_obj.state_id:
                                        data_dict.update({'state_id':rec_obj.state_id.id})
                                    if rec_obj.district_id:
                                        data_dict.update({'district_id':rec_obj.district_id.id})
                                    if rec_obj.mandal_id:
                                        data_dict.update({'mandal_id':rec_obj.mandal_id.id})
                                    data_list.append(data_dict)
                            else:
                                request.params['all_records'] = True
                                for rec_obj in total_records:
                                    data_dict = {}
                                    data_dict.update({'id': rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name': rec_obj.name})
                                    if rec_obj.state_id:
                                        data_dict.update({'state_id':rec_obj.state_id.id})
                                    if rec_obj.district_id:
                                        data_dict.update({'district_id':rec_obj.district_id.id})
                                    if rec_obj.mandal_id:
                                        data_dict.update({'mandal_id':rec_obj.mandal_id.id})
                                    data_list.append(data_dict)
                    # last_sync_obj.write({'lead_school_last_sync':datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")})
                    request.params['last_sync_server'] = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
                if data_list:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Received Lead School Data successfully..!"
                    return request.params
                else:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Could not found any Lead School Data list for current PRO."
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values     
    
    """Districts"""
    
    @http.route('/mobile/rest/get_districts_for_offline', type='json', auth="none")
    def get_districts_for_offline(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}) 
                data_list = []
                total_records = env['state.district'].search([])
                request.params['total_count_server'] = len(total_records.ids)
                last_sync_obj = env['res.users'].search([('login','=',request.params['login'])])
                if last_sync_obj:
                    last_sync = last_sync_obj.district_last_sync 
                    if len(total_records.ids) != request.params['total_count']:
                        if not last_sync:
                            for rec_obj in total_records:
                                data_dict = {}
                                data_dict.update({'id':rec_obj.id})
                                if rec_obj.name:
                                    data_dict.update({'name':rec_obj.name})
                                if rec_obj.state_id:
                                    data_dict.update({'state_id':rec_obj.state_id.id})      
                                data_list.append(data_dict)
                            request.params['all_records'] = True
                        elif last_sync:
                            total_rec_after_sync = env['state.district'].search(['|',('create_date','>',last_sync), ('write_date','>',last_sync)])
                            if len(total_records.ids) == (len(total_rec_after_sync.ids)+request.params['total_count']):
                                request.params['all_records'] = False
                                for rec_obj in total_rec_after_sync:
                                    data_dict = {}
                                    data_dict.update({'id':rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name':rec_obj.name})
                                    if rec_obj.state_id:
                                        data_dict.update({'state_id':rec_obj.state_id.id})      
                                    data_list.append(data_dict)                                    
                            else:
                                request.params['all_records'] = True
                                for rec_obj in total_records:
                                    data_dict = {}
                                    data_dict.update({'id':rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name':rec_obj.name})
                                    if rec_obj.state_id:
                                        data_dict.update({'state_id':rec_obj.state_id.id})      
                                    data_list.append(data_dict)
                    # last_sync_obj.write({'district_last_sync':datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")})
                    request.params['last_sync_server'] = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
                if data_list:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Received District Data successfully..!"
                    return request.params
                else:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Could not found District Data"
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values    
    
    @http.route('/mobile/rest/get_city_for_offline', type='json', auth="none")
    def get_city_for_offline(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}) 
                data_list = []
                total_records = env['pappaya.city'].search([])
                request.params['total_count_server'] = len(total_records.ids)
                last_sync_obj = env['res.users'].search([('login','=',request.params['login'])])
                if last_sync_obj:
                    last_sync = last_sync_obj.city_last_sync 
                    if len(total_records.ids) != request.params['total_count']:
                        if not last_sync:
                            for rec_obj in total_records:
                                data_dict = {}
                                data_dict.update({'id':rec_obj.id})
                                if rec_obj.name:
                                    data_dict.update({'name':rec_obj.name})
                                if rec_obj.district_id:
                                    data_dict.update({'district_id':rec_obj.district_id.id})                       
                                data_list.append(data_dict)
                            request.params['all_records'] = True
                        elif last_sync:
                            total_rec_after_sync = env['pappaya.city'].search(['|',('create_date','>',last_sync), ('write_date','>',last_sync)])
                            if len(total_records.ids) == (len(total_rec_after_sync.ids)+request.params['total_count']):
                                request.params['all_records'] = False
                                for rec_obj in total_rec_after_sync: 
                                    data_dict = {}
                                    data_dict.update({'id':rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name':rec_obj.name})
                                    if rec_obj.district_id:
                                        data_dict.update({'district_id':rec_obj.district_id.id})                       
                                    data_list.append(data_dict)
                            else:
                                request.params['all_records'] = True
                                for rec_obj in total_records:
                                    data_dict = {}
                                    data_dict.update({'id':rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name':rec_obj.name})
                                    if rec_obj.district_id:
                                        data_dict.update({'district_id':rec_obj.district_id.id})                       
                                    data_list.append(data_dict)
                    # last_sync_obj.write({'city_last_sync':datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")})
                    request.params['last_sync_server'] = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
                if data_list:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Received city data successfully..!"
                    return request.params
                else:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Could not found any City Data"
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values    
    
    @http.route('/mobile/rest/get_ward_for_offline', type='json', auth="none")
    def get_ward_for_offline(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}) 
                data_list = []
                total_records = env['pappaya.ward'].search([])
                request.params['total_count_server'] = len(total_records.ids)
                last_sync_obj = env['res.users'].search([('login','=',request.params['login'])])
                if last_sync_obj:
                    last_sync = last_sync_obj.ward_last_sync
                    if len(total_records.ids) != request.params['total_count']:
                        if not last_sync:
                            for rec_obj in total_records:
                                data_dict = {}
                                data_dict.update({'id': rec_obj.id})
                                if rec_obj.name:
                                    data_dict.update({'name': rec_obj.name})
                                if rec_obj.city_id:
                                    data_dict.update({'city_id':rec_obj.city_id.id})
                                data_list.append(data_dict)
                            request.params['all_records'] = True
                        elif last_sync:
                            total_rec_after_sync = env['pappaya.ward'].search(['|',('create_date','>',last_sync), ('write_date','>',last_sync)])
                            if len(total_records.ids) == (len(total_rec_after_sync.ids)+request.params['total_count']):
                                request.params['all_records'] = False
                                for rec_obj in total_rec_after_sync:
                                    data_dict = {}
                                    data_dict.update({'id': rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name': rec_obj.name})
                                    if rec_obj.city_id:
                                        data_dict.update({'city_id':rec_obj.city_id.id})
                                    data_list.append(data_dict)
                            else:
                                request.params['all_records'] = True
                                for rec_obj in total_records:
                                    data_dict = {}
                                    data_dict.update({'id': rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name': rec_obj.name})
                                    if rec_obj.city_id:
                                        data_dict.update({'city_id':rec_obj.city_id.id})
                                    data_list.append(data_dict)
                    # last_sync_obj.write({'ward_last_sync':datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")})
                    request.params['last_sync_server'] = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
                if data_list:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Received city data successfully..!"
                    return request.params
                else:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Could not found any City Data"
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values     
    
    @http.route('/mobile/rest/get_ward_area_for_offline', type='json', auth="none")
    def get_ward_area_for_offline(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}) 
                data_list = []
                total_records = env['pappaya.area'].search([])
                request.params['total_count_server'] = len(total_records.ids)
                last_sync_obj = env['res.users'].search([('login','=',request.params['login'])])
                if last_sync_obj:
                    last_sync = last_sync_obj.ward_area_last_sync 
                    if len(total_records.ids) != request.params['total_count']:
                        if not last_sync:
                            for rec_obj in total_records:
                                data_dict = {}
                                data_dict.update({'id': rec_obj.id})
                                if rec_obj.name:
                                    data_dict.update({'name': rec_obj.name})
                                if rec_obj.ward_id:
                                    data_dict.update({'ward_id':rec_obj.ward_id.id})
                                data_list.append(data_dict)
                            request.params['all_records'] = True
                        elif last_sync:
                            total_rec_after_sync = env['pappaya.area'].search(['|',('create_date','>',last_sync), ('write_date','>',last_sync)])
                            if len(total_records.ids) == (len(total_rec_after_sync.ids)+request.params['total_count']):
                                request.params['all_records'] = False
                                for rec_obj in total_rec_after_sync:
                                    data_dict = {}
                                    data_dict.update({'id': rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name': rec_obj.name})
                                    if rec_obj.ward_id:
                                        data_dict.update({'ward_id':rec_obj.ward_id.id})
                                    data_list.append(data_dict)
                            else:
                                request.params['all_records'] = True
                                for rec_obj in total_records:
                                    data_dict = {}
                                    data_dict.update({'id': rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name': rec_obj.name})
                                    if rec_obj.ward_id:
                                        data_dict.update({'ward_id':rec_obj.ward_id.id})
                                    data_list.append(data_dict)
                    # last_sync_obj.write({'ward_area_last_sync':datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")})
                    request.params['last_sync_server'] = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
                if data_list:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Received Area data successfully..!"
                    return request.params
                else:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Could not found any Area Data"
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values     
    
    @http.route('/mobile/rest/get_mandal_for_offline', type='json', auth="none")
    def get_mandal_for_offline(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}) 
                data_list = []
                total_records = env['pappaya.mandal.marketing'].search([])
                request.params['total_count_server'] = len(total_records.ids)
                last_sync_obj = env['res.users'].search([('login','=',request.params['login'])])
                if last_sync_obj:
                    last_sync = last_sync_obj.mandal_last_sync 
                    if len(total_records.ids) != request.params['total_count']:
                        if not last_sync:
                            for rec_obj in total_records:
                                data_dict = {}
                                data_dict.update({'id': rec_obj.id})
                                if rec_obj.name:
                                    data_dict.update({'name': rec_obj.name})
                                if rec_obj.district_id:
                                    data_dict.update({'district_id':rec_obj.district_id.id})
                                data_list.append(data_dict)
                            request.params['all_records'] = True
                        elif last_sync:
                            total_rec_after_sync = env['pappaya.mandal.marketing'].search(['|',('create_date','>',last_sync), ('write_date','>',last_sync)])
                            if len(total_records.ids) == (len(total_rec_after_sync.ids)+request.params['total_count']):
                                request.params['all_records'] = False
                                for rec_obj in total_rec_after_sync:
                                    data_dict = {}
                                    data_dict.update({'id': rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name': rec_obj.name})
                                    if rec_obj.district_id:
                                        data_dict.update({'district_id':rec_obj.district_id.id})
                                    data_list.append(data_dict)
                            else:
                                request.params['all_records'] = True
                                for rec_obj in total_records:
                                    data_dict = {}
                                    data_dict.update({'id': rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name': rec_obj.name})
                                    if rec_obj.district_id:
                                        data_dict.update({'district_id':rec_obj.district_id.id})
                                    data_list.append(data_dict)
                    # last_sync_obj.write({'mandal_last_sync':datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")})
                    request.params['last_sync_server'] = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
                if data_list:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Received Mandal data successfully..!"
                    return request.params
                else:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Could not found any Mandal Data"
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values    
    
    @http.route('/mobile/rest/get_village_for_offline', type='json', auth="none")
    def get_village_for_offline(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}) 
                data_list = []
                total_records = env['pappaya.village'].search([])
                request.params['total_count_server'] = len(total_records.ids)
                last_sync_obj = env['res.users'].search([('login','=',request.params['login'])])
                if last_sync_obj:
                    last_sync = last_sync_obj.village_last_sync 
                    if len(total_records.ids) != request.params['total_count']:
                        if not last_sync:
                            for rec_obj in total_records:
                                data_dict = {}
                                data_dict.update({'id': rec_obj.id})
                                if rec_obj.name:
                                    data_dict.update({'name': rec_obj.name})
                                if rec_obj.mandal_id:
                                    data_dict.update({'mandal_id':rec_obj.mandal_id.id})
                                data_list.append(data_dict)
                            request.params['all_records'] = True
                        elif last_sync:
                            total_rec_after_sync = env['pappaya.village'].search(['|',('create_date','>',last_sync), ('write_date','>',last_sync)])
                            if len(total_records.ids) == (len(total_rec_after_sync.ids)+request.params['total_count']):
                                request.params['all_records'] = False
                                for rec_obj in total_rec_after_sync:
                                    data_dict = {}
                                    data_dict.update({'id': rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name': rec_obj.name})
                                    if rec_obj.mandal_id:
                                        data_dict.update({'mandal_id':rec_obj.mandal_id.id})
                                    data_list.append(data_dict)                                    
                            else:
                                request.params['all_records'] = True
                                for rec_obj in total_records:
                                    data_dict = {}
                                    data_dict.update({'id': rec_obj.id})
                                    if rec_obj.name:
                                        data_dict.update({'name': rec_obj.name})
                                    if rec_obj.mandal_id:
                                        data_dict.update({'mandal_id':rec_obj.mandal_id.id})
                                    data_list.append(data_dict)
                    # last_sync_obj.write({'village_last_sync':datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")})
                    request.params['last_sync_server'] = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
                if data_list:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Received Village data successfully..!"
                    return request.params
                else:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Could not found any Village Data"
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values
    
    @http.route('/mobile/rest/get_branch_for_offline', type='json', auth="none")
    def get_branch_for_offline(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            log_uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if log_uid:
                env = Environment(request.cr, SUPERUSER_ID, {}); branch_data = []
                data_list = []
                user_id = env['res.users'].search([('login','=',request.params['login'])])
                employee_id = env['hr.employee'].search([('user_id','=',user_id.id)], limit=1)
                academic_year_id = env['academic.year'].search([('is_active','=',True)])
                total_records = env['res.company'].search([('id','!=',1),('tem_state_id','=',employee_id.payroll_branch_id.state_id.id)])
                last_sync_obj = env['res.users'].search([('login','=',request.params['login'])])
                if last_sync_obj:
                    last_sync = last_sync_obj.branch_last_sync
                    if len(total_records.ids) != request.params['total_count']:
                        for rec_obj in total_records:
                            data_dict = {}
                            data_dict.update({'id': rec_obj.id})
                            if rec_obj.name:
                                data_dict.update({'name': rec_obj.name})
                            if rec_obj.branch_type:
                                data_dict.update({'branch_type':rec_obj.branch_type})
                            if rec_obj.tem_state_id:
                                data_dict.update({'state_id':rec_obj.tem_state_id.id})
                            data_list.append(data_dict)
                        request.params['all_records'] = True
                    # last_sync_obj.write({'branch_last_sync':datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")})
                    request.params['last_sync_server'] = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
                if data_list:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Received  Branch data successfully..!"
                    return request.params
                else:
                    request.params['data_list'] = {'data_list': data_list}
                    request.params['status'] = "Could not found any Branch Data"
                    return request.params
            else:
                values['error_msg'] = "Invalid Login";
        else:
            values['error_msg'] = "Please check POST method."
        return values

    
    ''' Web Service for create/Update from .net application. '''
    
    """ Method to validate authentication with Pro security code """
    def _validate_authentication(self):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        if 'secretKey' not in request.params:
            values['error_msg'] = "401 - Unauthorized - Secret key is missing"
            return values
        if env['res.users'].browse(SUPERUSER_ID).pro_security_code != request.params['secretKey']:
            values['error_msg'] = "401 - Unauthorized - Invalid secret key."
            _logger.info("ERROR MSG: 401 - Unauthorized - Invalid secret key.")
            return values
        return True
    
    """method to check duplication record with record_id(which is given by .net team)"""
    def _check_record_id_duplication(self, model_name, record_id):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        if model_name and record_id:
            if not isinstance(record_id, int):
                values['error_msg'] = "422 - Unprocessable Entity - recordId should be integer."
                return values                
            if env[model_name].search([('record_id','=',record_id)]).ids:
                values['error_msg'] = "422 - duplicate entry - Record already exists with given recordId."
                _logger.info("422 - duplicate entry - Record already exists with given recordId.")
                return values
            if model_name == 'hr.employee':
                if env[model_name].search([('record_id','=',record_id),'|',('active','=',True),('active','=',False)]).ids:
                    values['error_msg'] = "422 - duplicate entry - Record already exists with given recordId."
                    return values
        return True
    
    """method to check record existance with given id"""
    def _check_record_existance(self, model_name, record_id):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        if model_name and record_id:
            if not isinstance(record_id, int):
                message = ''
                if model_name == 'res.country.state':
                    message = "stateId should be Integer"
                elif model_name == 'state.district':
                    message = "districtId should be Integer"
                elif model_name == 'pappaya.city':
                    message = "cityId should be integer"
                elif model_name == 'pappaya.ward':
                    message = "wardId should be integer"
                elif model_name == 'pappaya.area':
                    message = "areaId should be integer"                    
                elif model_name == 'pappaya.mandal.marketing':
                    message = "mandalId should be integer"
                elif model_name == 'pappaya.village':
                    message = "villageId should be integer"
                elif model_name == 'pappaya.lead.school':
                    message = "schoolId should be integer"
                elif model_name == 'pappaya.lead.course':
                    message = "courseId should be integer"
                elif model_name == 'hr.job':
                    message = "jobId should be integer"
                elif model_name == 'hr.employee':
                    message = "employeeId should be integer"
                elif model_name == 'pappaya.payroll.branch':
                    message = "payrollBranchId should be integer."
                elif model_name == 'pappaya.office.type':
                    message = "OfficeTypeId should be integer"
                values['error_msg'] = "422 - Unprocessable Entity - "+message
                return values
            if not env[model_name].search([('record_id','=',record_id)]):
                message = ''
                if model_name == 'res.country.state':
                    message = "No state record is found for given id"
                elif model_name == 'state.district':
                    message = "No district record is found for given id"
                elif model_name == 'pappaya.city':
                    message = "No city record is found for given id"
                elif model_name == 'pappaya.ward':
                    message = "No ward record is found for given id"
                elif model_name == 'pappaya.area':
                    message = "No area record is found for given id"                    
                elif model_name == 'pappaya.mandal.marketing':
                    message = "No mandal record is found for given id"
                elif model_name == 'pappaya.village':
                    message = "No village record is found for given id"
                elif model_name == 'pappaya.lead.school':
                    message = "No school record is found for given id"
                elif model_name == 'pappaya.lead.course':
                    message = "No course record is found for given id"
                elif model_name == 'hr.job':
                    message = "No Job Position record is found for given id"
                elif model_name == 'hr.employee':
                    message = "No Employee record is found for given id"
                elif model_name == 'pappaya.payroll.branch':
                    message = "No Payroll Branch record is found for given id"
                elif model_name == 'pappaya.office.type':
                    message = "No Office Type record is found for given id"
                values['error_msg'] = "404 - Not Found - "+message
                return values
        return True
    
    """Method to get object to write"""
    def get_object_to_write(self, model_name, record_id):
        env = Environment(request.cr, SUPERUSER_ID, {})
        if model_name and record_id:
            if env[model_name].search([('record_id','=',record_id)], limit=1):
                return env[model_name].search([('record_id','=',record_id)], limit=1)
            else:
                return False
        else:
            return False
    """Method to get database Id based on given recordId"""
    def get_db_id(self, model_name, record_id):
        env = Environment(request.cr, SUPERUSER_ID, {})
        if model_name and record_id:
            return env[model_name].search([('record_id','=',record_id)]).id
        return False
    
    @http.route('/api/v1/get_country_data', type='json', auth="none")
    def get_country_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {}); 
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            country_data = []
            for country_obj in env['res.country'].search([('is_active','=',True)]):
                country_data.append({'id': country_obj.id, 'name': country_obj.name})
            if country_data:
                request.params['country_data'] = {'country_data': country_data}
                request.params['status'] = "201 - OK - coutry data has been fetched successfully."
                return request.params
            else:
                request.params['country_data'] = {'country_data': country_data}
                request.params['status'] = "Could not found active country data."
                return request.params
        return values
    
    """Service to create state record"""
    
    @http.route('/api/v1/add_state_data', type='json', auth="none", cors='*')
    def add_state_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            state_name =''; state_code=''; country_id='';sequence='';record_id=''
            if 'stateName' in request.params:
                state_name = request.params['stateName']
            if 'stateCode' in request.params:
                state_code = request.params['stateCode']
            if 'countryId' in request.params:
                if not isinstance(request.params['countryId'], int):
                    values['error_msg'] = "422 - Unprocessable Entity - countryId should be mandatory."
                    return values
                if not env['res.country'].search([('id','=',request.params['countryId'])]):
                    values['error_msg'] = "404 - Not Found - No record found for given countryId"
                    return values
                country_id = request.params['countryId']
            if 'sequence' in request.params:
                sequence = request.params['sequence']
            if 'recordId' in request.params:
                if self._check_record_id_duplication('res.country.state', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('res.country.state', request.params['recordId'])
                record_id = request.params['recordId']
            if state_name and state_code and country_id and record_id:
                if env['res.country.state'].search([('code','=',state_code),('country_id','=',country_id)]):
                    values['error_msg'] = "422 - Duplicate Entry - Record exists. The code of the state must be unique by country."
                    return values
                try:
                    env['res.country.state'].create({'name':state_name, 'code':state_code, 'country_id':country_id,'sequence':sequence,'record_id':record_id})
                    values['status'] = "201 – OK – New state record hcityas been created"
                    return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = '422 - Unprocessable Entity - Please check given input.'
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - stateName,stateCode,countryId and recordId are mandatory to create state record."
            return values
    
    """Controller to update State record"""
    
    @http.route('/api/v1/update_state_data', type='json', auth="none", cors='*')
    def update_state_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            state_obj = False
            dict_to_modify = {}
            if 'recordId' in request.params:
                if self._check_record_existance('res.country.state', request.params['recordId']) is not True:
                    return self._check_record_existance('res.country.state', request.params['recordId'])
                state_obj = self.get_object_to_write('res.country.state', request.params['recordId'])
            if 'stateName' in request.params:
                state_name = request.params['stateName']              
                dict_to_modify.update({'name':state_name})
            if 'stateCode' in request.params and 'countryId' in request.params:
                if not isinstance(request.params['countryId'], int):
                    values['error_msg'] = "422 - Unprocessable Entity - countryId should be mandatory."
                    return values
                if not env['res.country'].search([('id','=',request.params['countryId'])]):
                    values['error_msg'] = "404 - Not Found - No record found for given countryId"
                    return values
                if env['res.country.state'].search([('code','=',request.params['stateCode']),('country_id','=',request.params['countryId'])]):
                    values['error_msg'] = "422 - Duplicate Entry - Record exists. The code of the state must be unique by country."
                    return values
                dict_to_modify.update({'code':request.params['stateCode'],'country_id':request.params['countryId'] })
            if 'sequence' in request.params:
                dict_to_modify.update({'sequence':request.params['sequence']})
            if state_obj and dict_to_modify:
                try:
                    record_modified = state_obj.write(dict_to_modify)
                    if record_modified:
                        values['status'] = "200 - OK - Eyerything is working - Given data has been successfully changed."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."    
            return values
    
    """Service to create new city record"""
    
    @http.route('/api/v1/add_city_data', type='json', auth="none", cors='*')
    def add_city_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            # checking for authentication.
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            record_id = False; city_name = False; district_id = False;state_id = False
            if 'recordId' in request.params:
                if self._check_record_id_duplication('pappaya.city', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('pappaya.city', request.params['recordId'])
                record_id = request.params['recordId']
            if 'cityName' in request.params:
                city_name = request.params['cityName']
            if 'districtId' in request.params:
                # checking for given districtId is exists are not
                if self._check_record_existance('state.district', request.params['districtId']) is not True:
                    return self._check_record_existance('state.district', request.params['districtId'])
                district_id = self.get_db_id('state.district', request.params['districtId'])
            if district_id:
                state_id = env['state.district'].search([('id','=',district_id)]).state_id.id if env['state.district'].search([('id','=',district_id)]) else False
            if record_id and city_name and district_id:
                existing_rec = env['pappaya.city'].search([('name','=',city_name),('district_id','=',district_id)])
                if existing_rec:
                    values['error_msg'] = "422 - Duplicate Entry - Couldn't create. already city record exists with given city (%s) and district(%s)"%(existing_rec.name, existing_rec.district_id.name)
                    _logger.info("422 - Duplicate Entry - Couldn't create. already city record exists with given city (%s) and district(%s)"%(existing_rec.name, existing_rec.district_id.name))
                    return values
                try:
                    city_creation = env['pappaya.city'].create({'name': city_name, 'district_id':district_id, 'state_id':state_id, 'record_id':record_id})
                    if city_creation:
                        values['status'] = "201 – OK – New city record has been created"
                        _logger.info("201 – OK – New city record has been created")
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Couldn't create please check params."
                    return values
            else:
                values['error_msg'] = "422 - Unprocessable Entity - recordId, cityName and districtId are mandatory to create city record."
        return values    
    
    """API controller to modify city data"""
        
    @http.route('/api/v1/update_city_data', type='json', auth="none", cors='*')
    def update_city_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            dict_to_modify = {};district_id=False
            city_obj = False
            domain_condition = []
            if 'recordId' in request.params:
                if self._check_record_existance('pappaya.city', request.params['recordId']) is not True:
                    return self._check_record_existance('pappaya.city', request.params['recordId'])
                city_obj = self.get_object_to_write('pappaya.city', request.params['recordId'])                    
            if 'cityName' in request.params:
                dict_to_modify.update({'name':request.params['cityName']})
                domain_condition.append(('name','=',request.params['cityName']))
            if 'districtId' in request.params:
                if self._check_record_existance('state.district', request.params['districtId']) is not True:
                    return self._check_record_existance('state.district', request.params['districtId'])    
                domain_condition.append(('district_id','=',self.get_db_id('state.district', request.params['districtId'])))
                district_id = self.get_db_id('state.district', request.params['districtId'])
                dict_to_modify.update({'district_id':self.get_db_id('state.district', request.params['districtId'])})
            if district_id:
                state_id = env['state.district'].search([('id','=',district_id)]).state_id.id if env['state.district'].search([('id','=',district_id)]) else False
                dict_to_modify.update({'state_id':state_id})
            if domain_condition:
                if env['pappaya.city'].search(domain_condition):
                    values['error_msg'] = "422 - Duplicate Entry - record alredy exists with gievn cityName."
                    return values
            if city_obj and dict_to_modify:
                try:
                    record_updated = city_obj.write(dict_to_modify)
                    if record_updated:
                        values['status'] = "200 - OK - Eyerything is working - given data has been modified successfully."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values   
        
    """Studying Course"""
    
    @http.route('/api/v1/add_lead_course_data', type='json', auth="none", cors='*')
    def add_lead_course_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            course_name = ''; description=''; record_id = False
            domain_condition = []
            if 'courseName' in request.params:
                course_name = request.params['courseName']
                domain_condition.append(('name','=',request.params['courseName']))
            if 'description' in request.params:
                description = request.params['description']
            if 'recordId' in request.params:
                if self._check_record_id_duplication('pappaya.lead.course', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('pappaya.lead.course', request.params['recordId'])
                record_id = request.params['recordId']                
            if domain_condition:
                if env['pappaya.lead.course'].search(domain_condition):
                    values['error_msg'] = "422 - Duplicate Entry - Couldn't create. already record exists with given course name"
                    return values
            if record_id and course_name:
                try:
                    new_id = env['pappaya.lead.course'].create({'name':course_name, 'description':description, 'record_id':record_id})
                    if new_id:
                        values['status'] = "201 – OK – New Lead course record has been created"
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please Check given input."
            return values
        
    """Method to update lead course master record"""
    
    @http.route('/api/v1/update_lead_course_data', type='json', auth="none", cors='*')
    def update_lead_course_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            course_obj = False
            dict_to_modify = {}
            if 'recordId' in request.params:
                if self._check_record_existance('pappaya.lead.course', request.params['recordId']) is not True:
                    return self._check_record_existance('pappaya.lead.course', request.params['recordId'])   
                record_id = request.params['recordId']
                course_obj = self.get_object_to_write('pappaya.lead.course', record_id)
            if 'courseName' in request.params and 'recordId' in request.params:
                course_name = request.params['courseName']
                if env['pappaya.lead.course'].search([('id','!=',course_obj.id),('name','=',course_name)]):
                    values['error_msg'] = "422 - Duplicate Entry - record exists with given course name"
                    return values
                dict_to_modify.update({'name':course_name})
            if 'description' in request.params:
                description = request.params['description']
                dict_to_modify.update({'description':description}) 
            if course_obj and dict_to_modify:
                try:
                    record_id_changed = course_obj.write(dict_to_modify)
                    if record_id_changed:
                        values['status'] = "200 - OK - Eyerything is working - Given data has been successfully changed."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check input."
        return values
    
    """State District"""
    
    @http.route('/api/v1/add_state_district_data', type='json', auth="none", cors='*')
    def add_state_district_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            district_name = ''; code=''; state_id= ''; record_id=''
            if 'districtName' in request.params:
                district_name = request.params['districtName'] 
            if 'code' in request.params:
                code = request.params['code']
                existing_rec = env['state.district'].search([('code','=',code)])
                if existing_rec:
                    values['error_msg'] = "422 – Unprocessable Entity - Already district ( %s ) data exists with gievn code. code should be unique."%(existing_rec.name)
                    _logger.info("422 – Unprocessable Entity - Already district data exists with gievn code. code should be unique.")
                    return values    
            if 'stateId' in request.params and isinstance(request.params['stateId'], int):
                if self._check_record_existance('res.country.state', request.params['stateId']) is not True:
                    return self._check_record_existance('res.country.state', request.params['stateId'])
                state_id = self.get_db_id('res.country.state', request.params['stateId'])
            if 'recordId' in request.params:
                if self._check_record_id_duplication('state.district', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('state.district', request.params['recordId'])
                record_id = request.params['recordId']
            if district_name and code and state_id and record_id:
                try:
                    district_creation = env['state.district'].create({'name': district_name, 'code':code, 'state_id': state_id,'record_id':record_id})
                    if district_creation:
                        values['status'] = "201 – OK – New state district record has been created"
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values
    
    """Update district data""" 

    @http.route('/api/v1/update_state_district_data', type='json', auth="none", cors='*')
    def update_state_district_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            district_obj = False; record_id = False
            dict_to_modify = {}
            district_name = ''; code = ''; state_id = ''
            if 'recordId' in request.params:
                if self._check_record_existance('state.district', request.params['recordId']) is not True:
                    return self._check_record_existance('pappaya.lead.course', request.params['recordId'])  
                record_id = request.params['recordId']
                district_obj = self.get_object_to_write('state.district', record_id)
            if 'districtName' in request.params:
                district_name = request.params['districtName']
                dict_to_modify.update({'name': district_name})
            if 'code' in request.params and 'recordId' in request.params:
                code = request.params['code']
                existing_rec = env['state.district'].search([('record_id','!=',record_id),('code','=',code)])
                if existing_rec:
                    values['error_msg'] = "422 – Unprocessable Entity - Already district ( %s ) data exists with gievn code. code should be unique."%(existing_rec.name)
                    _logger.info("422 – Unprocessable Entity - Already district ( %s ) data exists with gievn code. code should be unique."%(existing_rec.name))
                    return values
                dict_to_modify.update({'code':code})      
            if 'stateId' in request.params:
                if self._check_record_existance('res.country.state', request.params['stateId']) is not True:
                    return self._check_record_existance('res.country.state', request.params['stateId'])
                state_id = self.get_db_id('res.country.state', request.params['stateId'])                
                dict_to_modify.update({'state_id':state_id})
            if district_obj and dict_to_modify:
                try:
                    record_modified = district_obj.write(dict_to_modify)
                    if record_modified:
                        values['status'] = "200 - OK - Eyerything is working - Given data has been changed."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values
    
    """ Create  Ward Data """
    
    @http.route('/api/v1/add_ward_data', type='json', auth="none", cors='*')
    def add_ward_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            ward_name = ''; city_id = '';record_id='';state_id='';district_id=''
            if 'wardName' in request.params:
                ward_name = request.params['wardName']
            if 'cityId' in request.params:
                if self._check_record_existance('pappaya.city', request.params['cityId']) is not True:
                    return self._check_record_existance('pappaya.city', request.params['cityId'])
                city_id = self.get_db_id('pappaya.city', request.params['cityId'])
            if city_id:
                city_obj = env['pappaya.city'].search([('id','=',city_id)])
                district_id = city_obj.district_id.id
                state_id = city_obj.district_id.state_id.id
            if 'recordId' in request.params:
                if self._check_record_id_duplication('pappaya.ward', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('pappaya.ward', request.params['recordId'])
                record_id = request.params['recordId']
            if ward_name and city_id and record_id and district_id and state_id:
                try:
                    ward_creation = env['pappaya.ward'].create({'name': ward_name, 'state_id':state_id, 'district_id':district_id, 'city_id':city_id, 'record_id':record_id})
                    if ward_creation:
                        values['status'] = "201 – OK – New Ward record has been created"
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values
    
    @http.route('/api/v1/update_ward_data', type='json', auth="none", cors='*')
    def update_ward_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            ward_obj = False
            dict_to_modify = {}
            if 'recordId' in request.params:
                if self._check_record_existance('pappaya.ward', request.params['recordId']) is not True:
                    return self._check_record_existance('pappaya.ward', request.params['recordId'])
                record_id = request.params['recordId']
                ward_obj = self.get_object_to_write('pappaya.ward', record_id)
            ward_name = ''; city_id = ''
            if 'wardName' in request.params:
                ward_name = request.params['wardName']
                dict_to_modify.update({'name':ward_name})
            if 'cityId' in request.params:
                if self._check_record_existance('pappaya.city', request.params['cityId']) is not True:
                    return self._check_record_existance('pappaya.city', request.params['cityId'])                
                city_id = self.get_db_id('pappaya.city',request.params['cityId'])
                dict_to_modify.update({'city_id':city_id})
            if city_id:
                city_obj = env['pappaya.city'].search([('id','=',city_id)])
                district_id = city_obj.district_id.id
                state_id = city_obj.district_id.state_id.id
                dict_to_modify.update({'district_id':district_id, 'state_id':state_id})
            if ward_obj and dict_to_modify:
                try:
                    record_modified = ward_obj.write(dict_to_modify)
                    if record_modified:
                        values['status'] = "200 - OK - Eyerything is working - Given data has been successfully changed."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
    
    """ Area Data Creation """
    
    @http.route('/api/v1/add_area_data', type='json', auth="none", cors='*')
    def add_area_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            area_name = ''; ward_id = ''; record_id = '';state_id='';district_id='';city_id=''
            if 'areaName' in request.params:
                area_name = request.params['areaName']
            if 'wardId' in request.params:
                if self._check_record_existance('pappaya.ward', request.params['wardId']) is not True:
                    return self._check_record_existance('pappaya.ward', request.params['wardId']) 
                ward_id = self.get_db_id('pappaya.ward', request.params['wardId'])
            if ward_id:
                ward_obj = env['pappaya.ward'].search([('id','=',ward_id)])
                city_id = ward_obj.city_id.id
                district_id = ward_obj.city_id.district_id.id
                state_id = ward_obj.city_id.district_id.state_id.id
            if 'recordId' in request.params:
                if self._check_record_id_duplication('pappaya.area', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('pappaya.area', request.params['recordId'])    
                record_id = request.params['recordId']
            if area_name and state_id and district_id and city_id and ward_id and record_id:
                try:
                    area_creation = env['pappaya.area'].create({'name': area_name, 'state_id':state_id,'district_id':district_id,'city_id':city_id,
                                                    'ward_id':ward_id, 'record_id':record_id})
                    if area_creation:
                        values['status'] = "201 – OK – New Area record has been created"
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values  
    
    @http.route('/api/v1/update_area_data', type='json', auth="none", cors='*')
    def update_area_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()        
            area_obj = False
            dict_to_modify = {}
            if 'recordId' in request.params:
                if self._check_record_existance('pappaya.area', request.params['recordId']) is not True:
                    return self._check_record_existance('pappaya.area', request.params['recordId'])
                record_id = request.params['recordId']
                area_obj = self.get_object_to_write('pappaya.area', record_id)    
            area_name = ''; ward_id = ''
            if 'areaName' in request.params:
                area_name = request.params['areaName']               
                dict_to_modify.update({'name':area_name})
            if 'wardId' in request.params:
                if self._check_record_existance('pappaya.ward', request.params['wardId']) is not True:
                    return self._check_record_existance('pappaya.ward', request.params['wardId']) 
                ward_id = self.get_db_id('pappaya.ward', request.params['wardId'])
                dict_to_modify.update({'ward_id':ward_id})
            if ward_id:
                ward_obj = env['pappaya.ward'].search([('id','=',ward_id)])
                city_id = ward_obj.city_id.id
                district_id = ward_obj.city_id.district_id.id
                state_id = ward_obj.city_id.district_id.state_id.id            
                dict_to_modify.update({'city_id':city_id, 'district_id':district_id, 'state_id':state_id})
            if area_obj and dict_to_modify:
                try:
                    area_updated = area_obj.write(dict_to_modify)
                    if area_updated:
                        values['Status'] = "200 - OK - Eyerything is working - Given data hase been modified successfully."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values     

    """ Creating Mandal Mrketing """
    
    @http.route('/api/v1/add_mandal_data', type='json', auth="none", cors='*')
    def add_mandal_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            mandal_name = ''; district_id = False;record_id='';state_id=False
            if 'mandalName' in request.params:
                mandal_name = request.params['mandalName']
            if 'districtId' in request.params:
                if self._check_record_existance('state.district', request.params['districtId']) is not True:
                    return self._check_record_existance('state.district', request.params['districtId'])                    
                district_id = self.get_db_id('state.district', request.params['districtId'])
            if district_id:
                district_obj = env['state.district'].search([('id','=',district_id)])
                state_id = district_obj.state_id.id
            if 'recordId' in request.params:
                if self._check_record_id_duplication('pappaya.mandal.marketing', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('pappaya.mandal.marketing', request.params['recordId'])                   
                record_id = request.params['recordId']
            if mandal_name and district_id:
                try:
                    mandal_creation = env['pappaya.mandal.marketing'].create({'name': mandal_name, 'state_id':state_id, 'district_id':district_id,'record_id':record_id})
                    if mandal_creation:
                        values['status'] = "201 – OK – New Mandal record has been created."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values    
    
    @http.route('/api/v1/update_mandal_data', type='json', auth="none", cors='*')
    def update_mandal_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})            
            mandal_obj = False
            dict_to_modify = {};district_id=False
            if 'recordId' in request.params:
                if self._check_record_existance('pappaya.mandal.marketing', request.params['recordId']) is not True:
                    return self._check_record_existance('pappaya.mandal.marketing', request.params['recordId'])
                mandal_obj = self.get_object_to_write('pappaya.mandal.marketing', request.params['recordId'])
            if 'mandalName' in request.params:
                mandal_name = request.params['mandalName']
                dict_to_modify.update({'name':mandal_name})
            if 'districtId' in request.params:
                if self._check_record_existance('state.district', request.params['districtId']) is not True:
                    return self._check_record_existance('state.district', request.params['districtId'])
                district_id = self.get_db_id('state.district', request.params['districtId'])
                dict_to_modify.update({'district_id':district_id})
            if district_id:
                district_obj = env['state.district'].search([('id','=',district_id)])
                dict_to_modify.update({'state_id':district_obj.state_id.id})
            if mandal_obj and dict_to_modify:
                try:
                    record_modified = mandal_obj.write(dict_to_modify)
                    if record_modified:
                        values['status'] = "200 - OK - Everything is working - given data has been modified successfully."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values    
    
    """ Creating Village Record """
    
    @http.route('/api/v1/add_village_data', type='json', auth="none", cors='*')
    def add_village_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            village_name = ''; mandal_id = '';record_id='';state_id=False;district_id=False
            if 'recordId' in request.params:
                if self._check_record_id_duplication('pappaya.village', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('pappaya.village', request.params['recordId'])
                record_id = request.params['recordId']
            if 'villageName' in request.params:
                village_name=request.params['villageName']
            if 'mandalId' in request.params:
                if self._check_record_existance('pappaya.mandal.marketing', request.params['mandalId']) is not True:
                    return self._check_record_existance('pappaya.mandal.marketing', request.params['mandalId'])                  
                mandal_id = self.get_db_id('pappaya.mandal.marketing', request.params['mandalId'])
            if mandal_id:
                mandal_obj = env['pappaya.mandal.marketing'].search([('id','=',mandal_id)])
                district_id = mandal_obj.district_id.id
                state_id = mandal_obj.district_id.state_id.id
            if  village_name and mandal_id:
                try:
                    village_creation = env['pappaya.village'].create({'name': village_name, 'state_id':state_id,'district_id':district_id,'mandal_id':mandal_id,'record_id':record_id})
                    if village_creation:
                        values['status'] = "201 - OK - New Village record has been created successfully."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values

    @http.route('/api/v1/update_village_data', type='json', auth="none", cors='*')
    def update_village_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            village_obj = False
            dict_to_modify = {}            
            if 'recordId' in request.params:
                if self._check_record_existance('pappaya.village', request.params['recordId']) is not True:
                    return self._check_record_existance('pappaya.village', request.params['recordId'])
                record_id = request.params['recordId']
                village_obj = self.get_object_to_write('pappaya.village', record_id)
            if 'villageName' in request.params:
                village_name = request.params['villageName']
                dict_to_modify.update({'name':village_name})
            if 'mandalId' in request.params:
                if self._check_record_existance('pappaya.mandal.marketing', request.params['mandalId']) is not True:
                    return self._check_record_existance('pappaya.mandal.marketing', request.params['mandalId'])                      
                mandal_id = self.get_db_id('pappaya.mandal.marketing',request.params['mandalId'])
                dict_to_modify.update({'mandal_id':mandal_id})
            if mandal_id:
                mandal_obj = env['pappaya.mandal.marketing'].search([('id','=',mandal_id)])
                district_id = mandal_obj.district_id.id
                state_id = mandal_obj.district_id.state_id.id
                dict_to_modify.update({'district_id':district_id,'state_id':state_id})
            if village_obj and dict_to_modify:
                try:
                    record_modified = village_obj.write(dict_to_modify)
                    if record_modified:
                        values['status'] = "200 - OK - Eyerything is working - Given data has been successfully changed."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values
        
    @http.route('/api/v1/add_lead_school_data', type='json', auth="none", cors='*')
    def add_lead_school_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()            
            school_name = ''; state_id=False; district_id = False; mandal_id = False;record_id=''
            if 'schoolName' in request.params:
                school_name = request.params['schoolName']
            if 'stateId' in request.params:
                if self._check_record_existance('res.country.state', request.params['stateId']) is not True:
                    return self._check_record_existance('res.country.state', request.params['stateId'])                  
                state_id = self.get_db_id('res.country.state',request.params['stateId'])
            if 'districtId' in request.params:
                if self._check_record_existance('state.district', request.params['districtId']) is not True:
                    return self._check_record_existance('state.district', request.params['districtId'])                  
                district_id = self.get_db_id('state.district',request.params['districtId'])                   
            if 'mandalId' in request.params:
                if self._check_record_existance('pappaya.mandal.marketing', request.params['mandalId']) is not True:
                    return self._check_record_existance('pappaya.mandal.marketing', request.params['mandalId'])                  
                mandal_id = self.get_db_id('pappaya.mandal.marketing',request.params['mandalId'])
            if 'recordId' in request.params:
                if self._check_record_id_duplication('pappaya.lead.school', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('pappaya.lead.school', request.params['recordId'])
                record_id = request.params['recordId']
            if record_id and school_name and state_id and district_id and mandal_id:
                try:
                    school_creation = env['pappaya.lead.school'].create({'name': school_name, 'state_id':state_id, 'district_id':district_id, 'mandal_id':mandal_id,
                                                                         'record_id':record_id})
                    if school_creation:
                        values['status'] = "201 – OK – New Lead School record has been created"
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
            return values
    
    @http.route('/api/v1/update_lead_school_data', type='json', auth="none", cors='*')
    def update_lead_school_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication() 
            lead_school_obj = False
            dict_to_modify = {}
            if 'recordId' in request.params:
                if self._check_record_existance('pappaya.lead.school', request.params['recordId']) is not True:
                    return self._check_record_existance('pappaya.lead.school', request.params['recordId'])                  
                lead_school_obj = self.get_object_to_write('pappaya.lead.school',request.params['recordId'])
            school_name = ''; state_id=False; district_id = False; mandal_id = False
            if 'schoolName' in request.params:
                school_name = request.params['schoolName']
                dict_to_modify.update({'name':school_name})
            if 'stateId' in request.params:
                if self._check_record_existance('res.country.state', request.params['stateId']) is not True:
                    return self._check_record_existance('res.country.state', request.params['stateId'])
                state_id = self.get_db_id('res.country.state', request.params['stateId'])
                dict_to_modify.update({'state_id':state_id})
            if 'districtId' in request.params:
                if self._check_record_existance('state.district', request.params['districtId']) is not True:
                    return self._check_record_existance('state.district', request.params['districtId'])
                district_id = self.get_db_id('state.district', request.params['districtId'])
                dict_to_modify.update({'district_id':district_id})
            if 'mandalId' in request.params:
                if self._check_record_existance('pappaya.mandal.marketing', request.params['mandalId']) is not True:
                    return self._check_record_existance('pappaya.mandal.marketing', request.params['mandalId'])
                mandal_id = self.get_db_id('pappaya.mandal.marketing', request.params['mandalId'])
                dict_to_modify.update({'mandal_id':mandal_id})
            if lead_school_obj and dict_to_modify:
                try:
                    record_modified = lead_school_obj.write(dict_to_modify)
                    if record_modified:
                        values['status'] = "200 - OK - Eyerything is working - Given data has been successfully changed."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unprocessable Entity - Please check given data."
            return values
        
    @http.route('/api/v1/add_hr_job_data', type='json', auth="none", cors='*')
    def add_hr_job_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication() 
            job_name = ''; description = '';record_id = False;employee_no=''
            if 'jobName' in request.params:
                job_name = request.params['jobName']
            if 'recordId' in request.params:
                if self._check_record_id_duplication('hr.job', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('hr.job', request.params['recordId'])
                record_id = request.params['recordId']
            if 'description' in request.params:
                description = request.params['description']
            if 'empNoRef' in request.params:
                employee_no = request.params['empNoRef']
            if job_name and record_id:
                if env['hr.job'].search([('name','=',job_name)]):
                    values['error_msg'] = "422 - Duplicate Entry - record already exists with given jobName"
                    return values
                try:
                    env['hr.job'].create({'name':job_name,'description':description, 'emp_no_ref':employee_no,'record_id':record_id})
                    values['status'] = "201 - OK - New Job position has been created successfully."
                    return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            else:
                values['error_msg'] = "422 - Unprocessable Entity - jobName and recordId are mandatory to create Job position."
                return values
            values['error_msg'] = "422 - Unproceesable Entity - Please check given params"
            return values
    
    @http.route('/api/v1/update_hr_job_data', type='json', auth="none", cors='*')
    def update_hr_job_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication() 
            job_name = ''; description = '';record_id = False
            dict_to_modify = {}
            job_obj = False
            if 'jobName' in request.params:
                job_name = request.params['jobName']
                if env['hr.job'].search([('name','=',job_name)]):
                    values['error_msg'] = "422 - Duplicate Entry - record already exists with given jobName"
                    return values
                dict_to_modify.update({'name':job_name})
            if 'description' in request.params:
                dict_to_modify.update({'description':description})
            if 'empNoRef' in request.params:
                dict_to_modify.update({'emp_no_ref': request.params['empNoRef']})
            if 'recordId' in request.params:
                if self._check_record_existance('hr.job', request.params['recordId']) is not True:
                    return self._check_record_existance('hr.job', request.params['recordId'])                  
                job_obj = self.get_object_to_write('hr.job',request.params['recordId'])
            if job_obj and dict_to_modify:
                try:
                    record_modified = job_obj.write(dict_to_modify)
                    if record_modified:
                        values['status'] = "200 - OK - Eyerything is working - Given data has been successfully changed."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unproceesable Entity - Please check given params"
            return values

    @http.route('/api/v1/add_branch_data', type='json', auth="none", cors='*')
    def add_branch_data(self, **kw):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        if request.httprequest.method == 'POST':
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            branch_name = ''; branch_type=''; state_id='';emp_no_ref='';record_id='';code='';mobile='';email='';district_id=False
            if 'recordId' in request.params:
                if self._check_record_id_duplication('res.company', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('res.company', request.params['recordId'])
                record_id = request.params['recordId']
            if 'branchName' in request.params:
                branch_name = request.params['branchName'].upper()
            if 'branchType' in request.params:
                branch_type = request.params['branchType']
            if 'stateId' in request.params:
                if self._check_record_existance('res.country.state', request.params['stateId']) is not True:
                    return self._check_record_existance('res.country.state', request.params['stateId'])
                state_id = self.get_db_id('res.country.state', request.params['stateId'])
            if 'empNoRef' in request.params:
                emp_no_ref = request.params['empNoRef']
            if 'code' in request.params:
                code = request.params['code']
            if 'mobile' in request.params:
                mobile = request.params['mobile']
            if 'email' in request.params:
                email = request.params['email']
            if 'districtId' in request.params:
                if self._check_record_existance('state.district', request.params['districtId']) is not True:
                    return self._check_record_existance('state.district', request.params['districtId'])
                district_id = self.get_db_id('state.district', request.params['districtId'])           
            if record_id and branch_name and branch_type and state_id:
                if env['res.company'].search([('name','=',branch_name),('branch_type','=',branch_type),('state_id','=',state_id)]):
                    values['error_msg'] = "422 - Duplicate Entry - Record exists for given input combination."
                    return values
                try:
                    branch_data_dict = {'type':'branch','name':branch_name,'branch_type':branch_type,'tem_state_id':state_id,'emp_no_ref':emp_no_ref, 'record_id':record_id}
                    if district_id:
                        branch_data_dict.update({'state_district_id':district_id})
                    if code:
                        branch_data_dict.update({'code':code})
                    if mobile:
                        branch_data_dict.update({'mobile':mobile})
                    if email:
                        branch_data_dict.update({'email':email})
                    branch_creation = env['res.company'].create(branch_data_dict)
                    if branch_creation:
                        values['status'] = "201 - OK - New branch record has been created successfully."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
                    return values
            else:
                values['error_msg'] = "422 - Unprocessable Entity - branchName, branchType, stateId and recordId are mandatory to create branch."
        values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
        return values
                        
    @http.route('/api/v1/update_branch_data', type='json', auth="none", cors='*')
    def update_branch_data(self, **kw):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        if request.httprequest.method == 'POST':
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            branch_obj = False
            data_to_update = {}
            if 'recordId' in request.params:
                if self._check_record_existance('res.company', request.params['recordId']) is not True:
                    return self._check_record_existance('res.company', request.params['recordId'])
                branch_obj = self.get_object_to_write('res.company', request.params['recordId'])
            if 'branchName' in request.params:
                data_to_update.update({'name':request.params['branchName']})
            if 'branchType' in request.params:
                data_to_update.update({'branch_type':request.params['branchType'].lower()})
            if 'stateId' in request.params:
                if self._check_record_existance('res.country.state', request.params['stateId']) is not True:
                    return self._check_record_existance('res.country.state', request.params['stateId'])
                state_id = self.get_db_id('res.country.state', request.params['stateId'])
                data_to_update.update({'tem_state_id':state_id})
            if 'empNoRef' in request.params:
                data_to_update.update({'emp_no_ref':request.params['empNoRef']})
            if 'code' in request.params:
                data_to_update.update({'code':request.params['code']})
            if 'mobile' in request.params:
                data_to_update.update({'mobile':request.params['mobile']})
            if 'email' in request.params:
                data_to_update.update({'email':request.params['email']})
            if 'districtId' in request.params:
                if self._check_record_existance('state.district', request.params['districtId']) is not True:
                    return self._check_record_existance('state.district', request.params['districtId'])
                district_id = self.get_db_id('state.district', request.params['districtId'])            
                branch_data_dict.update({'state_district_id':district_id})
            if branch_obj and data_to_update:
                try:
                    record_updated = branch_obj.write(data_to_update)
                    if record_updated:
                        values['status'] = "200 - OK - Eyerything is working - Given data has been successfully changed."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
                    return values
            else:
                values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
            return values
        
    @http.route('/api/v1/add_office_type_data', type='json', auth="none", cors='*')
    def add_office_type_data(self, **kw):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        if request.httprequest.method == 'POST':
            record_id = False;type_name='';description=''; code=''
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            if 'recordId' in request.params:
                if self._check_record_id_duplication('pappaya.office.type', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('pappaya.office.type', request.params['recordId'])
                record_id = request.params['recordId']
            if 'typeName' in request.params:
                type_name = request.params['typeName']
            if 'code' in request.params:
                code = request.params['code']                
            if 'description' in request.params:
                description = request.params['description']
            if record_id and type_name:
                if env['pappaya.office.type'].search([('name','=',type_name)]):
                    values['error_msg'] = "422 - Duplicate Entry - Record already exists"
                    return values
                try:
                    new_office_type = env['pappaya.office.type'].create({'name':type_name,'description':description,'code':code,'record_id':record_id})
                    if new_office_type:
                        values['status'] = "201 - OK - New Office Type record has been created successfully."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
                    return values
            else:
                values['error_msg'] = "422 - Unprocessable Entity - TypeName mandatory to create Office Type."
        values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
        return values                        
    
    @http.route('/api/v1/update_office_type_data', type='json', auth="none", cors='*')
    def update_office_type_data(self, **kw):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        dict_to_update = {}
        if request.httprequest.method == 'POST':
            type_name = ''
            office_type_obj = False
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            if 'recordId' in request.params:
                if self._check_record_existance('pappaya.office.type', request.params['recordId']) is not True:
                    return self._check_record_existance('pappaya.office.type', request.params['recordId'])
                office_type_obj = self.get_object_to_write('pappaya.office.type', request.params['recordId'])
            if 'typeName' in request.params:
                type_name = request.params['typeName']
                dict_to_update.update({'name':type_name})
            if 'code' in request.params:
                dict_to_update.update({'code':request.params['code']})
            if 'description' in request.params:
                description = request.params['description']
                dict_to_update.update({'description':description})
            if office_type_obj and dict_to_update:
                if type_name:
                    if env['pappaya.office.type'].search([('name','=',type_name)]):
                        values['error_msg'] = "422 - Duplicate Entry - Record already exists"
                        return values
                    try:
                        new_office_type = office_type_obj.write(dict_to_update)
                        if new_office_type:
                            values['status'] = "201 - OK - Given data has been successfully."
                            return values
                    except:
                        request.cr.rollback()
                        values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
                        return values
        values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
        return values    
    
    @http.route('/api/v1/add_payroll_branch_data', type='json', auth="none", cors='*')
    def add_payroll_branch_data(self, **kw):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        if request.httprequest.method == 'POST':
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            branch_name = ''; branch_type=''; state_id='';emp_no_ref='';record_id='';office_type_id=''
            if 'recordId' in request.params:
                if self._check_record_id_duplication('pappaya.payroll.branch', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('pappaya.payroll.branch', request.params['recordId'])
                record_id = request.params['recordId']
            if 'branchName' in request.params:
                branch_name = request.params['branchName']
            if 'officeTypeId' in request.params:
                if self._check_record_existance('pappaya.office.type', request.params['officeTypeId']) is not True:
                    return self._check_record_existance('pappaya.office.type', request.params['officeTypeId'])
                office_type_id = self.get_db_id('pappaya.office.type', request.params['officeTypeId'])
            if 'stateId' in request.params:
                if self._check_record_existance('res.country.state', request.params['stateId']) is not True:
                    return self._check_record_existance('res.country.state', request.params['stateId'])
                state_id = self.get_db_id('res.country.state', request.params['stateId'])
            if 'empNoRef' in request.params:
                emp_no_ref = request.params['empNoRef']
            if record_id and branch_name and office_type_id and state_id:
                if env['pappaya.payroll.branch'].search([('name','=',branch_name),('office_type_id','=',office_type_id),('state_id','=',state_id)]):
                    values['error_msg'] = "422 - Duplicate Entry - Record Already exists for given input combination."
                    return values
                try:
                    branch_creation = env['pappaya.payroll.branch'].create({'name':branch_name,'branch_type':branch_type,'state_id':state_id,
                                               'office_type_id':office_type_id,'emp_no_ref':emp_no_ref, 'record_id':record_id})
                    if branch_creation:
                        values['status'] = "201 - OK - New payroll branch record has been created successfully."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
                    return values
            else:
                values['error_msg'] = "422 - Unprocessable Entity - branchName, branchType, stateId and recordId are mandatory to create branch."
        values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
        return values
                        
    @http.route('/api/v1/update_payroll_branch_data', type='json', auth="none", cors='*')
    def update_payroll_branch_data(self, **kw):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        if request.httprequest.method == 'POST':
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            branch_obj = False
            data_to_update = {}
            if 'recordId' in request.params:
                if self._check_record_existance('pappaya.payroll.branch', request.params['recordId']) is not True:
                    return self._check_record_existance('pappaya.payroll.branch', request.params['recordId'])
                branch_obj = self.get_object_to_write('pappaya.payroll.branch', request.params['recordId'])
            if 'branchName' in request.params:
                data_to_update.update({'name':request.params['branchName']})
            if 'officeTypeId' in request.params:
                if self._check_record_existance('pappaya.office.type', request.params['officeTypeId']) is not True:
                    return self._check_record_existance('pappaya.office.type', request.params['officeTypeId'])
                office_type_id = self.get_db_id('pappaya.office.type', request.params['officeTypeId'])            
                data_to_update.update({'office_type_id':office_type_id})
            if 'stateId' in request.params:
                if self._check_record_existance('res.country.state', request.params['stateId']) is not True:
                    return self._check_record_existance('res.country.state', request.params['stateId'])
                state_id = self.get_db_id('res.country.state', request.params['stateId'])
                data_to_update.update({'state_id':state_id})
            if 'empNoRef' in request.params:
                data_to_update.update({'emp_no_ref':request.params['empNoRef']})
            if branch_obj and data_to_update:
                try:
                    record_updated = branch_obj.write(data_to_update)
                    if record_updated:
                        values['status'] = "200 - OK - Eyerything is working - Given data has been successfully changed."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
                    return values
            else:
                values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
            return values
        
    @http.route('/api/v1/add_employee_data', type='json', auth="none", cors='*')
    def add_employee_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {})
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            employee_name = ''; employee_id = '' ; job_id = '' ; active = False ; status = True; record_id = False
            emp_no_ref = ''; unique_id = ''; mobile=''; payroll_branch_id = '';email='';required_user = False
            if 'employeeName' in request.params:
                employee_name=request.params['employeeName']
            if 'employeeId' in request.params:
                if env['hr.employee'].search([('emp_id','=',request.params['employeeId'])]):
                    values['error_msg'] = "422 - Unprocessable Entity - Given employee ID is already Exists."
                    return values
                employee_id = request.params['employeeId']
            if 'uniqueId' in request.params:
                if env['hr.employee'].search([('unique_id','=',request.params['uniqueId'])]):
                    values['error_msg'] = "422 - Unprocessable Entity - Given unique number is already Exists."
                    return values
                unique_id = request.params['uniqueId']
            if 'mobile' in request.params:
                mobile = request.params['mobile']
            if 'payrollBranchId' in request.params:
                if self._check_record_existance('pappaya.payroll.branch', request.params['payrollBranchId']) is not True:
                    return self._check_record_existance('pappaya.payroll.branch', request.params['payrollBranchId'])
                payroll_branch_id = self.get_db_id('pappaya.payroll.branch', request.params['payrollBranchId'])
            if 'empNoRef' in request.params:
                emp_no_ref = request.params['empNoRef']                
            if 'jobId' in request.params:
                if self._check_record_existance('hr.job', request.params['jobId']) is not True:
                    return self._check_record_existance('hr.job', request.params['jobId'])
                job_id = self.get_db_id('hr.job', request.params['jobId'])
            if 'active' in request.params:
                status = True if request.params['active'] == 'True' else False
                active = request.params['active']
            if 'recordId' in request.params:
                if self._check_record_id_duplication('hr.employee', request.params['recordId']) is not True:
                    return self._check_record_id_duplication('hr.employee', request.params['recordId'])
                record_id = request.params['recordId']
            if 'email' in request.params:
                email = request.params['email']
            if 'requiredUser' in request.params:
                required_user = True if request.params['requiredUser'] == 'True' else False
            if employee_name and employee_id and job_id and record_id and unique_id:
                try:
                    employee_creation = env['hr.employee'].create({
                        'name' : employee_name,
                        'emp_id': employee_id,
                        'job_id' : job_id,
                        'active' : active,
                        'record_id':record_id,
                        'emp_no_ref' : emp_no_ref,
                        'unique_id':unique_id,
                        'work_mobile':mobile,
                        'work_email': email,
                        'payroll_branch_id':payroll_branch_id
                        })
                    if not status:
                        employee_creation.write({'active': status})
                    if required_user:
                        employee_creation.create_user()
                    if employee_creation:
                        values['status'] = "201 - OK - New Employee record has been created successfully."
                        _logger.info("201 - OK - New Employee record has been created successfully.")
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            else:
                values['error_msg'] = "422 - Unprocessable Entity - employeeName, employeeId, jobId, recordId and uniqueId are mandatory to create employee record."
                return values
            values['error_msg'] = "422 - Unproceesable Entity - Please check given params"
            return values    

    @http.route('/api/v1/update_employee_data', type='json', auth="none", cors='*')
    def update_employee_data(self, **kw):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        if request.httprequest.method == 'POST':
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            employee_obj = False
            employee_dict_to_update = {}
            if 'recordId' in request.params:
                if self._check_record_existance('hr.employee', request.params['recordId']) is not True:
                    return self._check_record_existance('hr.employee', request.params['recordId'])
                employee_obj = self.get_object_to_write('hr.employee', request.params['recordId'])
            if 'employeeName' in request.params:
                employee_dict_to_update.update({'name':request.params['employeeName']})
            if 'employeeId' in request.params:
                if env['hr.employee'].search([('emp_id','=',request.params['employeeId'])]):
                    values['error_msg'] = "422 - Unprocessable Entity - Given employee ID is already Exists."
                    return values
                employee_dict_to_update.update({'emp_id':request.params['employeeId']})
            if 'empNoRef' in request.params:
                employee_dict_to_update.update({'emp_no_ref':request.params['empNoRef']})           
            if 'jobId' in request.params:
                if self._check_record_existance('hr.job', request.params['jobId']) is not True:
                    return self._check_record_existance('hr.job', request.params['jobId'])
                job_id = self.get_db_id('hr.job', request.params['jobId'])
                employee_dict_to_update.update({'job_id':job_id})
            if 'empNoRef' in request.params:
                employee_dict_to_update.update({'emp_no_ref':request.params['empNoRef']})
            if 'active' in request.params:
                status = True if request.params['active'] == 'True' else False
                employee_dict_to_update.update({'active':status})
            if 'uniqueId' in request.params:
                if env['hr.employee'].search([('unique_id','=',request.params['uniqueId'])]):
                    values['error_msg'] = "422 - Unprocessable Entity - Given unique number is already Exists."
                    return values
                employee_dict_to_update.update({'unique_id': request.params['uniqueId']})
            if 'mobile' in request.params:
                employee_dict_to_update.update({'mobile': request.params['mobile']})
            if 'payrollBranchId' in request.params:
                if self._check_record_existance('pappaya.payroll.branch', request.params['payrollBranchId']) is not True:
                    return self._check_record_existance('pappaya.payroll.branch', request.params['payrollBranchId'])
                payroll_branch_id = self.get_db_id('pappaya.payroll.branch', request.params['payrollBranchId'])
                employee_dict_to_update.update({'payroll_branch_id':payroll_branch_id})
            if 'email' in request.params:
                employee_dict_to_update.update({'work_email':request.params['email']})
            if employee_obj and employee_dict_to_update:
                try:
                    record_modified = employee_obj.write(employee_dict_to_update)
                    if record_modified:
                        values['status'] = "200 - OK - Eyerything is working - Given data has been successfully changed."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - Unprocessable Entity - Please check given input."
                    return values
            values['error_msg'] = "422 - Unproceesable Entity - Please check given params"
            return values
    
    @http.route('/api/v1/get_student_address_data', type='json', auth="none")
    def get_student_address_data(self, **kw):
        values = request.params.copy()
        if request.httprequest.method == 'POST':
            env = Environment(request.cr, SUPERUSER_ID, {}); 
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            student_address = []
            for sudent_address_obj in env['pappaya.lead.stud.address'].search([('record_id','=',None)], order='sequence'):
                student_address_dict = {}
                student_address_dict = {
                    'dbId': sudent_address_obj.id,
                    'branch_id':sudent_address_obj.branch_id.record_id,
                    'sequence':sudent_address_obj.sequence,
                    'student_name':sudent_address_obj.name,
                    'academic_year': sudent_address_obj.academic_year_id.name,
                    'employee_id':sudent_address_obj.employee_id.record_id,
                    'studying_course_id':sudent_address_obj.studying_course_id.record_id,
                    'state_id':sudent_address_obj.state_id.record_id,
                    'district_id':sudent_address_obj.district_id.record_id,                    
                }
                if sudent_address_obj.father_name:
                    student_address_dict.update({'father_name':sudent_address_obj.father_name})
                else:
                    student_address_dict.update({'father_name':''})
                if sudent_address_obj.location_type:
                    student_address_dict.update({'location_type':sudent_address_obj.location_type})
                else:
                    student_address_dict.update({'location_type':''})
                if sudent_address_obj.city:
                    student_address_dict.update({'city':sudent_address_obj.city})
                else:
                    student_address_dict.update({'city':''})
                if sudent_address_obj.ward:
                    student_address_dict.update({'ward':sudent_address_obj.ward})
                else:
                    student_address_dict.update({'ward':''})
                if sudent_address_obj.area:
                    student_address_dict.update({'area':sudent_address_obj.area})
                else:
                    student_address_dict.update({'area':''})
                if sudent_address_obj.mandal:
                    student_address_dict.update({'mandal':sudent_address_obj.mandal})
                else:
                    student_address_dict.update({'mandal':''})
                if sudent_address_obj.village:
                    student_address_dict.update({'village':sudent_address_obj.village})
                if sudent_address_obj.pincode:
                    student_address_dict.update({'pincode':sudent_address_obj.pincode})
                if sudent_address_obj.mobile:
                    student_address_dict.update({'mobile':sudent_address_obj.mobile})
                if sudent_address_obj.studying_school_name:
                    student_address_dict.update({'studying_school_name':sudent_address_obj.studying_school_name})
                if sudent_address_obj.status:
                    student_address_dict.update({'status':sudent_address_obj.status})
                if sudent_address_obj.file_name:
                    student_address_dict.update({'file_name':sudent_address_obj.file_name})
                student_address.append(student_address_dict)                
            if student_address:
                request.params['student_address'] = student_address
                request.params['status'] = "201 - OK - Student Address data has been fetched successfully."
                return request.params
            else:
                request.params['student_address'] = student_address
                request.params['status'] = "Could not found active country data."
                return request.params
        return values        
        
    @http.route('/api/v1/update_student_address_data', type='json', auth="none", cors='*')
    def update_student_address_data(self, **kw):
        values = request.params.copy()
        env = Environment(request.cr, SUPERUSER_ID, {})
        dict_to_update = {}
        if request.httprequest.method == 'POST':
            record_id = False
            address_object = False
            if self._validate_authentication() is not True:
                return self._validate_authentication()
            if 'dbId' in request.params:
                if isinstance(request.params['dbId'], int):
                    address_object = env['pappaya.lead.stud.address'].search([('id','=',request.params['dbId'])], order='sequence')
                    if not address_object:
                        values['error_msg'] = "404 - No Lead address record found for given dbId."
                        return values
                else:
                    values['error_msg'] = "422 - dbId should be integer."
                    return values
            else:
                values['error_msg'] = "422 - dbId should be mandatory to fetch lead address."
                return values
            if 'recordId' in request.params:
                record_id = request.params['recordId']
                if not isinstance(record_id, int):
                    values['error_msg'] = "422 - recordId should be integer."
                    return  values
            if address_object and record_id:
                if env['pappaya.lead.stud.address'].search([('record_id','=',record_id)]):
                    values['error_msg'] = "422 - Duplicate Entry - Record already exists with given record Id."
                    return values
                try:
                    update = address_object.write({'record_id':record_id})
                    if update:
                        values['status'] = "201 - OK - Given recordId has been updated successfully."
                        return values
                except:
                    request.cr.rollback()
                    values['error_msg'] = "422 - dbId or recordId are incorrect."
                    return values
            else:
                values['error_msg'] = "422 - dbId and recordId are mandatory to update."
                return values
        values['error_msg'] = "422 - Unproceesable Entity - Please check the input."
        return values 

    ''' End '''
    