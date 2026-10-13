from odoo import models, fields, api
import base64

class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    show_submit_approval = fields.Boolean(compute="_compute_stage_buttons", store=False)
    show_approve_button = fields.Boolean(compute="_compute_stage_buttons", store=False)
    is_hr_executive = fields.Boolean(compute="_compute_is_hr_executive", store=False)

    def _compute_is_hr_executive(self):
        for rec in self:
            user = self.env.user

            if user.has_group('famti.group_for_hr_executive'):
                rec.is_hr_executive = False
            else:
                rec.is_hr_executive = True

    @api.depends('stage_id')
    def _compute_stage_buttons(self):
        for rec in self:
            rec.show_submit_approval = rec.stage_id.name == 'Second Interview'
            rec.show_approve_button = rec.stage_id.name == 'Document Verification'


    def write(self, vals):
        old_stage_map = {rec.id: rec.stage_id.id for rec in self}
        res = super().write(vals)

        return res

    def send_offer_letter(self):
        self.ensure_one()

        template = self.env.ref('famti.email_template_offer_letter')

        pdf, _ = self.env['ir.actions.report']._render_qweb_pdf(
            'famti.offer_letter_report',
            [self.id]
        )

        attachment = self.env['ir.attachment'].create({
            'name': f'Offer Letter - {self.partner_name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf),
            'res_model': 'hr.applicant',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        subject = f"Offer Letter for the Position of {self.job_id.name or ''}"
        email_to = self.email_from or ''

        body = template._render_field('body_html', [self.id])[self.id]

        self.env['mail.mail'].create({
            'subject': subject,
            'body_html': body,
            'email_to': email_to,
            'attachment_ids': [(4, attachment.id)],
        }).send()

        self.message_post(
            body=body,
            subject=subject,
            message_type='comment',
            subtype_xmlid='mail.mt_note',
            attachment_ids=[attachment.id],
        )

    def submit_for_approval(self):
        document_verification = self.env['hr.recruitment.stage'].search(
            [('name', '=', 'Document Verification')], limit=1
        )   
        if document_verification:
            self.stage_id = document_verification.id

    def document_approved(self):
        document_verified = self.env['hr.recruitment.stage'].search(
            [('name', '=', 'Document Verified')], limit=1
        )   
        if document_verified:
            self.stage_id = document_verified.id

class HrJob(models.Model):
    _inherit = 'hr.job'

    budget = fields.Float(string="Budget")

    expected_date_to_fill = fields.Date(string="Expected Date to Fill")
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='draft', tracking=True)

    remarks = fields.Text(string=" Rejection Remarks", tracking=True)

    def action_submit(self):
        self.state = 'submitted'

    def action_approve(self):
        self.state = 'approved'

    def action_reject(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Reason',
            'res_model': 'hr.job.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_job_id': self.id
            }
        }

    
    
