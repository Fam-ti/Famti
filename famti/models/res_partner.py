from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
from datetime import datetime
import io
import base64
import xlsxwriter



class ResPartner(models.Model):
    _inherit = "res.partner"

    is_supplier = fields.Boolean(string="Supplier")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)


    iso_vendor_certificate = fields.Binary(string="ISO Vendor Certificate",
        attachment=True,required=True
    )
    iso_certificate_name = fields.Char(string="Certificate Name")
    
    vendor_document_expiry = fields.Date(string="Certificate Expiry Date")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verified_vendor', 'Certificate Verified'),
        ('certificate_expired', 'Certificate Expired'),
    ], string="Vendor Status", default='draft', tracking=True)

    gst_verified = fields.Boolean(string="GST Verified")

    credit_grace_days = fields.Integer(string="Credit Grace Period (Days)", default=0)
    lc_required = fields.Boolean(string="LC Required")
    lc_document = fields.Binary(string="LC Document",required=True)


    def action_iso_certificate_updated(self):
        for rec in self:
            if rec.is_supplier:
                if not rec.iso_vendor_certificate:
                    raise UserError("Please Upload The ISO Certificate.")
                if not rec.vendor_document_expiry:
                    raise UserError("Please Mention The Certificate Expiry Date.")
                if rec.vendor_document_expiry < datetime.now().date():
                    raise UserError("Expiry Date Must Be Future Date.")
                rec.state = 'verified_vendor'

    def action_iso_certificate_renew(self):
        for rec in self:
            rec.state = 'verified_vendor'


    def _cron_vendor_document_expiry_reminder(self):
        today = fields.Date.today()
        last_reminder_day = today + timedelta(days=2)

        vendors = self.search([
            ('is_supplier', '=', True),
            ('vendor_document_expiry', '>=', today),
            ('vendor_document_expiry', '<=', last_reminder_day),
            ('email', '!=', False),
        ])

        template = self.env.ref(
            'famti.mail_template_vendor_document_expiry',
            raise_if_not_found=False
        )

        for vendor in vendors:
            if vendor.vendor_document_expiry == today:
                vendor.write({
                    'state': 'certificate_expired'
                })

            subject = "Vendor Certificate Expiry Reminder"
            body = f"""
                Dear {vendor.name},

                Your certificate will expire on {vendor.vendor_document_expiry}.

                Please renew and share the updated certificate before the expiry date.

                Thank you,
                {self.env.user.company_id.name}
                """
            self.env['mail.mail'].create({
                'subject': subject,
                'body_html': body.replace('\n', '<br/>'),
                'email_to': vendor.email,
            }).send()

    
class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    transit_no = fields.Char("Transit No")
    institution_no = fields.Char("Institution No")


