from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval


class CostSheet(models.Model):
    _name = 'cost.sheet'
    _description = 'Cost Sheet'

    name = fields.Char(string="Cost Sheet No", required=True, copy=False, default="New")
    sale_order_id = fields.Many2one('sale.order', string="Sales Order",required=True)
    partner_id = fields.Many2one('res.partner', string="Customer",related='sale_order_id.partner_id',store=True,readonly=True)
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string="Quantity (KG)")
    line_ids = fields.One2many(
        'cost.sheet.line',
        'cost_sheet_id'
    )

    slit_line_ids = fields.One2many(
        'cost.sheet.line.slit',
        'cost_sheet_id'
    )

    raw_material_cost = fields.Float(string="Raw Material Cost / KG")
    metallization_cost = fields.Float(string="Metallization Cost / KG")
    slitting_cost = fields.Float(string="Slitting Cost / KG")
    packing_cost = fields.Float(string="Packing Cost / KG")
    logistics_cost = fields.Float(string="Logistics Cost / KG")

    wastage_percent = fields.Float(string="Wastage %")

    total_cost_per_kg = fields.Float(string="Total Cost / KG", compute="_compute_total_cost", store=True)

    total_cost = fields.Float(string="Total Cost", compute="_compute_total_cost", store=True)

    selling_price = fields.Float(string="Selling Price / KG")

    profit_per_kg = fields.Float(string="Profit / KG", compute="_compute_profit", store=True)

    total_profit = fields.Float(string="Total Profit", compute="_compute_profit", store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'Submitted to CFO'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'cost.sheet.sequence'
            ) or 'New'

        return super().create(vals)

    def action_cfo_approval(self):
        if self.state == 'draft':
            self.write({'state': 'to_approve'})

    def action_approve(self):
        if self.state == 'to_approve':
            self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_reset_to_draft(self):
        if self.state not in ['draft','to_approve']:
            self.write({'state': 'draft'})

    def action_calculate_metaliser(self):
        templates = self.env[
            'cost.sheet.template'
        ].search([])
        lines = []
        for temp in templates:
            lines.append((0, 0, {
                'name': temp.name,
                'title': temp.title,
                'code': temp.code,
                'uom': temp.uom,
                'default_value': temp.default_value,
                'formula': temp.formula,
                'sequence': temp.sequence,
            }))
        self.line_ids = [(5, 0, 0)] + lines


    def action_calculate_slitter(self):
        templates = self.env[
            'cs.slitted.template'
        ].search([])
        lines = []
        for temp in templates:
            lines.append((0, 0, {
                'name': temp.name,
                'title': temp.title,
                'code': temp.code,
                'uom': temp.uom,
                'default_value': temp.default_value,
                'formula': temp.formula,
                'sequence': temp.sequence,
            }))
        self.slit_line_ids = [(5, 0, 0)] + lines


    @api.depends('qty', 'wastage_percent', 'raw_material_cost',
                 'metallization_cost', 'slitting_cost',
                 'packing_cost', 'logistics_cost')
    def _compute_total_cost(self):
        for rec in self:

            base_cost = (
                    rec.raw_material_cost +
                    rec.metallization_cost +
                    rec.slitting_cost +
                    rec.packing_cost +
                    rec.logistics_cost
            )

            if rec.wastage_percent:
                net_qty = rec.qty * (1 - rec.wastage_percent / 100.0)
            else:
                net_qty = rec.qty

            rec.total_cost_per_kg = (base_cost * rec.qty) / net_qty if net_qty else 0
            rec.total_cost = rec.total_cost_per_kg * rec.qty

    @api.depends('selling_price', 'total_cost_per_kg', 'qty')
    def _compute_profit(self):
        for rec in self:
            rec.profit_per_kg = rec.selling_price - rec.total_cost_per_kg
            rec.total_profit = rec.profit_per_kg * rec.qty

class CostSheetLine(models.Model):
    _name = 'cost.sheet.line'

    cost_sheet_id = fields.Many2one(
        'cost.sheet'
    )
    template_id = fields.Many2one(
        'cost.sheet.template'
    )
    name = fields.Char()
    title = fields.Char()
    code = fields.Char()
    uom = fields.Char()
    default_value = fields.Float()
    formula = fields.Char()
    sequence = fields.Integer()


    def read(self, fields=None, load='_classic_read'):
        # Call normal read
        res = super().read(fields, load)
        self.compute_all()
        return res

    def compute_all(self):
        records = self.search([])
        context = {r.code: r.default_value for r in records if r.code}
        # Step 2: compute all formulas in sequence order
        for rec in records.sorted(key=lambda r: r.sequence):
            if rec.formula:
                try:
                    value = safe_eval(rec.formula, context)
                    rec.default_value = value
                    context[rec.code] = value
                except Exception:
                    rec.default_value = 0



class CostSheetLineSlit(models.Model):
    _name = 'cost.sheet.line.slit'

    cost_sheet_id = fields.Many2one(
        'cost.sheet'
    )
    template_id = fields.Many2one(
        'cs.slitted.template'
    )
    name = fields.Char()
    title = fields.Char()
    code = fields.Char()
    uom = fields.Char()
    default_value = fields.Float()
    formula = fields.Char()
    sequence = fields.Integer()


    def read(self, fields=None, load='_classic_read'):
        # Call normal read
        res = super().read(fields, load)
        self.compute_all()
        return res

    def compute_all(self):
        records = self.search([])
        context = {r.code: r.default_value for r in records if r.code}
        # Step 2: compute all formulas in sequence order
        for rec in records.sorted(key=lambda r: r.sequence):
            if rec.formula:
                try:
                    value = safe_eval(rec.formula, context)
                    rec.default_value = value
                    context[rec.code] = value
                except Exception:
                    rec.default_value = 0