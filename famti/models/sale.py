from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('to_approve', 'To Approve'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, tracking=True, default='draft')
    logo = fields.Image("Logo", max_width=1920, max_height=1920, default=lambda self: self.env.company.logo)

    partner_credit_limit = fields.Monetary(
        string="Credit Limit",
        currency_field='currency_id',
        compute="_compute_partner_credit_info",
        store=False
    )

    partner_outstanding = fields.Monetary(
        string="Outstanding Amount",
        currency_field='currency_id',
        compute="_compute_partner_credit_info",
        store=False
    )

    partner_lc_document = fields.Binary(
        related='partner_id.lc_document',
        readonly=True
    )

    customer_email = fields.Char(string="Email")
    customer_phone = fields.Char(string="Contact")
    valuation_line_ids = fields.One2many('sale.mo.valuation', 'sale_id', string="MO Valuation")
    mo_ids = fields.One2many(
	'mrp.production',
	'origin',
	string="Manufacturing Orders",
	compute="_compute_mo_ids"
    )

    so_type = fields.Selection([
        ('sample', 'Sample'),
        ('normal', 'Normal'),
        ('tolling', 'Tolling'),
        ('fgf', 'FGF'),
    ], string='SO Type', tracking=True, default='normal')

    mo_count = fields.Integer(
        string="Manufacturing Orders",
        compute="_compute_mo_count"
    )
    remarks = fields.Text(string="Remarks")

    freight_ids = fields.One2many(
        'freight.order',
        'sale_id',
        string="Freight Orders"
    )

    freight_count = fields.Integer(
        string="Freight Count",
        compute="_compute_freight_count"
    )

    buyer_po_number = fields.Char( string="Buyer PO Number")
    buyer_po_date = fields.Date(string="Buyer PO Date")
    expected_date = fields.Date(string='Expected Date', help='The expected date'
                                                             'of the order', required=False)

    def _compute_freight_count(self):
        for order in self:
            order.freight_count = len(order.freight_ids)

    def action_view_freight_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "famti.freight_order_action"
        )
        action['domain'] = [('sale_id', '=', self.id)]
        action['context'] = {'default_sale_id': self.id}
        return action

    def _compute_mo_count(self):
        for order in self:
            order.mo_count = self.env['mrp.production'].search_count(
                [('sale_id', '=', order.id)]
            )


    @api.depends('partner_id')
    def _compute_partner_credit_info(self):
        for order in self:
            partner = order.partner_id
            order.partner_credit_limit = partner.credit_limit or 0.0
            order.partner_outstanding = partner.credit or 0.0
            order.partner_lc_document = partner.lc_document or False


    def _get_unpaid_invoices(self):
        self.ensure_one()
        return self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('company_id', '=', self.company_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
        ])

    def _check_credit_and_overdue(self):
        self.ensure_one()
        partner = self.partner_id

        unpaid_invoices = self._get_unpaid_invoices()
        outstanding = sum(unpaid_invoices.mapped('amount_residual'))
        if partner.credit_limit and outstanding + self.amount_total > partner.credit_limit:
            return (
                f"The customer's credit limit of {partner.credit_limit} has been exceeded."
                f"The current outstanding amount is {outstanding},"
                f"and the value of this sales order is {self.amount_total}."
            )

        today = date.today()
        for inv in unpaid_invoices:
            if inv.invoice_date_due < today:
                overdue_days = (today - inv.invoice_date_due).days
                if overdue_days > partner.credit_grace_days:
                    return (
                        f"The customer has overdue invoices beyond the allowed grace period."
                        f"Invoice {inv.name} is overdue by {overdue_days} days."
                    )

        return False
        


    def action_cfo_approval(self):
         for order in self:
            if not order.order_line:
                raise UserError("Sales Order must have at least one order line.")
            self.write({'state': 'to_approve'})

    def action_approve(self):
        for order in self:
            issue = order._check_credit_and_overdue()
            if issue:
                raise UserError(issue)
            else:
                if order.state == 'to_approve':
                    order.write({'state': 'draft'})

            order.action_confirm()


    def action_reject(self):
        return self.action_cancel()

    def action_confirm(self):
        if self.state == 'to_approve' and not self.env.user.has_group(
                'famti.group_cheif_financial_officer'):
            raise UserError("Sale Order requires CFO approval.")
        # return super().action_confirm()
        res = super().action_confirm()
        self._create_freight_cost()
        return res
    
    def _create_freight_cost(self):
        freight = self.env['freight.order']
        freightorderline = self.env['freight.order.line']
        loading_port_id = self.env['freight.port'].search([])[0]
        discharging_port_id = self.env['freight.port'].search([])[0]
        for order in self.filtered(lambda so: so.state in ('sale', 'done')):
            line_vals = []
            for line in order.order_line:
                line_vals.append((0, 0, {
                    'product_id': line.product_id.id,
                    'weight': line.product_uom_qty,
                    'billing_type': 'weight',
                    'price': line.price_unit,
                }))

            freight.create([{
                'shipper_id': order.partner_id.id, 
                'type': 'export', 
                'transport_type': 'land',
                'loading_port_id': loading_port_id.id,
                'discharging_port_id':discharging_port_id.id,
                'agent_id':self.env.user.partner_id.id,
                'sale_id': order.id,
                'expected_date':order.expected_date,
                'incoterm_id':order.incoterm.id,
                'order_ids': line_vals,
                'consignee_id': order.partner_id.id,}])
                
        return

    def action_view_mo(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Orders',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('sale_id', '=', self.id)],
            'context': {'default_sale_id': self.id},
        }


    def action_view_manufacturing_cost(self):
        self.ensure_one()

        service_product = self.env['product.product'].search([
            ('type', '=', 'service'),
            ('mo_service_cost', '=', True)
        ], limit=1)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Cost',
            'res_model': 'manufacturing.cost.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_id': self.id,
                'default_manufacturing_service_id': service_product.id,
            }
        }


    @api.onchange('partner_id')
    def _onchange_partner_set_terms(self):
        if self.partner_id:
            self.note = f"""
                <p><strong>DELIVERY:</strong></p>
                <p>
                1. SHIPMENT - ETD - <br/>
                2. DELIVER TO ADDRESS MENTIONED ABOVE <br/>
                3. THE PRODUCTS IS AS PER OUR TDS WHICH ARE INDICATIVE VALUES <br/>
                4. SUBJECT TO JURISDICTION IN TORONTO, CANADA <br/>
                5. DELAYED PAYMENT WILL BE CHARGED @ 18% P.A <br/>
                6. LABEL INSTRUCTIONS - <br/>
                7. PACKING INSTRUCTIONS -
                </p>

                <p><strong>CONTACT DETAILS:</strong></p>
                <p>
                Customer Name: {self.partner_id.name or ''} <br/>
                Email: {self.partner_id.email or ''} <br/>
                Phone Number: {self.partner_id.phone or ''}
                </p>
                """

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()

        bank_journal = self.env['account.journal'].search([
            ('type', '=', 'bank')
        ], limit=1)

        bank_details = ""

        if bank_journal and bank_journal.bank_account_id:
            bank = bank_journal.bank_account_id.bank_id
            print("bank id",bank)

            bank_details = f"""
            <p><strong>Payment Method:</strong></p>

            <p>
            1. Wire Transfer:<br/>
            {self.company_id.name} BANKING DETAILS<br/>
            BANK NAME: {bank.name}<br/>
            ACCOUNT NO.: {bank_journal.bank_account_id.acc_number}<br/>
            TRANSIT NO.: {bank_journal.bank_account_id.transit_no or ''}<br/>
            INST. NO.: {bank_journal.bank_account_id.institution_no or ''}
            </p>

            <p>
            2. By Cheque:<br/>
            Please make a cheque payment to {self.company_id.name}
            and kindly mention invoice number.
            </p>
            """

        invoice_vals['narration'] = bank_details

        return invoice_vals
    
    def action_open_sales_excel_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Excel Report',
            'res_model': 'sale.report.wizard',
            'view_mode': 'form',
            'target': 'new',
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

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

    thickness_val = fields.Float(string="Thickness",help="This helps to categorise specific product.")
    thickness_uom = fields.Selection(selection=[('guage','Guage'),('micron','Micron'),('mm','MM'),('mil','Mil')],default='micron',string=" ")
    width_val = fields.Float(string="Width",help="This helps to categorise specific product.")
    width_uom = fields.Selection(selection=[('mm','MM'),('inch','Inch'),('mm','MM'),('mil','Mil')],default='mm',string=" ")
    core_id = fields.Selection(selection=[('3','3 Inch'),('6','6 Inch')],string="Core")
    length_val = fields.Float(string="Length", help="Product Length")
    length_uom = fields.Selection(selection=[('m','M'),('feet','Feet')],default='feet',string=" ")
    pieces = fields.Float(string="Pieces")
    mo_price = fields.Float(string="MO Price")
    rolls_uom_id = fields.Many2one('uom.uom', string="UoM",domain="[('name','=','rolls')]",
        default=lambda self: self.env['uom.uom'].search([('name','=','rolls')], limit=1))

    @api.model
    def create(self, vals):
        record = super().create(vals)

        if record.order_id.so_type == 'sample':
            record.write({'price_unit': 0})  

        return record

    def write(self, vals):
        for rec in self:
            new_vals = vals.copy()

            if rec.order_id.so_type == 'sample':
                new_vals['price_unit'] = 0

            super(SaleOrderLine, rec).write(new_vals)

        return True

class SaleMoValuation(models.Model):
    _name = 'sale.mo.valuation'
    _description = 'MO Valuation Lines'

    sale_id = fields.Many2one('sale.order', string="Sale Order")

    date = fields.Datetime(string="Date")
    reference = fields.Char(string="Reference")
    product_id = fields.Many2one('product.product', string="Product")
    mo_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order"
    )
    quantity = fields.Float(string="Quantity")
    unit_cost = fields.Float(string="Unit Cost")
    total_cost = fields.Float(string="Total Cost")

