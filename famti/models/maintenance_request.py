from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import models
import io
import base64
import xlsxwriter

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    show_supervisor_button = fields.Boolean(compute="_compute_stage_buttons",store=False)
    show_approve_button = fields.Boolean(compute="_compute_stage_buttons",store=False)
    show_submit_button =  fields.Boolean( compute="_compute_stage_buttons", store=False)
    show_responsible = fields.Boolean(compute="_compute_responsible_field", store=False)
    show_scrap_button = fields.Boolean(compute="_compute_stage_buttons", store=False)

    contractor_name = fields.Char(string="Contractor Name", required=True)
    contractor_id = fields.Many2one('res.partner', string="Contractor")
    contractor_phone = fields.Char(string="Phone No", required=True)
    expected_duration = fields.Float(string="Expected Maintenance Duration")
    start_datetime = fields.Datetime(string="Start Date")
    end_datetime = fields.Datetime(string="End Date")
    track_ids = fields.One2many('maintenance.track','maintenance_id',
        string="Track Maintenance", tracking=True
    )
    email = fields.Char(string="Email", required=True)
    request_date = fields.Datetime(string="Request Date", default=fields.Datetime.now)
    downtime_start = fields.Datetime("Downtime Start")
    downtime_end = fields.Datetime("Downtime End")
    downtime_duration = fields.Float(
        "Downtime (Hours)",
        compute="_compute_downtime",
        store=True
    )
    completion_remarks = fields.Text(string="Closure Remarks")
    repair_file = fields.Binary(string="Upload File")
    repair_filename = fields.Char(string="File Name")


    vent_from = fields.Datetime(string="Vent From")
    vent_to = fields.Datetime(string="Vent To")
    vent_total = fields.Float(string="Vent Total")
    vent_reason = fields.Char(string="Vent Reason")

    boat_heating_kw = fields.Float(string="Boat Heating (KW)")
    other_than = fields.Char(string="Other Than")

    vacuum_start_time = fields.Datetime(string="Vacuum Start Time")
    heating_start_time = fields.Datetime(string="Heating Start Time")
    web_start_time = fields.Datetime(string="Web Start Time")
    mc_stop_time = fields.Datetime(string="Machine Stop Time")

    @api.onchange('start_datetime', 'end_datetime')
    def _onchange_duration_calculation(self):
        for rec in self:
            rec.duration = 0.0

            if rec.start_datetime and rec.end_datetime:

                if rec.end_datetime < rec.start_datetime:
                    raise ValidationError("End Date must be greater than Start Date")

                # Difference in hours
                diff = rec.end_datetime - rec.start_datetime
                rec.duration = diff.total_seconds() / 3600

    def action_view_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Request',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }
    
    @api.depends('downtime_start', 'downtime_end')
    def _compute_downtime(self):
        for rec in self:
            if rec.downtime_start and rec.downtime_end:
                diff = rec.downtime_end - rec.downtime_start
                rec.downtime_duration = diff.total_seconds() / 3600
            else:
                rec.downtime_duration = 0

    @api.depends('maintenance_team_id')
    def _compute_responsible_field(self):
        for rec in self:
            rec.show_responsible = False
            if rec.maintenance_team_id and rec.maintenance_team_id.name == "External Maintenance":
                rec.show_responsible = True

    @api.onchange('user_id', 'maintenance_team_id','contractor_id')
    def _onchange_email(self):
        for rec in self:
            if rec.maintenance_team_id and rec.maintenance_team_id.name == "External Maintenance":
                rec.email = rec.contractor_id.email if rec.contractor_id and rec.contractor_id.email else False
                rec.contractor_phone = rec.contractor_id.phone if rec.contractor_id and rec.contractor_id.phone else False
                rec.user_id = False
            else:
                rec.email = rec.user_id.email if rec.user_id else False
                rec.contractor_phone = rec.user_id.partner_id.phone if rec.user_id and rec.user_id.partner_id.phone else False
    
    @api.model
    def create(self, vals):
        rec = super().create(vals)

        if rec.maintenance_team_id and rec.maintenance_team_id.name == "External Maintenance":
            rec.activity_schedule_external()

        return rec
        
    def write(self, vals):
        res = super().write(vals)

        for rec in self:
            if rec.maintenance_team_id and rec.maintenance_team_id.name == "External Maintenance":
                rec.activity_schedule_external()

        return res

    def activity_schedule_external(self):
        for rec in self:
            if rec.maintenance_team_id.name == "External Maintenance":
                if not rec.email:
                    raise UserError("Enter contractor email")

                self.env['mail.activity'].create({
                    'res_model_id': self.env['ir.model']._get_id('maintenance.request'),
                    'res_id': rec.id,
                    'summary': 'External Maintenance',
                    'note': f"Assigned to Contractor: {rec.contractor_id.name} ({rec.email})",
                    'user_id': self.env.user.id  
                })

    @api.depends('stage_id')
    def _compute_stage_buttons(self):
        for rec in self:
            rec.show_supervisor_button = False
            rec.show_approve_button = False
            rec.show_submit_button = False
            rec.show_scrap_button = False

            if rec.stage_id.name == "To Approve":
                rec.show_supervisor_button = True

            if rec.stage_id.name == "In Progress":
                rec.show_approve_button = True

            if rec.stage_id.name == "New Request":
                rec.show_submit_button = True

            if rec.stage_id.name == "Scrap":
                rec.show_scrap_button = True


    def send_for_cfo_appoval(self):
        for rec in self:
            # find CFO stage
            cfo_stage = self.env['maintenance.stage'].search(
                [('name', '=', 'In Progress')],	
                limit=1
            )
            if rec.stage_id.name == 'To Approve':
                rec.stage_id = cfo_stage.id
                for track in rec.track_ids:
                    if track.state not in ['repaired', 'scrap']:
                        track.state = 'in_progress'
            else:
                raise UserError(_('Only To Approve Will Be Send To Approve By Supervisor'))

        
    def maintenance_approval(self):
        for rec in self:

            if not rec.duration:
                raise UserError(_("Please enter the Duration before approving the maintenance."))

            cfo_stage = self.env['maintenance.stage'].search(
                [('name', '=', 'Repaired')],
                limit=1
            )
            if rec.stage_id.name == 'In Progress':
                rec.stage_id = cfo_stage.id
                for track in rec.track_ids:
                    if track.state not in ['repaired', 'scrap']:
                        track.state = 'repaired'
            else:
                raise UserError(_('Only In Progress Will Be Send To Approve By Maintenance'))
    
    def submit_for_approval(self):
        for rec in self:
            cfo_stage = self.env['maintenance.stage'].search(
                [('name', '=', 'To Approve')],
                limit=1
            )
            if rec.stage_id.name == 'New Request':
                rec.stage_id = cfo_stage.id
                for track in rec.track_ids:
                    if track.state not in ['repaired', 'scrap']:
                        track.state = 'to_approve'
            else:
                raise UserError(_('Only New Request Will Be Send To In Progress'))

    def action_scrap_confirm(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirm Scrap',
            'res_model': 'scrap.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def action_open_track_wizard(self):
        return {
            'name': 'Track Maintenance',
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.track.wizard',
            'view_mode': 'form',
            'target': 'new', 
            'context': {
                'default_maintenance_id': self.id,
            }
        }
    
    def action_maintenance_downtime_excel(self):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Downtime Report')

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'border': 1,
            'bg_color': '#DCE6D1',
        })

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True,
        })

        table_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        sheet.set_column('A:O', 20)

        sheet.merge_range('A1:O1', 'FAMTI', title_format)

        machine_name = ''

        if self:
            machine_name = self[0].equipment_id.name or ''

        sheet.merge_range('A2:P2', machine_name, title_format)
        sheet.merge_range('A4:D4', 'Process down time', header_format)
        sheet.merge_range('E4:E5', 'vacuum start time', header_format)
        sheet.merge_range('F4:F5', 'heating start time', header_format)
        sheet.merge_range('G4:G5', 'web start time', header_format)
        sheet.merge_range('H4:H5', 'm/c stop time', header_format)
        sheet.merge_range('I4:I5', 'remarks', header_format)
        sheet.merge_range('J4:J5', 'vent time', header_format)
        sheet.merge_range('K4:K5', 'boat heating (kw)', header_format)
        sheet.merge_range('L4:O4', 'other than', header_format)

        sub_headers = ['from', 'to', 'total', 'reason']

        col = 0

        for head in sub_headers:
            sheet.write(4, col, head, header_format)
            col += 1

        col = 11

        for head in sub_headers:
            sheet.write(4, col, head, header_format)
            col += 1

        row = 5

        for rec in self:

            sheet.write(row, 0,str(rec.downtime_start or ''),table_format)
            sheet.write(row, 1,str(rec.downtime_end or ''),table_format)
            sheet.write(row, 2,rec.downtime_duration or 0,table_format)
            sheet.write( row, 3, rec.name or '', table_format)
            sheet.write(row, 4, str(rec.vacuum_start_time or ''),table_format)
            sheet.write(row, 5, str(rec.heating_start_time or ''), table_format)
            sheet.write( row, 6,str(rec.web_start_time or ''), table_format)
            sheet.write(row, 7,str(rec.mc_stop_time or ''), table_format)
            sheet.write( row, 8,rec.completion_remarks or '', table_format)
            vent_time = ''

            if rec.vent_from and rec.vent_to:
                vent_time = f"{rec.vent_from} - {rec.vent_to}"

            sheet.write(row, 9,vent_time,table_format)
            sheet.write(row, 10, rec.boat_heating_kw or 0,table_format)
            sheet.write(row, 11, rec.vent_from or '', table_format)
            sheet.write( row, 12,rec.vent_to or '',table_format)
            sheet.write(row, 13,rec.vent_total or '', table_format)
            sheet.write(row, 14,rec.other_than or '',table_format)
            row += 1

        eng_start_row = row + 3

        sheet.merge_range(
            eng_start_row,
            0,
            eng_start_row,
            3,
            'Engineering down time',
            header_format
        )

        eng_headers = ['From', 'To', 'Total', 'Reason']

        col = 0

        for head in eng_headers:
            sheet.write(eng_start_row + 1, col, head, header_format)
            col += 1

        eng_row = eng_start_row + 2

        for rec in self:

            sheet.write(eng_row,0,str(rec.start_datetime or ''),table_format)
            sheet.write(eng_row, 1,str(rec.end_datetime or ''), table_format)
            sheet.write(eng_row, 2,rec.expected_duration or 0,table_format)
            sheet.write( eng_row,3,rec.completion_remarks or '', table_format)

            eng_row += 1

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Maintenance_Downtime_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype':
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }



