from werkzeug import urls
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from io import BytesIO
import base64
import xlsxwriter


class FreightOrder(models.Model):
    """Model for creating freight orders"""
    _name = 'freight.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Freight Order'

    name = fields.Char(string='Name', default='New', readonly=True,
                       help='Name of the order',tracking=True)
    shipper_id = fields.Many2one('res.partner', string='Shipper', required=True,
                                 help="Shipper's Details",tracking=True)
    consignee_id = fields.Many2one('res.partner', 'Consignee',
                                   help="Select the consignee for the order",tracking=True, required=True)
    type = fields.Selection([('import', 'Import'), ('export', 'Export')],tracking=True,
                            string='Import/Export', required=True,
                            help="Type of freight operation")
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('ocean', 'Ocean')], string='Transport',
                                      help='Type of transportation',
                                      required=True,tracking=True)
    land_type = fields.Selection([('ltl', 'LTL'), ('ftl', 'FTL')],
                                 string='Land Shipping',
                                 help="Types of shipment movement involved in"
                                      "Land",tracking=True)
    water_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')],
                                  string='Water Shipping',
                                  help="Types of shipment movement involved in"
                                       "Water",tracking=True)
    order_date = fields.Date(string='Date', default=fields.Date.today(),
                             help="Date of order",tracking=True)
    loading_port_id = fields.Many2one('freight.port', string="ETD(Load Port)",
                                      required=True,
                                      help="Load port of the freight order",tracking=True)
    discharging_port_id = fields.Many2one('freight.port',
                                          string="ETA(Discharge Port)",
                                          required=True,
                                          help="Discharge port of freight"
                                               "order",tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('submit', 'In Transit'),
                              ('confirm', 'Confirmed'),
                              ('invoice', 'Invoiced'), ('done', 'Done'),
                              ('cancel', 'Cancel')],
                             default='draft', string="State",
                             help='Different states of freight order',tracking=True)
    clearance = fields.Boolean(string='Clearance', help='Checking the'
                                                        'clearance',)
    clearance_count = fields.Integer(compute='_compute_count',
                                     string='Clearance Count',
                                     help='The number of clearance', store=True)
    invoice_count = fields.Integer(compute='_compute_count',
                                   string='Invoice Count',
                                   help='The number invoice created', store=True)
    total_order_price = fields.Float(string='Total',
                                     compute='_compute_total_order_price',
                                     help='The total order price', store=True)
    total_volume = fields.Float(string='Total Volume',
                                compute='_compute_total_order_price',
                                help='The total used volume', store=True)
    total_weight = fields.Float(string='Total Weight',
                                compute='_compute_total_order_price',
                                help='The total weight used', store=True)
    order_ids = fields.One2many('freight.order.line', 'order_id',
                                string='Freight Order Line',
                                help='The freight order lines of the order')
    route_ids = fields.One2many('freight.order.routes.line', 'freight_id',
                                string='Route', help='The route of order')
    total_route_sale = fields.Float(string='Total Sale',
                                    compute="_compute_total_route_cost",
                                    help='The total cost of sale', store=True)
    service_ids = fields.One2many('freight.order.service', 'freight_id',
                                  string="Service", help='Service of the order')
    total_service_sale = fields.Float(string='Service Total Amount',
                                      compute="_compute_total_service_cost",
                                      help='The total service cost of order', store=True)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    company_currency_id = fields.Many2one(related="company_id.currency_id", string="Company Currency")
    total_service_amount = fields.Monetary(string='Service Total Amount',
                                      compute="_compute_total_service_cost",currency_field="company_currency_id",
                                      help='The total service cost of order',store=True)
    agent_id = fields.Many2one('res.partner', string='Agent',
                               required=True, help="Details of agent",tracking=True)
    expected_date = fields.Date(string='Expected Date', help='The expected date'
                                                             'of the order',tracking=True, required=False)
    track_ids = fields.One2many('freight.track', 'freight_id',
                                string='Tracking', help='For tracking the'
                                                        'freight orders')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
    purchase_id = fields.Many2one('purchase.order',string="Purchase Order")
    commercial_invoice = fields.Binary(string="Upload Inv.",help="Upload The Commercial Invoice.",tracking=True)
    certificate_of_analysis = fields.Binary(string="Upload COA")
    bill_of_loading = fields.Binary(string="Upload BOL",help="Upload the bill of loading.")
    incoterm = fields.Selection([('fob','FOB'),('cif','CIF'),('cfr','CFR'),('ddp','DDP')],tracking=True, string='Incoterm',help="FOB: FAM Ti books freight & insurance via freight "
                                                                                                                 "forwarder,CIF: Supplier arranges freight & insurance to destination port,CFR: Supplier arranges freight only,"
                                                                                                                 "DDP: Supplier responsible for full delivery to FAM Ti")
    incoterm_id = fields.Many2one('account.incoterms', string='Incoterm',tracking=True, required=True,  help="FOB: FAM Ti books freight & insurance via freight "
                                                                                                                 "forwarder,CIF: Supplier arranges freight & insurance to destination port,CFR: Supplier arranges freight only,"
                                                                                                                 "DDP: Supplier responsible for full delivery to FAM Ti")
    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    # def action_export_tracking_xlsx(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Sales Excel Report',
    #         'res_model': 'sale.report.wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #     }

    def action_export_transport_summary_xlsx(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Transport Summary')
        # =====================================================
        # Formats
        # =====================================================

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 15,
            'border': 1,
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9EAD3',
            'border': 1,
            'align': 'center',
            'text_wrap': True,
        })

        normal_format = workbook.add_format({
            'border': 1,
            'align': 'left',
        })

        amount_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00',
        })

        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd-mm-yyyy',
        })

        # =====================================================
        # Sheet Setup
        # =====================================================

        sheet.set_column('A:H', 28)

        # =====================================================
        # Title
        # =====================================================

        sheet.merge_range(
            'A1:H1',
            'Local Delivery Tracking Report',
            title_format
        )

        # =====================================================
        # Headers
        # =====================================================

        headers = [
            'COMPANY NAME',
            'CUSTOMER NAME',
            'DONE JOB',
            'TOTAL WEIGHT',
            'NO OF PALLETS',
            'TRANSPORTATION FEES',
            'PICKUP DATE',
            'NOTES',
        ]

        row = 2

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)

        row += 1

        # =====================================================
        # Data
        # =====================================================

        for order in self:
            for track in order.track_ids:
                total_pallets = 0
                total_weight = 0
                for line in order.order_ids:
                    total_weight += line.weight if hasattr(line, 'weight') else 0
                    total_pallets += int(line.packing_no) if hasattr(line, 'packing_no') else 0

                col = 0

                # COMPANY NAME
                sheet.write(
                    row,
                    col,
                    order.shipper_id.name or '',
                    normal_format
                )
                col += 1

                # CUSTOMER NAME
                sheet.write(
                    row,
                    col,
                    order.consignee_id.name or '',
                    normal_format
                )
                col += 1

                # DONE JOB
                sheet.write(
                    row,
                    col,
                    track.date or '',
                    normal_format
                )
                col += 1

                # TOTAL WEIGHT
                sheet.write(
                    row,
                    col,
                    order.total_weight or 0.0,
                    amount_format
                )
                col += 1

                # NO OF PALLETS
                sheet.write(
                    row,
                    col,
                    total_pallets,
                    normal_format
                )
                col += 1

                # TRANSPORTATION FEES
                sheet.write(
                    row,
                    col,
                    order.total_service_amount or 0.0,
                    amount_format
                )
                col += 1

                # PICKUP DATE
                sheet.write(
                    row,
                    col,
                    str(order.order_date or ''),
                    date_format
                )
                col += 1

                # NOTES
                sheet.write(
                    row,
                    col,
                    order.incoterm_id.name or '',
                    normal_format
                )

                row += 1

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Transportation_Summary_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_export_container_payment_reminder_xlsx(self):

        from io import BytesIO
        import base64
        import xlsxwriter

        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Container Payments')

        # =====================================================
        # Formats
        # =====================================================

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 15,
            'border': 1,
        })

        sub_title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'border': 1,
            'bg_color': '#FFF2CC',
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9EAD3',
            'border': 1,
            'align': 'center',
            'text_wrap': True,
        })

        normal_format = workbook.add_format({
            'border': 1,
            'align': 'left',
        })

        amount_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00',
        })

        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd-mm-yyyy',
        })

        # =====================================================
        # Sheet Setup
        # =====================================================

        sheet.set_column('A:G', 25)

        # =====================================================
        # Titles
        # =====================================================

        sheet.merge_range(
            'A1:G1',
            'Container Payment Reminder To Accounts Team',
            title_format
        )

        sheet.merge_range(
            'A2:G2',
            'CONTAINERS',
            sub_title_format
        )

        # =====================================================
        # Headers
        # =====================================================

        headers = [
            'DUE Date',
            'Supplier',
            'Amount',
            'Invoice',
            'ETA Canada',
            'Container',
            'Paid or not',
        ]

        row = 3

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)

        row += 1

        # =====================================================
        # Data
        # =====================================================

        for order in self:
            for service in order.service_ids:
                for track in order.track_ids:
                    col = 0

                    # DUE DATE
                    sheet.write(
                        row,
                        col,
                        str(order.expected_date or ''),
                        date_format
                    )
                    col += 1

                    # SUPPLIER
                    sheet.write(
                        row,
                        col,
                        order.shipper_id.name or '',
                        normal_format
                    )
                    col += 1

                    # AMOUNT
                    sheet.write(
                        row,
                        col,
                        order.total_service_amount or 0.0,
                        amount_format
                    )
                    col += 1

                    # INVOICE
                    sheet.write(
                        row,
                        col,
                        service.category_id.name or '',
                        normal_format
                    )
                    col += 1

                    # ETA CANADA
                    sheet.write(
                        row,
                        col,
                        str(track.date or ''),
                        normal_format
                    )
                    col += 1

                    # CONTAINER
                    sheet.write(
                        row,
                        col,
                        order.order_ids[0].container_number or '',
                        normal_format
                    )
                    col += 1

                    # PAID OR NOT
                    sheet.write(
                        row,
                        col,
                        'Paid' if order.state == 'done' else 'Pending',
                        normal_format
                    )

                    row += 1

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Container_Payment_Reminder.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_export_warehouse_container_xlsx(self):

        from io import BytesIO
        import base64
        import xlsxwriter

        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Warehouse Containers')

        # =====================================================
        # Formats
        # =====================================================

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 15,
            'border': 1,
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9EAD3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        normal_format = workbook.add_format({
            'border': 1,
            'align': 'left',
        })

        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd-mm-yyyy',
        })

        # =====================================================
        # Sheet Setup
        # =====================================================

        sheet.set_column('A:E', 25)

        # =====================================================
        # Title
        # =====================================================

        sheet.merge_range(
            'A1:E1',
            'Updating Warehouse For Upcoming Containers',
            title_format
        )

        # =====================================================
        # Headers
        # =====================================================

        headers = [
            'DELIVERY DATE',
            'CONTAINER NO.',
            'SUPPLIER',
            'Delivery Location',
            'Status',
        ]

        row = 2

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)

        row += 1

        # =====================================================
        # Data
        # =====================================================

        for order in self:
            for line in order.order_ids:
                for track in order.track_ids:
                    col = 0

                    # DELIVERY DATE
                    sheet.write(
                        row,
                        col,
                        str(track.date or ''),
                        date_format
                    )
                    col += 1

                    # CONTAINER NO.
                    sheet.write(
                        row,
                        col,
                        line.container_number or '',
                        normal_format
                    )
                    col += 1

                    # SUPPLIER
                    sheet.write(
                        row,
                        col,
                        order.shipper_id.name or '',
                        normal_format
                    )
                    col += 1

                    # Delivery Location
                    sheet.write(
                        row,
                        col,
                        track.destination_loc_id.name or '',
                        normal_format
                    )
                    col += 1

                    # Status
                    sheet.write(
                        row,
                        col,
                        track.type or '',
                        normal_format
                    )

                    row += 1

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Warehouse_Upcoming_Containers.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_export_tracking_xlsx(self):

        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Container Tracking')

        # =========================
        # Formats
        # =========================

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 14,
            'border': 1,
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9EAD3',
            'border': 1,
            'align': 'center',
            'text_wrap': True,
        })

        normal_format = workbook.add_format({
            'border': 1,
        })

        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd-mm-yyyy',
        })

        # =========================
        # Sheet Setup
        # =========================

        sheet.set_column('A:V', 20)

        sheet.merge_range(
            'A1:V1',
            'Container Tracking Sheet',
            title_format
        )

        headers = [
            'PO DATE',
            'PO No.',
            'Pi No.',
            'Pi date',
            'ETD',
            'ORIGIN',
            'CUSTOMER',
            'shipping line',
            'Container No',
            'SUPPLIER',
            'AGENT',
            'BL No.',
            'SUPPLIER INV NO.',
            'CURRENT STATUS',
            'ETA PORT',
            'ETA Toronto',
            'Amount',
            'Paid or no',
            'CUSTOMS',
            'TELEX',
            'PICK UP No',
            'Delivery Location',
        ]

        row = 2

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)

        row += 1

        for order in self:

            for line in order.order_ids:
                col = 0

                sheet.write(row, col, str(order.purchase_id.name or ''), normal_format)
                col += 1

                sheet.write(row, col, order.purchase_id.date_approve or '', normal_format)
                col += 1

                sheet.write(row, col, order.purchase_id.name or '', normal_format)
                col += 1

                sheet.write(row, col, str(order.purchase_id.date_approve or ''), normal_format)
                col += 1

                sheet.write(row, col, str(order.loading_port_id.name or ''), normal_format)
                col += 1

                sheet.write(row, col, line.container_id.name or '', normal_format)
                col += 1

                sheet.write(row, col, order.consignee_id.name or '', normal_format)
                col += 1

                sheet.write(row, col, order.shipper_id.name or '', normal_format)
                col += 1

                sheet.write(row, col, line.container_number or '', normal_format)
                col += 1

                sheet.write(row, col, order.shipper_id.name or '', normal_format)
                col += 1

                sheet.write(row, col, order.agent_id.name or '', normal_format)
                col += 1

                sheet.write(row, col, order.bl_number or '', normal_format)
                col += 1

                sheet.write(row, col, order.name or '', normal_format)
                col += 1

                sheet.write(row, col, order.state or '', normal_format)
                col += 1

                sheet.write(row, col, str(order.discharging_port_id.name or ''), normal_format)
                col += 1

                sheet.write(row, col, str(order.discharging_port_id.name or ''), normal_format)
                col += 1

                sheet.write(row, col, line.weight or 0.0, normal_format)
                col += 1

                sheet.write(
                    row,
                    col,
                    'Paid' if order.state == 'done' else 'No',
                    normal_format
                )
                col += 1

                sheet.write(row, col, order.name or '', normal_format)
                col += 1

                sheet.write(row, col, order.name or '', normal_format)
                col += 1

                sheet.write(row, col, order.transport_type or '', normal_format)
                col += 1

                sheet.write(row, col, order.final_destination_id.name or '', normal_format)

                row += 1

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Container_Tracking.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


    @api.depends('order_ids.total_price', 'order_ids.volume',
                 'order_ids.weight')
    def _compute_total_order_price(self):
        """Computing the price of the order"""
        for rec in self:
            rec.total_order_price = sum(rec.order_ids.mapped('total_price'))
            rec.total_volume = sum(rec.order_ids.mapped('volume'))
            rec.total_weight = sum(rec.order_ids.mapped('weight'))

    @api.depends('route_ids.sale')
    def _compute_total_route_cost(self):
        """Computing the total cost of route operation"""
        for rec in self:
            rec.total_route_sale = sum(rec.route_ids.mapped('sale'))

    @api.depends('service_ids.total_sale')
    def _compute_total_service_cost(self):
        """Computing the total cost of services"""
        for rec in self:
            rec.total_service_sale = sum(rec.service_ids.mapped('total_sale'))
            rec.total_service_amount = sum(rec.service_ids.mapped('total_sale'))

    @api.model_create_multi
    def create(self, vals_list):
        """Create Sequence for multiple records"""
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'freight.order.sequence')
        return super(FreightOrder, self).create(vals_list)

    def action_create_custom_clearance(self):
        """Create custom clearance"""
        clearance = self.env['custom.clearance'].create({
            'name': 'CC - ' + self.name,
            'freight_id': self.id,
            'date': self.order_date,
            'loading_port_id': self.loading_port_id.id,
            'discharging_port_id': self.discharging_port_id.id,
            'agent_id': self.agent_id.id,
        })
        result = {
            'name': 'action.name',
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'current',
            'res_id': clearance.id,
            'res_model': 'custom.clearance',
        }
        self.clearance = True
        return result

    def get_custom_clearance(self):
        """Get custom clearance"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Custom Clearance',
            'view_mode': 'list,form',
            'res_model': 'custom.clearance',
            'domain': [('freight_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_track_order(self):
        """Track the order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Received/Delivered',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'freight.order.track',
            'context': {
                'default_freight_id': self.id
            }
        }

    def action_create_invoice(self):
        """Create invoice"""
        lines = []
        if self.order_ids:
            for order in self.order_ids:
                value = (0, 0, {
                    'name': order.product_id.name,
                    'price_unit': order.price,
                    'quantity': order.volume + order.weight,
                })
                lines.append(value)
        if self.route_ids:
            for route in self.route_ids:
                value = (0, 0, {
                    'name': route.routes_id.name,
                    'price_unit': route.sale,
                })
                lines.append(value)
        if self.service_ids:
            for service in self.service_ids:
                value = (0, 0, {
                    'name': service.service_id.name,
                    'price_unit': service.sale,
                    'quantity': service.qty
                })
                lines.append(value)
        invoice_line = {
            'move_type': 'out_invoice',
            'partner_id': self.shipper_id.id,
            'invoice_user_id': self.env.user.id,
            'invoice_origin': self.name,
            'ref': self.name,
            'invoice_line_ids': lines,
        }
        inv = self.env['account.move'].create(invoice_line)
        result = {
            'name': 'action.name',
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'current',
            'res_id': inv.id,
            'res_model': 'account.move',
        }
        self.state = 'invoice'
        return result

    def action_cancel(self):
        """Cancel the record"""
        if self.state == 'draft' and self.state == 'submit':
            self.state = 'cancel'
        else:
            raise ValidationError("You can't cancel this order")

    def get_invoice(self):
        """View the invoice"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('ref', '=', self.name)],
            'context': "{'create': False}"
        }

    @api.depends('name')
    def _compute_count(self):
        """Compute custom clearance and account move's count"""
        for rec in self:
            if rec.env['custom.clearance'].search(
                    [('freight_id', '=', rec.id)]):
                rec.clearance_count = rec.env['custom.clearance'].search_count(
                    [('freight_id', '=', rec.id)])
            else:
                rec.clearance_count = 0
            if rec.env['account.move'].search([('ref', '=', rec.name)]):
                rec.invoice_count = rec.env['account.move'].search_count(
                    [('ref', '=', rec.name)])
            else:
                rec.invoice_count = 0

    def action_submit(self):
        """Submitting order"""
        for rec in self:
            rec.state = 'submit'
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            Urls = urls.url_join(base_url,
                                 'odoo/action-%(actionId)s/%(id)s' % {
                                     'id': self.id, 'actionId': self.env.ref('freight_management_system.freight_order_action').id})
            mail_content = _('Hi %s,<br>'
                             'The Freight Order %s is Submitted'
                             '<div style = "text-align: center; '
                             'margin-top: 16px;"><a href = "%s"'
                             'style = "padding: 5px 10px; font-size: 12px; '
                             'line-height: 18px; color: #FFFFFF; '
                             'border-color:#875A7B;text-decoration: none; '
                             'display: inline-block; margin-bottom: 0px; '
                             'font-weight: 400;text-align: center; '
                             'vertical-align: middle; cursor: pointer; '
                             'white-space: nowrap; background-image: none; '
                             'background-color: #875A7B; '
                             'border: 1px solid #875A7B; border-radius:3px;">'
                             'View %s</a></div>'
                             ) % (rec.agent_id.name, rec.name, Urls, rec.name)
            email_to = self.env['res.partner'].search([
                ('id', 'in', (self.shipper_id.id, self.consignee_id.id,
                              self.agent_id.id))])
            for mail in email_to:
                main_content = {
                    'subject': _('Freight Order %s is Submitted') % self.name,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': mail.email
                }
                mail_id = self.env['mail.mail'].create(main_content)
                mail_id.mail_message_id.body = mail_content
                mail_id.send()

    def action_confirm(self):
        """Confirm order"""
        for rec in self:
            custom_clearance = self.env['custom.clearance'].search([
                ('freight_id', '=', self.id)])
            rec.state = 'confirm'
            # if custom_clearance:
            #     for clearance in custom_clearance:
            #         if clearance.state == 'confirm':
            #             rec.state = 'confirm'
            #             base_url = self.env['ir.config_parameter'].sudo().get_param(
            #                 'web.base.url')
            #             Urls = urls.url_join(base_url,
            #                                  'odoo/action-%(actionId)s/%(id)s' % {
            #                                      'id': self.id, 'actionId': self.env.ref('freight_management_system.freight_order_action').id})
            #             mail_content = _('Hi %s,<br> '
            #                              'The Freight Order %s is Confirmed '
            #                              '<div style = "text-align: center; '
            #                              'margin-top: 16px;"><a href = "%s"'
            #                              'style = "padding: 5px 10px; '
            #                              'font-size: 12px; line-height: 18px; '
            #                              'color: #FFFFFF; border-color:#875A7B; '
            #                              'text-decoration: none; '
            #                              'display: inline-block; '
            #                              'margin-bottom: 0px; font-weight: 400;'
            #                              'text-align: center; '
            #                              'vertical-align: middle; '
            #                              'cursor: pointer; white-space: nowrap; '
            #                              'background-image: none; '
            #                              'background-color: #875A7B; '
            #                              'border: 1px solid #875A7B; '
            #                              'border-radius:3px;">'
            #                              'View %s</a></div>'
            #                              ) % (rec.agent_id.name, rec.name,
            #                                   Urls, rec.name)
            #             email_to = self.env['res.partner'].search([
            #                 ('id', 'in', (self.shipper_id.id,
            #                               self.consignee_id.id, self.agent_id.id))])
            #             for mail in email_to:
            #                 main_content = {
            #                     'subject': _(
            #                         'Freight Order %s is Confirmed') % self.name,
            #                     'author_id': self.env.user.partner_id.id,
            #                     'body_html': mail_content,
            #                     'email_to': mail.email
            #                 }
            #                 mail_id = self.env['mail.mail'].create(main_content)
            #                 mail_id.mail_message_id.body = mail_content
            #                 mail_id.send()
            #         elif clearance.state == 'draft':
            #             raise ValidationError("the custom clearance ' %s ' is "
            #                                   "not confirmed" % clearance.name)
            # else:
            #     raise ValidationError(
            #         "Create a custom clearance for %s" % rec.name)
            for line in rec.order_ids:
                line.container_id.state = 'reserve'

    def action_done(self):
        """Mark order as done"""
        for rec in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            Urls = urls.url_join(base_url,
                                 'odoo/action-%(actionId)s/%(id)s' % {
                                     'id': self.id, 'actionId': self.env.ref('freight_management_system.freight_order_action').id})
            mail_content = _('Hi %s,<br>'
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
                             ) % (rec.agent_id.name, rec.name, Urls, rec.name)
            email_to = self.env['res.partner'].search([
                ('id', 'in', (self.shipper_id.id, self.consignee_id.id,
                              self.agent_id.id))])
            for mail in email_to:
                main_content = {
                    'subject': _('Freight Order %s is completed') % self.name,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': mail.email
                }
                mail_id = self.env['mail.mail'].create(main_content)
                mail_id.mail_message_id.body = mail_content
                mail_id.send()
            self.state = 'done'
            for line in rec.order_ids:
                line.container_id.state = 'available'


