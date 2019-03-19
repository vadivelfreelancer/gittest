# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OrgChartDepartment(models.Model):
	_name = 'org.chart.department'

	name = fields.Char("Org Chart Department",size=200)

	@api.model
	def get_department_data(self):
		data = {
			'name': self.env.user.company_id.name,
			'title': '',
			'children': [],
		}
		departments = self.env['operating.unit'].search([('company_id','!=',False),('child_ids','!=',False)])
		for department in departments:
			data['children'].append(self.get_children(department, 'middle-level'))
		
		return {'values': data}


	@api.model
	def get_children(self, dep, style=False):
		data = []
		dep_data = {'name': dep.name, 'title': dep.company_id.name}
		childrens = self.env['operating.unit'].search([('parent_id','=',dep.id)])
		for child in childrens:
			sub_child = self.env['operating.unit'].search([('parent_id','=',child.id),('company_id','=',child.company_id.id)])
			next_style= self._get_style(style)
			if not sub_child:
				data.append({'name': child.name, 'title': child.company_id.name, 'className': next_style})
			else:
				data.append(self.get_children(child, next_style))

		if childrens:
			dep_data['children'] = data
		if style:
			dep_data['className'] = style

		return dep_data


	def _get_style(self, last_style):
		if last_style == 'middle-level':
			return 'product-dept'
		if last_style == 'product-dept':
			return 'rd-dept'
		if last_style == 'rd-dept':
			return 'pipeline1'
		if last_style == 'pipeline1':
			return 'frontend1'

		return 'middle-level'