class MaintenanceTrack(models.Model):
    _name = 'maintenance.track'
    _description = 'Maintenance Tracking'

    maintenance_id = fields.Many2one(
        'maintenance.request',
        string="Maintenance",
        ondelete='cascade'
    )

    team_id = fields.Many2one('maintenance.team', string="Team", tracking=True)
    user_id = fields.Many2one('res.users', string="Responsible", tracking=True)

    contractor_name = fields.Char(string="Contractor Name", tracking=True)
    contractor_id = fields.Many2one('res.partner', string="Contractor")
    phone = fields.Char(string="Phone No", tracking=True)
    email = fields.Char(string="Email")
    request_date = fields.Datetime(string="Request Date", tracking=True)
    schedule_date = fields.Datetime(string="Scheduled Date", tracking=True)

    start_datetime = fields.Datetime(string="Start Date", tracking=True)
    end_datetime = fields.Datetime(string="End Date", tracking=True)

    expected_duration = fields.Float(string="Expected Maintenance Duration", tracking=True)

    duration = fields.Float(string="Duration", tracking=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string="Priority", tracking=True)
    show_responsible = fields.Boolean(compute="_compute_responsible_field",store=False)
    state = fields.Selection([
        ('new', 'New Request'),
        ('to_approve', 'To Approve'),
        ('in_progress', 'In Progress'),
        ('repaired', 'Repaired'),
        ('scrap', 'Scrap'),
    ], string="Status", default='new', tracking=True)


    notes = fields.Text(string="Notes", tracking=True)
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
    

    def action_open_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Track Maintenance',
            'res_model': 'maintenance.track',
            'view_mode': 'form',
            'view_id': self.env.ref('famti.view_maintenance_track_form').id,
            'res_id': self.id,
            'target': 'current',  
        }

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    scrap_date = fields.Datetime(string="Shutdown Date")
    assign_date = fields.Datetime(string="Assign Date")
    cost = fields.Float(string="Maintenance Cost")
    next_service_date = fields.Datetime(string="Next Service Date")
    maintenance_request_ids = fields.One2many(
        'maintenance.request',
        'equipment_id',
        string="Maintenance Requests"
    )