class FreightOrderLine(models.Model):
    """Freight order lines are defined"""
    _name = 'freight.order.line'
    _description = 'Freight Order Line'

    order_id = fields.Many2one('freight.order', string="Freight Order",
                               help="Reference from freight order")
    container_id = fields.Many2one('freight.container', string='Container',
                                   domain="[('state', '=', 'available')]",
                                   help='The freight container')
    product_id = fields.Many2one('product.product', string='Goods',
                                 help='The Freight Products')
    billing_type = fields.Selection([('weight', 'Weight'),
                                     ('volume', 'Volume')], string="Billing On",
                                    help='Select the billing type for'
                                         'calculating the total amount')
    pricing_id = fields.Many2one('freight.price', string='Pricing',
                                 help='The pricing of order')
    price = fields.Float(string='Unit Price', help='Unit price of the selected'
                                                   'goods')
    total_price = fields.Float(string='Total Price', help='This will be the'
                                                          'total price')
    volume = fields.Float(string='Volume', help='Volume of the goods')
    weight = fields.Float(string='Weight', help='Weight of the goods')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
    vessel_id = fields.Many2one('freight.vessel',string="Vessel")
    vessel = fields.Char(string="Vessel")
    packing_no = fields.Char(string="No.of packet list")
    packing_list_ids = fields.Many2many('stock.quant.package',string="Packing List")

    @api.constrains('weight')
    def _check_weight(self):
        """Checking the weight of containers"""
        for rec in self:
            if rec.container_id and rec.billing_type:
                if rec.billing_type == 'weight':
                    if rec.container_id.weight < rec.weight:
                        raise ValidationError(
                            'The weight is must be less '
                            'than or equal to %s' % (rec.container_id.weight))

    @api.constrains('volume')
    def _check_volume(self):
        """Checking the volume of containers"""
        for rec in self:
            if rec.container_id and rec.billing_type:
                if rec.billing_type == 'volume':
                    if rec.container_id.volume < rec.volume:
                        raise ValidationError(
                            'The volume is must be less '
                            'than or equal to %s' % (rec.container_id.volume))

    @api.onchange('pricing_id', 'billing_type')
    def _onchange_price(self):
        """Calculate the weight and volume of container"""
        for rec in self:
            if rec.billing_type == 'weight':
                rec.volume = 0.00
                rec.price = rec.pricing_id.weight
            elif rec.billing_type == 'volume':
                rec.weight = 0.00
                rec.price = rec.pricing_id.volume

    # @api.onchange('pricing_id', 'billing_type', 'volume', 'weight')
    # def _onchange_total_price(self):
    #     """Calculate sub total price"""
    #     for rec in self:
    #         if rec.billing_type and rec.pricing_id:
    #             if rec.billing_type == 'weight':
    #                 rec.total_price = rec.weight * rec.price
    #             elif rec.billing_type == 'volume':
    #                 rec.total_price = rec.volume * rec.price


