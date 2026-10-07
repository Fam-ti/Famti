from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo import _

class ScrapConfirmWizard(models.TransientModel):
    _name = 'scrap.confirm.wizard'
    _description = 'Scrap Confirmation'
    
    def action_confirm_scrap(self):
        active_id = self.env.context.get('active_id')
        rec = self.env['maintenance.request'].browse(active_id)

        scrap_stage = self.env['maintenance.stage'].search(
            [('name', '=', 'Scrap')],
            limit=1
        )

        rec.stage_id = scrap_stage.id

class MaintenanceTrackWizard(models.TransientModel):
    _name = 'maintenance.track.wizard'
    _description = 'Track Maintenance Wizard'

    maintenance_id = fields.Many2one('maintenance.request', string="Maintenance")
    team_id = fields.Many2one('maintenance.team', string="Team", required=True)
    user_id = fields.Many2one('res.users', string="Responsible")

    contractor_name = fields.Char(string="Contractor Name")
    contractor_id = fields.Many2one('res.partner', string="Contractor")
    phone = fields.Char(string="Phone No", required=True)
    email = fields.Char(string="Email", required=True)

    request_date = fields.Datetime(string="Request Date", default=fields.Datetime.now, required=True)
    schedule_date = fields.Datetime(string="Scheduled Date")

    start_datetime = fields.Datetime(string="Start Date")
    end_datetime = fields.Datetime(string="End Date")

    expected_duration = fields.Float(string="Expected Maintenance Duration", required=True)

    duration = fields.Float(string="Duration")

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string="Priority", required=True)
    show_responsible = fields.Boolean(compute="_compute_responsible_field", store=False)
    state = fields.Selection([
        ('new', 'New Request'),
        ('to_approve', 'To Approve'),
        ('in_progress', 'In Progress'),
        ('repaired', 'Repaired'),
        ('scrap', 'Scrap'),
    ], string="Status", default='new')


    notes = fields.Text(string="Notes")
    downtime_start = fields.Datetime("Downtime Start")
    downtime_end = fields.Datetime("Downtime End")
    downtime_duration = fields.Float(
        "Downtime (Hours)",
        compute="_compute_downtime",
        store=True
    )

    @api.depends('downtime_start', 'downtime_end')
    def _compute_downtime(self):
        for rec in self:
            if rec.downtime_start and rec.downtime_end:
                diff = rec.downtime_end - rec.downtime_start
                rec.downtime_duration = diff.total_seconds() / 3600
            else:
                rec.downtime_duration = 0

    @api.depends('team_id')
    def _compute_responsible_field(self):
        for rec in self:
            rec.show_responsible = False
            if rec.team_id and rec.team_id.name == "External Maintenance":
                rec.show_responsible = True

    @api.onchange('user_id', 'team_id','contractor_id')
    def _onchange_email(self):
        for rec in self:
            if rec.team_id and rec.team_id.name == "External Maintenance":
                rec.email = rec.contractor_id.email if rec.contractor_id and rec.contractor_id.email else False
                rec.phone = rec.contractor_id.phone if rec.contractor_id and rec.contractor_id.phone else False
                rec.user_id = False
            else:
                rec.email = rec.user_id.email if rec.user_id else False
                rec.phone = rec.user_id.partner_id.phone if rec.user_id and rec.user_id.partner_id.phone else False
    

    def action_confirm(self):
        self.ensure_one()

        if self.team_id.name == "External Maintenance":
            if not self.contractor_id:
                raise UserError("Please enter Contractor Name.")
        else:
            if not self.user_id:
                raise UserError("Please select a responsible user.")

        self.env['maintenance.track'].create({
            'maintenance_id': self.maintenance_id.id,
            'team_id': self.team_id.id,
            'user_id': self.user_id.id,
            'contractor_id': self.contractor_id.id,
            'phone': self.phone,
            'email': self.email,
            'request_date': self.request_date,
            'schedule_date': self.schedule_date,
            'start_datetime': self.start_datetime,
            'end_datetime': self.end_datetime,
            'expected_duration': self.expected_duration,
            'duration': self.duration,
            'priority': self.priority,
            'state': self.state,
            'show_responsible': self.show_responsible,
            'notes': self.notes,
            'downtime_start': self.downtime_start,
        })
        if self.maintenance_id and self.schedule_date:
            self.maintenance_id.schedule_date = self.schedule_date
        self.maintenance_id.stage_id = self.env['maintenance.stage'].search([('name', '=', 'New Request')], limit=1).id
        self.activity_schedule_external()
        return {'type': 'ir.actions.act_window_close'}


    def activity_schedule_external(self):
        for rec in self:
            if rec.team_id and rec.team_id.name == "External Maintenance":

                if not rec.email:
                    raise UserError("Enter contractor email")

                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env['ir.model']._get_id('maintenance.request'),
                    'res_id': rec.maintenance_id.id,
                    'summary': 'External Maintenance',
                    'note': f"Assigned to Contractor: {rec.contractor_id.name} ({rec.email})",
                    'user_id': self.env.user.id
                })
