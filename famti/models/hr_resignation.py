from odoo import models, fields, api
from datetime import date

class HrResignation(models.Model):
    _name = 'hr.resignation'
    _description = 'Employee Resignation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True)

    department_id = fields.Many2one('hr.department', string="Department")
    contract_id = fields.Many2one('hr.contract', string="Contract")
    joining_date = fields.Date(string="Joining Date")

    resignation_date = fields.Date(string="Resignation Date", required=True, tracking=True)
    approved_last_date = fields.Date(string="Approved Last Working Day", required=True, tracking=True)
    notice_period = fields.Integer(string="Notice Period (Days)", required=True, tracking=True)

    resignation_type = fields.Selection([
        ('normal', 'Normal Resignation'),
        ('terminated', 'Terminated / Fired')
    ],string="Resignation Type", default='normal', required=True, tracking=True)

    manager_id = fields.Many2one('hr.employee', string="Manager")

    reason = fields.Text(string="Reason", required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='draft')

    remarks = fields.Text(string="Rejection Remarks", tracking=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        # record.message_post(body="Resignation record created.")
        return record

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec.message_post(body="Resignation record updated.")
        return res

    # @api.onchange('employee_id')
    # def _onchange_employee(self):
    #     for rec in self:
    #         emp = rec.employee_id
    #
    #         if emp:
    #             rec.department_id = emp.department_id.id if emp.department_id else False
    #             rec.manager_id = emp.parent_id.id if emp.parent_id else False
    #             rec.joining_date = emp.joining_date
    #
    #             contract = self.env['hr.contract'].search(
    #                 [('employee_id', '=', emp.id), ('state', '=', 'open')],
    #                 limit=1
    #             )
    #             rec.contract_id = contract.id if contract else False
    #
    #         else:
    #             rec.department_id = False
    #             rec.manager_id = False
    #             rec.contract_id = False
    #             rec.joining_date = False

    def action_submit(self):
        self.state = 'waiting_for_approval'
        self.message_post(body="Sent for approval")

    def action_approve(self):
        self.state = 'approved'
        self.message_post(body="Resignation Approved")

    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'
        self.message_post(body="Resignation Rejected")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Resignation',
            'res_model': 'hr.resignation.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_resignation_id': self.id
            }
        }


class EmployeeResignation(models.Model):
    _name = 'employee.resignation'
    _description = 'Employee Resignation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True)

    department_id = fields.Many2one('hr.department',compute="_compute_employee_details", string="Department")
    contract_id = fields.Many2one('hr.contract',compute="_compute_employee_details", string="Contract")
    joining_date = fields.Date(string="Joining Date",compute="_compute_employee_details")

    resignation_date = fields.Date(string="Resignation Date", required=True, tracking=True)
    approved_last_date = fields.Date(string="Approved Last Working Day", required=True, tracking=True)
    notice_period = fields.Integer(string="Notice Period (Days)", required=True, tracking=True)

    resignation_type = fields.Selection([
        ('normal', 'Normal Resignation'),
        ('terminated', 'Terminated / Fired'),
        ('retirement', 'Retirement')
    ], default='normal', required=True, tracking=True)

    manager_id = fields.Many2one('hr.employee', compute="_compute_employee_details",string="Manager")

    reason = fields.Text(string="Reason", required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='draft')

    remarks = fields.Text(string="Rejection Remarks", tracking=True)

    @api.depends('employee_id')
    def _compute_employee_details(self):
        for rec in self:
            emp = rec.employee_id
            if emp:
                rec.department_id = emp.department_id
                rec.manager_id = emp.parent_id
                rec.joining_date = emp.joining_date

                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'open')
                ], limit=1)

                rec.contract_id = contract
            else:
                rec.department_id = False
                rec.manager_id = False
                rec.joining_date = False
                rec.contract_id = False

    def action_submit(self):
        self.state = 'waiting_for_approval'
        self.message_post(body="Sent for approval")

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

            if rec.employee_id:
                reason_map = {
                    'normal': 'Resignation',
                    'terminated': 'Fired',
                    'retirement': 'Retirement',
                }

                reason_name = reason_map.get(rec.resignation_type)

                reason = self.env['hr.departure.reason'].search([
                    ('name', 'ilike', reason_name)
                ], limit=1)

                rec.employee_id.write({
                    'departure_reason_id': reason.id if reason else False,
                    'departure_description': rec.reason or rec.remarks,
                })

                if rec.approved_last_date and rec.approved_last_date <= date.today():
                    rec.employee_id.active = False

            rec.message_post(body="Resignation Approved")

    def action_reject(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Resignation',
            'res_model': 'hr.resignation.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_resignation_id': self.id
            }
        }