class FreightOrderRoutesLine(models.Model):
    """Defining the routes for the shipping, also we can add the operations for
    the routes."""
    _name = 'freight.order.routes.line'
    _description = 'Freight Order Routes Lines'

    freight_id = fields.Many2one('freight.order', string='Freight Order',
                                 help='Relation from freight order')
    routes_id = fields.Many2one('freight.routes', required=True,
                                string='Routes', help='Select route of freight')
    source_loc_id = fields.Many2one('freight.port', string='Source Port',
                                    help='Select the source port')
    destination_loc_id = fields.Many2one('freight.port',
                                         string='Destination Port',
                                         help='Select the destination port')
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('ocean', 'Ocean')], string="Transport",
                                      required=True,
                                      help='Select the transporting medium')
    sale = fields.Float(string='Sale', help="Set the price for Land")
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
    origin_location  = fields.Char(string='Origin')
    destination_location  = fields.Char(string='Destination location')
    final_location  = fields.Char(string='Final location')


    @api.onchange('routes_id', 'transport_type')
    def _onchange_routes_id(self):
        """Calculate the price of route operation"""
        for rec in self:
            
            if rec.routes_id:
                transport = self.env['freight.routes'].search(
                    [('id', '=', rec.routes_id.id)], 
                    limit=1
                )
                rec.transport_type = transport.transport_type if transport else False

            if rec.transport_type:
                route = self.env['freight.routes'].search(
                    [('transport_type', '=', rec.transport_type)],
                    limit=1
                )
                rec.routes_id = route.id


            


