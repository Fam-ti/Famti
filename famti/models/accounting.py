from odoo import models, api, fields
import requests

class AccountMove(models.Model):
    _inherit = 'account.move'

    so_type = fields.Selection(
        related="invoice_line_ids.sale_line_ids.order_id.so_type",
        store=True
    )
    po_type = fields.Selection(
        related="invoice_line_ids.purchase_line_id.order_id.po_type",
        store=True
    )
    ship_via = fields.Selection([
        ('fedex', 'FedEx'),
        ('ups', 'UPS'),
        ('dhl', 'DHL'),
        ('usps', 'USPS'),
        ('canada_post', 'Canada Post'),
        ('pickup', 'Customer Pickup'),
        ('other', 'Other'),
    ], string="Ship Via")

    quickbook_id = fields.Char(string="QuickBook Id",index=True)
    gst_number = fields.Char(string='GST Number',related='partner_id.vat',store=True,readonly=True)
    buyer_po_number = fields.Char(string="Buyer PO Number")


    _sql_constraints = [
        ('quickbook_id_unique', 'unique(quickbook_id)', 'QuickBooks ID must be unique!')
    ]

    def action_send_to_qb(self):
        config = self.env['quickbook.config'].search([('status','=','connected')], limit=1)

        if not config:
            raise Exception("QuickBooks not connected!")
        for invoice in self:
            # if invoice.move_type != 'out_invoice':
            #     continue
            qb_invoice = config.create_or_update_qb_invoice(invoice)
            invoice.quickbook_id = qb_invoice.get('Id')

    def _get_bank_payment_html(self):
        bank_journal = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not bank_journal or not bank_journal.bank_account_id:
            return ""

        bank = bank_journal.bank_account_id.bank_id

        return f"""
            <p><strong>Payment Method:</strong></p>

            <p>
            1. Wire Transfer:<br/>
            {self.env.company.name} BANKING DETAILS<br/>
            BANK NAME: {bank.name}<br/>
            ACCOUNT NO.: {bank_journal.bank_account_id.acc_number}<br/>
            TRANSIT NO.: {bank_journal.bank_account_id.transit_no or ''}<br/>
            INST. NO.: {bank_journal.bank_account_id.institution_no or ''}
            </p>

            <p>
            2. By Cheque:<br/>
            Please make a cheque payment to {self.env.company.name}
            and kindly mention invoice number.
            </p>
            """

    @api.model
    def create(self, vals):
        if vals.get('move_type') == 'out_invoice':
            vals['narration'] = self._get_bank_payment_html()

        return super().create(vals)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pieces = fields.Float(string="Pieces", related="sale_line_ids.pieces", store=True)
    pieces_po = fields.Float(string="Pieces", related="purchase_line_id.pieces", store=True)
    rolls_uom_id = fields.Many2one('uom.uom', string="UoM",domain="[('name','=','rolls')]",
        default=lambda self: self.env['uom.uom'].search([('name','=','rolls')], limit=1))
    description = fields.Char("Description")
    treatment_in = fields.Selection([
        ('corona', 'Corona'),
        ('met_corona', 'Metalizzed on Corona'),
        ('met_chemical', 'Metallized on Chemical'),
        ('met_plain', 'Metallized on Plain'),
        ('plain', 'Plain'),
        ('pvdc', 'PVDC COATED'),
        ('soft_touch', 'SOFT TOUCH'),
        ('alox', 'Top coat Alox'),
        ('chemical_coat', 'Chemical Coated'),
        ('met_copolymer', 'Met on Copolymer'),
        ('acrylic', 'ACRYLIC'),
        ('copolymer', 'Copolymer'),
        ('special_chemical', 'Special Chemical'),
    ], string="Treatment IN")

    treatment_out = fields.Selection([
        ('acrylic', 'ACRYLIC'),
        ('corona', 'Corona'),
        ('met_plain', 'Metallized on Plain'),
        ('met_corona', 'Metallized on Corona'),
        ('met_chemical', 'Metallized on Chemical'),
        ('plain', 'Plain'),
        ('pvdc_out', 'PVDC COATED'),
        ('soft_touch', 'SOFT TOUCH'),
        ('alox', 'Top coat Alox'),
        ('chemical_coat', 'Chemical Coated'),
        ('met_copolymer', 'Met on Copolymer'),
        ('copolymer', 'Copolymer'),
        ('special_chemical', 'Special Chemical'),
    ], string="Treatment OUT")

    thickness_val = fields.Float(string="Thickness", help="This helps to categorise specific product.")
    thickness_uom = fields.Selection(selection=[('guage', 'Guage'), ('micron', 'Micron'), ('mm', 'MM'), ('mil', 'Mil')],
                                     default='micron', string=" ")
    width_val = fields.Float(string="Width", help="This helps to categorise specific product.")
    width_uom = fields.Selection(selection=[('mm', 'MM'), ('inch', 'Inch'), ('mm', 'MM'), ('mil', 'Mil')], default='mm',
                                 string=" ")
    core_id = fields.Selection(selection=[('3', '3 Inch'), ('6', '6 Inch')], string="Core")
    length_val = fields.Float(string="Length", help="Product Length")
    length_uom = fields.Selection(selection=[('m', 'M'), ('feet', 'Feet')], default='feet', string=" ")
    remarks = fields.Text(string="Remarks")



    class AccountTaxPython(models.Model):
        _inherit = "account.tax"

        qb_tax_code = fields.Char(string="QuickBooks Tax Code")

