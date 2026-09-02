from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mo_serial_no = fields.Boolean(string="Is Metalize")
    is_consumables = fields.Boolean(string="Is Consumables")
    supplier_name = fields.Many2one('res.partner',string="Supplier Name")
    material_type = fields.Char(string="Film Type")
    type_reference = fields.Char(string="Type")
    film_type = fields.Selection([
        ('bare', 'Bare'),
        ('met', 'MET'),
        ('gold_met', 'GOLD MET'),
        ('pvdc', 'PVDC'),
        ('alox', 'Alox'),
    ], string='Film')
    film_description = fields.Text(string="Film Description")
    treatment_in = fields.Char(string="Treatment In")
    treatment_out = fields.Char(string="Treatment Out")
    treatment_in_selection = fields.Selection([
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

    treatment_out_selection = fields.Selection([
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
    product_reference_code = fields.Char(string="Product Code")
    mo_service_cost = fields.Boolean(string="Is Manufacturing Cost")
    density = fields.Float(string="Roll Density", help="This helps to categorise specific product.")
    thickness_val = fields.Float(string="Thickness",help="This helps to categorise specific product.")
    thickness_uom = fields.Selection(selection=[('guage','Guage'),('micron','Micron'),('mm','MM'),('mil','Mil')],default='micron',string="Thickness UOM")


    width_val = fields.Float(string="Width",help="This helps to categorise specific product.")
    width_uom = fields.Selection(selection=[('mm','MM'),('inch','Inch'),('mm','MM'),('mil','Mil')],default='inch',string="Width UOM")
    pallet_no = fields.Char(string="Pallet Number",help='The pallet no. which are received from vendor end.')
    length = fields.Float(string="Length",help='The length of the product.')
    no_of_joint = fields.Char(string="No. Of Joint")
    aging = fields.Char(string="Aging")
    received_date = fields.Datetime(string="Received Date")
    


class ProductProduct(models.Model):
    _inherit = "product.product"

    mo_serial_no = fields.Boolean(string="Is Metalize",related='product_tmpl_id.mo_serial_no')
    is_consumables = fields.Boolean(string="Is Consumables",related='product_tmpl_id.is_consumables')

    supplier_name = fields.Many2one('res.partner',string="Supplier Name",related='product_tmpl_id.supplier_name')
    film_description = fields.Text(string="Film Description",related='product_tmpl_id.film_description')
    material_type = fields.Char(string="Material Type",related='product_tmpl_id.material_type')
    type_reference = fields.Char(string="Type",related='product_tmpl_id.type_reference')
    film_type = fields.Selection([
        ('bare', 'Bare'),
        ('met', 'MET'),
        ('gold_met', 'GOLD MET'),
        ('pvdc', 'PVDC'),
        ('alox', 'Alox'),
    ], string='Film Type',related='product_tmpl_id.film_type')
    treatment_in = fields.Char(string="Treatment In",related='product_tmpl_id.treatment_in')
    treatment_out = fields.Char(string="Treatment Out",related='product_tmpl_id.treatment_out')
    treatment_in_selection = fields.Selection([
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
        ], string="Treatment IN",related='product_tmpl_id.treatment_in_selection')

    treatment_out_selection = fields.Selection([
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
        ], string="Treatment OUT",related='product_tmpl_id.treatment_out_selection')
    mo_service_cost = fields.Boolean(string="Is Manufacturing Cost",related='product_tmpl_id.mo_service_cost')
    density = fields.Float(string="Roll Density", help="This helps to categorise specific product.",related='product_tmpl_id.density')

    low_stock_alert_sent = fields.Boolean(
        string="Low Stock Alert Sent",
        default=False
    )
    thickness_val = fields.Float(string="Thickness",help="This helps to categorise specific product.",related='product_tmpl_id.thickness_val')
    thickness_uom = fields.Selection(selection=[('guage','Guage'),('micron','Micron'),('mm','MM'),('mil','Mil')],default='micron',string=" ",related='product_tmpl_id.thickness_uom')


    width_val = fields.Float(string="Width",help="This helps to categorise specific product.",related='product_tmpl_id.width_val')
    width_uom = fields.Selection(selection=[('mm','MM'),('inch','Inch'),('mm','MM'),('mil','Mil')],default='mm',string=" ",related='product_tmpl_id.width_uom')
    

    @api.model
    def check_low_stock_products(self):

        products = self.search([
            ('type', 'in', ['product', 'consu']),
            ('low_stock_alert_sent', '!=', True)
        ])

        low_stock_products = products.filtered(lambda p: p.qty_available < 20)
        print("low_stock_products==============",len(low_stock_products))

        if not low_stock_products:
            return

        group = self.env.ref('famti.group_inventory_dep_users', raise_if_not_found=False)
        if not group:
            return

        users = group.users.filtered(lambda u: u.email)
        if not users:
            return

        product_rows = ""
        for product in low_stock_products:
            product_rows += f"""
                <tr>
                    <td style="padding:8px;border:1px solid #ddd;">{product.default_code or '-'}</td>
                    <td style="padding:8px;border:1px solid #ddd;">{product.name}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:center;">{product.qty_available}</td>
                </tr>
            """

        body_html = f"""
            <p>Dear Inventory Team,</p>

            <p>The following products are below minimum stock level (20 units):</p>

            <table style="border-collapse:collapse;width:100%;">
                <thead>
                    <tr>
                        <th style="padding:8px;border:1px solid #ddd;background:#f2f2f2;">
                            Product Code
                        </th>
                        <th style="padding:8px;border:1px solid #ddd;background:#f2f2f2;">
                            Product
                        </th>
                        <th style="padding:8px;border:1px solid #ddd;background:#f2f2f2;text-align:center;">
                            Available Quantity
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {product_rows}
                </tbody>
            </table>

            <br/>
            <p>
                A purchase requisition has been generated for the above low-stock products.
                Please review the requisition and proceed with submission to the CFO for approval.
            </p>

            <p>Regards,<br/>Fam Ti</p>
        """

        email_to = ",".join(users.mapped('email'))

        mail_values = {
            'subject': 'Low Stock Alert - Multiple Products',
            'body_html': body_html,
            'email_to': email_to,
        }

        self.env['mail.mail'].create(mail_values).send()

        recovered_products = self.search([
            ('type', 'in', ['product', 'consu']),
            ('low_stock_alert_sent', '=', True)
        ]).filtered(lambda p: p.qty_available >= 20)

        recovered_products.write({'low_stock_alert_sent': False})