class FreightOrderServiceLine(models.Model):
    """Services in freight orders"""
    _name = 'freight.order.service'
    _description = 'Freight Order Service'

    freight_id = fields.Many2one('freight.order', string='Freight Order',
                                 help='Relation from freight order')
    service_id = fields.Many2one('freight.service', required=True,
                                 string='Service', help='Select the service')
    partner_id = fields.Many2one('res.partner', string="Vendor",
                                 help='Select the partner for the service')
    qty = fields.Float(string='Quantity', help='How many Quantity required')
    cost = fields.Float(string='Cost', help='The cost price of the service')
    sale = fields.Float(string='Sale', help='Sale price of the service')
    company_currency_id = fields.Many2one(related="company_id.currency_id", string="Company Currency")
    total_sale = fields.Monetary('Total Sale', help='The total sale price',currency_field="company_currency_id",)
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
    category_id = fields.Many2one('freight.service.category', string="Service Category")

    @api.onchange('service_id', 'partner_id')
    def _onchange_partner_id(self):
        """Calculate the price of services"""
        for rec in self:
            if rec.service_id:
                if rec.partner_id:
                    if rec.service_id.line_ids:
                        for service in rec.service_id.line_ids:
                            if rec.partner_id == service.partner_id:
                                rec.sale = service.sale
                            else:
                                rec.sale = rec.service_id.sale_price
                    else:
                        rec.sale = rec.service_id.sale_price
                else:
                    rec.sale = rec.service_id.sale_price

    @api.onchange('qty', 'sale')
    def _onchange_qty(self):
        """Calculate the subtotal of route operation"""
        for rec in self:
            rec.total_sale = rec.qty * rec.sale

    @api.constrains('total_sale')
    def _check_total_sale(self):
        for rec in self:
            if rec.total_sale < 0:
                raise ValidationError("Total Sale cannot be negative.")