class CustomerVisit(models.Model):
    _name = 'customer.visit'
    _description = 'Customer Visit Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", default="New", copy=False)

    visit_date = fields.Date(string="Date of Visit", required=True, tracking=True)
    company_name = fields.Char(string="Company Name", required=True)
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")
    city = fields.Char(string="City")

    state_id = fields.Many2one('res.country.state', string="State")
    zip = fields.Char(string="ZIP")
    country_id = fields.Many2one('res.country', string="Country")
    
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")

    contact_person = fields.Char(string="Contact Person (Customer)")
    designation = fields.Char(string="Designation")

    purpose = fields.Selection([
        ('product_enquiry', 'Product Enquiry'),
        ('quotation_discussion', 'Quotation Discussion'),
        ('purchase_order', 'Purchase Order Discussion'),
        ('sample_approval', 'Sample Approval'),
        ('new_business', 'New Business Discussion'),
        ('price_negotiation', 'Price Negotiation'),
        ('technical_discussion', 'Technical Discussion'),
        ('product_demo', 'Product Demo'),
        ('material_inspection', 'Material Inspection'),
        ('vendor_meeting', 'Vendor Meeting'),
        ('customer_meeting', 'Customer Meeting'),
        ('complaint_resolution', 'Complaint Resolution'),
        ('payment_followup', 'Payment Follow-up'),
        ('service_support', 'Service Support'),
        ('other', 'Other'),
    ], string="Purpose of Visit")
    summary = fields.Text(string="Summary")
    action_items = fields.Text(string="Action Items")
    product_ids = fields.Many2many(
        'product.product',
        string="Products Discussed"
    )

    user_id = fields.Many2one('res.users', string="Visited By", default=lambda self: self.env.user)

    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('customer.visit') or 'New'
        return super().create(vals)
    
    def action_print_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Customer Visits')

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter'
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#1F4E78',
            'font_color': '#FFFFFF',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        data_format = workbook.add_format({
            'border': 1,
            'text_wrap': True
        })

        sheet.merge_range('A1:H1', 'Customer Visit Report', title_format)

        sheet.set_row(0, 30)
        sheet.set_row(1, 20)

        headers = [
            'Date', 'Company', 'Contact Person',
            'Designation', 'Products', 'Purpose',
            'Summary', 'Action Items'
        ]

        for col, header in enumerate(headers):
            sheet.write(1, col, header, header_format)

        row = 2
        for rec in self:
            products = ", ".join(rec.product_ids.mapped('name'))

            sheet.write(row, 0, str(rec.visit_date or ''), data_format)
            sheet.write(row, 1, rec.company_name or '', data_format)
            sheet.write(row, 2, rec.contact_person or '', data_format)
            sheet.write(row, 3, rec.designation or '', data_format)
            sheet.write(row, 4, products, data_format)
            sheet.write(row, 5, rec.purpose or '', data_format)
            sheet.write(row, 6, rec.summary or '', data_format)
            sheet.write(row, 7, rec.action_items or '', data_format)

            row += 1


        sheet.set_column(0, 0, 15)  
        sheet.set_column(1, 1, 25)  
        sheet.set_column(2, 2, 25)  
        sheet.set_column(3, 3, 20)  
        sheet.set_column(4, 4, 30)  
        sheet.set_column(5, 5, 30)  
        sheet.set_column(6, 6, 35)  
        sheet.set_column(7, 7, 35)  

        sheet.freeze_panes(2, 0)

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Customer_Visit_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_customer_history_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Customer History')

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter'
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#1F4E78',
            'font_color': '#FFFFFF',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        data_format = workbook.add_format({
            'border': 1,
            'text_wrap': True
        })

        sheet.merge_range('A1:I1', 'Customer History Report', title_format)
        sheet.set_row(0, 30)
        sheet.set_row(1, 20)

        headers = [
            'S.No', 'Customer Name', 'Address', 'Date of Order',
            'Type of Film', 'Description of Film',
            'Thickness', 'Weight', 'Amount'
        ]

        for col, header in enumerate(headers):
            sheet.write(1, col, header, header_format)

        row = 2
        serial = 1

        for rec in self:
            address = " ".join(filter(None, [
                rec.street, rec.street2, rec.city,
                rec.state_id.name if rec.state_id else '',
                rec.country_id.name if rec.country_id else ''
            ]))

            for product in rec.product_ids:

                sheet.write(row, 0, serial, data_format)
                sheet.write(row, 1, rec.company_name or '', data_format)
                sheet.write(row, 2, address, data_format)
                sheet.write(row, 3, str(rec.visit_date or ''), data_format)
                sheet.write(row, 4, product.name or '', data_format)  
                sheet.write(row, 5, product.name or '', data_format)  
                sheet.write(row, 6, '', data_format)  
                sheet.write(row, 7, '', data_format)  
                sheet.write(row, 8, product.list_price or 0, data_format)  

                row += 1
                serial += 1

        sheet.set_column(0, 0, 8)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 35)
        sheet.set_column(3, 3, 18)
        sheet.set_column(4, 5, 25)
        sheet.set_column(6, 8, 15)

        sheet.freeze_panes(2, 0)

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Customer_History_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
