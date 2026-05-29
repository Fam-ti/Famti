from werkzeug import urls
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FreightOrder(models.Model):
    _inherit = 'freight.order'
    _description = 'Freight Order'

    purchase_id = fields.Many2one(
        'purchase.order',
        string="Purchase Order"
    )
    
    sale_id = fields.Many2one(
        'sale.order',
        string="Sales Order"
    )
    
    logo = fields.Image("Logo", max_width=1920, max_height=1920, default=lambda self: self.env.company.logo)
    etd = fields.Datetime(string="Estimated Time of Departure")
    bl_number = fields.Char( string="Bill of Lading Number", tracking=True)
    gross_weight = fields.Float(string="Gross Weight")
    net_weight = fields.Float(string="Net Weight")
    final_destination_id = fields.Many2one('freight.port', string="Final Destination",
                                      help="Final Destination of the freight order",tracking=True)
    eta = fields.Datetime(string="Estimated Time of Arrival")
    document_ids = fields.One2many('freight.order.document','freight_order_id',
        string="Documents"
    )
    etd_discharge_port = fields.Datetime(string="ETD (Discharge Port)")
    eta_destination = fields.Datetime(string="ETA (Destination / Toronto)")

    carrier_id = fields.Many2one('res.partner', string="Carrier Name")
    driver_name_id = fields.Many2one('res.partner', string="Driver Name")
    vehicle_number = fields.Char(string="Truck / Trailer No.")
    driver_phone = fields.Char(string="Driver Phone Number")
    driver_email = fields.Char(string="Driver Email")

    @api.onchange('driver_name_id')
    def _onchange_driver_name_id(self):
        for rec in self:
            if rec.driver_name_id:
                rec.driver_phone = rec.driver_name_id.phone or rec.driver_name_id.mobile or ''
                rec.driver_email = rec.driver_name_id.email or ''
            else:
                rec.driver_phone = ''
                rec.driver_email = ''


    def action_done(self):
        res = super().action_done()

        for rec in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

            url = urls.url_join(
                base_url,
                'odoo/action-%(actionId)s/%(id)s' % {
                    'id': rec.id,
                    'actionId': self.env.ref(
                        'freight_management_system.freight_order_action'
                    ).id
                }
            )
            partners = self.env['res.partner'].search([
                ('id', 'in', (
                    rec.shipper_id.id,
                    rec.consignee_id.id,
                    rec.agent_id.id
                ))
            ])

            accounts_group = self.env.ref('account.group_account_user')

            inventory_group = self.env.ref(
                'famti.group_inventory_dep_users'
            )

            sales_group = self.env.ref(
                'famti.group_sales_dep_users'
            )

            group_users = (
                accounts_group.users |
                inventory_group.users |
                sales_group.users
            )

            partners |= group_users.mapped('partner_id')
            partners = partners.filtered(lambda p: p.email)

            for partner in partners:
                mail_content = _(
                    'Hi %s,<br>'
                    'The Freight Order %s is Completed'
                    '<div style = "text-align: center; '
                    'margin-top: 16px;"><a href = "%s"'
                    'style = "padding: 5px 10px; font-size: 12px; '
                    'line-height: 18px; color: #FFFFFF; '
                    'border-color:#875A7B;text-decoration: none; '
                    'display: inline-block; '
                    'margin-bottom: 0px; font-weight: 400;'
                    'text-align: center; vertical-align: middle; '
                    'cursor: pointer; white-space: nowrap; '
                    'background-image: none; '
                    'background-color: #875A7B; '
                    'border: 1px solid #875A7B; border-radius:3px;">'
                    'View %s</a></div>'
                ) % (
                    partner.name,
                    rec.name,
                    url,
                    rec.name
                )

                mail_values = {
                    'subject': _('Freight Order %s is completed') % rec.name,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': partner.email,
                }

                mail = self.env['mail.mail'].create(mail_values)
                mail.send()

        return res

    


class FreightOrder(models.Model):
    _inherit = 'freight.order.line'
    _description = 'Freight Order Lines'


    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", related='order_id.purchase_id', store=True, readonly=True)   
    sale_id = fields.Many2one('sale.order', string="Sale Order", related='order_id.sale_id', store=True, readonly=True)   
    container_number = fields.Char(string="Container Number", tracking=True)

class FreightOrderDocument(models.Model):
    _name = 'freight.order.document'
    _description = 'Freight Order Documents'

    freight_order_id = fields.Many2one(
        'freight.order',
        string="Freight Order",
        ondelete='cascade'
    )

    document_type = fields.Selection([
        ('commercial_invoice', 'Commercial Invoice'),
        ('packing_list', 'Packing List (Excel/PDF)'),
        ('mbl', 'Master Bill of Lading'),
        ('hbl', 'House Bill of Lading'),
        ('coa', 'COA'),
        ('heat_certificate', 'Heat Treatment Certificate'),
        ('emanifest', 'E-manifest / ACI'),
    ], string="Document Type", required=True)

    file = fields.Binary(string="Upload Document")
    file_name = fields.Char(string="File Name")
