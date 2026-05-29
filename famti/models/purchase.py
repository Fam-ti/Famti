from odoo import api, fields, models
from odoo.exceptions import UserError


class Purchase(models.Model):
    _inherit = "purchase.order"

    # state = fields.Selection([
    #     ('draft', 'RFQ'),
    #     ('sent', 'RFQ Sent'),
    #     ('to approve', 'To Approve'),
    #     ('cfo_rejected', 'CFO Rejected'),
    #     ('purchase', 'Purchase Order'),
    #     ('done', 'Locked'),
    #     ('cancel', 'Cancelled')
    # ], string='Status', readonly=True, index=True, copy=False, default='draft')
    state = fields.Selection(
        selection_add=[('cfo_rejected', 'CFO Rejected')]
    )
    
    vendor_street = fields.Char()
    vendor_street2 = fields.Char()
    vendor_city = fields.Char()
    vendor_state_id = fields.Many2one('res.country.state')
    vendor_zip = fields.Char()
    vendor_country_id = fields.Many2one('res.country')
    vendor_vat = fields.Char()
    vendor_email = fields.Char(string="Email")
    vendor_phone = fields.Char(string="Contact")
    is_tolling = fields.Boolean(string='Is Tolling?')
    logo = fields.Image("Logo", max_width=1920, max_height=1920, default=lambda self: self.env.company.logo)

    remarks = fields.Text("Remarks")
    freight_ids = fields.One2many(
        'freight.order',
        'purchase_id',
        string="Freight Orders"
    )

    freight_count = fields.Integer(
        string="Freight Count",
        compute="_compute_freight_count"
    )

    po_type = fields.Selection([
        ('sample', 'Sample'),
        ('normal', 'Normal'),
        ('tolling', 'Tolling'),
        ('fgf', 'FGF'),
    ], string='PO Type', tracking=True, default='normal')
    due_date = fields.Date(string="Due Date")
    advance_amount = fields.Float(string="Advance Amount")
    po_expense_ids = fields.Many2many('hr.expense','po_expense_rel','po_id',           
        'expense_id',string='Expenses')


    def _compute_freight_count(self):
        for order in self:
            order.freight_count = len(order.freight_ids)

    def action_view_freight_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "famti.freight_order_action"
        )
        action['domain'] = [('purchase_id', '=', self.id)]
        action['context'] = {'default_purchase_id': self.id}

        return action

    def button_approve(self, force=False):
        result = super(Purchase, self).button_approve(force=force)
        self._create_freight_cost()
        return result

    def _create_freight_cost(self):
        freight = self.env['freight.order']
        freightorderline = self.env['freight.order.line']
        loading_port_id = self.env['freight.port'].search([])[0]
        discharging_port_id = self.env['freight.port'].search([])[0]
        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
            line_vals = []
            for line in order.order_line:
                line_vals.append((0, 0, {
                    'product_id': line.product_id.id,
                    'weight': line.product_qty,
                    'billing_type': 'weight',
                    'price': line.price_unit,
                }))

            freight.create([{'shipper_id': order.partner_id.id, 'type': 'import', 'transport_type': 'land','loading_port_id': loading_port_id.id,
                             'discharging_port_id':discharging_port_id.id,'agent_id':self.env.user.partner_id.id,'purchase_id':order.id,
                             'expected_date':order.date_planned,'incoterm_id':order.incoterm_id.id,
                             'order_ids': line_vals,'consignee_id': self.env.company.partner_id.id,}])
        return

    @api.onchange('partner_id')
    def _onchange_partner_id_address(self):
        if self.partner_id:
            self.vendor_street = self.partner_id.street
            self.vendor_street2 = self.partner_id.street2
            self.vendor_city = self.partner_id.city
            self.vendor_state_id = self.partner_id.state_id
            self.vendor_zip = self.partner_id.zip
            self.vendor_country_id = self.partner_id.country_id
            self.vendor_vat = self.partner_id.vat
            self.vendor_email = self.partner_id.email
            self.vendor_phone = self.partner_id.phone
    
    def action_rfq_send(self):
        for order in self:
            if not order.order_line:
                raise UserError(
                    "You cannot send the email without adding at least one order line."
                )
        return super().action_rfq_send()

    def action_send_for_cfo_approval(self):
        for order in self:
            if not order.order_line:
                raise UserError(
                    "Purchase Order must have at least one order line.")

            if order.partner_id.state == 'certificate_expired':
                raise UserError(
                    f"Cannot send for CFO approval. Vendor '{order.partner_id.name}' certificate has expired. Please renew it."
                )

        self.state='to approve'

    def action_reject_coa(self):
        self.state = 'cancel'


    def button_confirm(self):
        if not self.env.user.has_group('purchase.group_purchase_manager'):
            raise  UserError("You are not allowed to process this purchase. Please send to 'CFO' for approval")
        return super().button_confirm()

    @api.model
    def create(self, vals):
        if not vals.get('notes'):
            vals['notes'] = """
                <p><strong>Terms & Conditions:</strong></p>

                <ul>
                <li>Invoice each P.O. separately in duplicate showing the above P.O. number and shipping information.</li>
                <li>All duty and/or taxes must be shown separately on invoice where applicable.</li>
                <li>This order is subject to the terms and conditions stated.</li>
                </ul>
                """
        return super().create(vals)