class Tracking(models.Model):
    """Tracking the freight order"""
    _name = 'freight.track'
    _description = 'Freight Track'

    source_loc_id = fields.Many2one('freight.port', string='Source Location',
                                    help='Select the source location of port')
    destination_loc_id = fields.Many2one('freight.port',
                                         string='Destination Location',
                                         help='Destination location of the port')
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('ocean', 'Ocean')], string='Transport',
                                      help='Transporting medium of the order')
    freight_id = fields.Many2one('freight.order', string='Freight Order',
                                 help='Reference from freight order')
    date = fields.Date(string='Date', help='Select the date')
    type = fields.Selection([('received', 'Received'),
                             ('delivered', 'Delivered')],
                            string='Received/Delivered',
                            help='Status of the order')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)





class ContainerTrackingXlsx(models.AbstractModel):
    _name = 'report.freight_management_system.container_tracking_xlsx_report'
    # _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, orders):

        sheet = workbook.add_worksheet('Container Tracking')

        # =========================
        # Formats
        # =========================

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 14,
            'border': 1,
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9EAD3',
            'border': 1,
            'align': 'center',
            'text_wrap': True,
        })

        normal_format = workbook.add_format({
            'border': 1,
        })

        date_format = workbook.add_format({
            'border': 1,
            'num_format': 'dd-mm-yyyy',
        })

        # =========================
        # Sheet Setup
        # =========================

        sheet.set_column('A:V', 20)

        sheet.merge_range(
            'A1:V1',
            'Container Tracking Sheet',
            title_format
        )

        headers = [
            'PO DATE',
            'PO No.',
            'Pi No.',
            'Pi date',
            'ETD',
            'ORIGIN',
            'CUSTOMER',
            'shipping line',
            'Container No',
            'SUPPLIER',
            'AGENT',
            'BL No.',
            'SUPPLIER INV NO.',
            'CURRENT STATUS',
            'ETA PORT',
            'ETA Toronto',
            'Amount',
            'Paid or no',
            'CUSTOMS',
            'TELEX',
            'PICK UP No',
            'Delivery Location',
        ]

        row = 2

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)

        row += 1

        for order in orders:

            for track in order.freight_track_ids:

                col = 0

                sheet.write(row, col, order.po_date or '', date_format)
                col += 1

                sheet.write(row, col, order.po_no or '', normal_format)
                col += 1

                sheet.write(row, col, order.pi_no or '', normal_format)
                col += 1

                sheet.write(row, col, order.pi_date or '', date_format)
                col += 1

                sheet.write(row, col, track.etd or '', date_format)
                col += 1

                sheet.write(row, col, track.origin or '', normal_format)
                col += 1

                sheet.write(row, col, order.customer_id.name or '', normal_format)
                col += 1

                sheet.write(row, col, track.shipping_line_id.name or '', normal_format)
                col += 1

                sheet.write(row, col, track.container_no or '', normal_format)
                col += 1

                sheet.write(row, col, order.supplier_id.name or '', normal_format)
                col += 1

                sheet.write(row, col, track.agent_id.name or '', normal_format)
                col += 1

                sheet.write(row, col, track.bl_no or '', normal_format)
                col += 1

                sheet.write(row, col, order.supplier_invoice_no or '', normal_format)
                col += 1

                sheet.write(row, col, track.current_status or '', normal_format)
                col += 1

                sheet.write(row, col, track.eta_port or '', date_format)
                col += 1

                sheet.write(row, col, track.eta_toronto or '', date_format)
                col += 1

                sheet.write(row, col, order.amount_total or 0.0, normal_format)
                col += 1

                sheet.write(
                    row,
                    col,
                    'Paid' if order.is_paid else 'No',
                    normal_format
                )
                col += 1

                sheet.write(row, col, track.customs or '', normal_format)
                col += 1

                sheet.write(row, col, track.telex or '', normal_format)
                col += 1

                sheet.write(row, col, track.pickup_no or '', normal_format)
                col += 1

                sheet.write(row, col, track.delivery_location or '', normal_format)

                row += 1