class PurchaseOrderLine(models.Model):
    _inherit = ["purchase.order.line"]

    weight_val = fields.Float(string="Weight",help="This helps to categorise specific product.")
    weight_uom = fields.Selection(selection=[
                                        ('kg', 'Kg'),
                                        ('lbs', 'Lbs'),
                                        ('gm', 'Gm'),
                                        ],required=True,default='kg',string=" ")
    thickness_val = fields.Float(string="Thickness",help="This helps to categorise specific product.")
    thickness_uom = fields.Selection(selection=[('guage','Guage'),('micron','Micron'),('mm','MM'),('mil','Mil')],default='micron',string=" ")


    width_val = fields.Float(string="Width",help="This helps to categorise specific product.")
    width_uom = fields.Selection(selection=[('mm','MM'),('inch','Inch'),('mm','MM'),('mil','Mil')],default='mm',string=" ")
    core_id = fields.Selection(selection=[('3','3 Inch'),('6','6 Inch')],string="Core")
    category = fields.Char(string="Film Category",  help="This helps to categorise specific product.")
    film = fields.Char(string="Film", help="Product Film.")
    film_type = fields.Char(string="Film Type", help="Film Type")
    length_val = fields.Float(string="Length", help="Product Length")
    length_uom = fields.Selection(selection=[('m','M'),('feet','Feet')],default='feet',string=" ")
    # uom_conv_id = fields.Many2one('uom.convert.wizard',string="UOM Conversion Wizard")
    pieces = fields.Float(string="Pieces")

    description = fields.Text(string="Product Description")
    remarks = fields.Text(string="Remarks")

    treatment_in = fields.Selection([
            ('corona', 'Corona'),
            ('met_corona', 'Met on Corona'),
            ('met_chemical', 'Met on Chemical'),
            ('met_plain', 'Met on Plain'),
            ('plain', 'Plain'),
            ('pvdc', 'PVDC COATED'),
            ('soft_touch', 'SOFT TOUCH'),
            ('alox', 'Top coat Alox'),
        ], string="Treatment IN")

    treatment_out = fields.Selection([
            ('acrylic', 'ACRYLIC'),
            ('corona', 'Corona'),
            ('met_plain', 'Met on Plain'),
            ('met_corona', 'Met on Corona'),
            ('met_corona_out', 'Metallized on Corona Outside'),
            ('met_chemical', 'Metallized on Chemical'),
            ('plain', 'Plain'),
            ('pvdc_out', 'PVDC COATED'),
        ], string="Treatment OUT")

    rolls_uom_id = fields.Many2one('uom.uom', string="UoM",domain="[('name','=','rolls')]",
        default=lambda self: self.env['uom.uom'].search([('name','=','rolls')], limit=1))


    def action_open_uom_conversion(self):
        print(f'-line 46--------{self}--{self.ids}')
        return {
            'name': 'Purchase Order Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'uom.convert.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self,
            }
        }

    @api.onchange('product_id')
    def _onchange_product_id_set_film_description(self):
        if self.product_id:
            if self.product_id.film_description:
                self.description = self.product_id.film_description
        
    @api.model
    def create(self, vals):
        record = super().create(vals)

        if record.order_id.po_type == 'sample':
            record.price_unit = 0

        return record
    
    def write(self, vals):
        for rec in self:
            new_vals = vals.copy()

            if rec.order_id.po_type == 'sample':
                new_vals['price_unit'] = 0

            super(PurchaseOrderLine, rec).write(new_vals)

        return True
