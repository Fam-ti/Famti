from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

#Metaliser Template with codes--------------------
class CostSheetTemplate(models.Model):
    _name = 'cost.sheet.template'
    _description = 'Cost Sheet Template (ROWS)'

    name = fields.Char(required=True)
    title = fields.Char(string="Title")
    code = fields.Char(string="Code")
    uom = fields.Char(string="UOM")
    default_value = fields.Float(string="Default Value",digits=(16, 10))
    formula = fields.Char(string="Formula")
    sequence = fields.Integer(string="Sequence")
    is_computed = fields.Boolean(default=False)
    cost_sheet_id = fields.Many2one('cost.sheet',string="Cost Sheet",ondelete='cascade')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Code must be unique!')
    ]

    def read(self, fields=None, load='_classic_read'):
        res = super().read(fields, load)
        self.compute_all()
        return res

    def compute_all(self):
        records = self.search([])
        context = {r.code: r.default_value for r in records if r.code}
        for rec in records.sorted(key=lambda r: r.sequence):
            if rec.formula:
                try:
                    value = safe_eval(rec.formula, context)
                    rec.default_value = value
                    context[rec.code] = value
                except Exception:
                    rec.default_value = 0


class CSSlittedTemplate(models.Model):
    _name = 'cs.slitted.template'
    _description = 'Cost Sheet Slitted Template'

    name = fields.Char(required=True)
    title = fields.Char(string="Title")
    code = fields.Char(string="Code")
    uom = fields.Char(string="UOM")
    default_value = fields.Float(string="Default Value",digits=(16, 10))
    formula = fields.Char(string="Formula")
    sequence = fields.Integer(string="Sequence")
    is_computed = fields.Boolean(default=False)
    average_cost = fields.Char(string="Average cost/kg (CAD)")
    cost_kgs = fields.Char(string="Cost/kg (CAD)")

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Code must be unique!')
    ]

    def read(self, fields=None, load='_classic_read'):
        res = super().read(fields, load)
        self.compute_all()
        return res

    def compute_all(self):
        records = self.search([])
        context = {r.code:r.default_value for r in records if r.code }

        for rec in records.sorted(key=lambda r: r.sequence):
            if rec.formula:
                try:
                    value = safe_eval(rec.formula, context)
                    rec.default_value = value
                    context[rec.code] = value
                except Exception:
                    rec.default_value = 0
                    context[rec.code] = 0

            if rec.average_cost:
                try:
                    avg_value = safe_eval(rec.average_cost, context)
                    rec.average_cost = avg_value
                except Exception:
                    rec.average_cost = 0

            if rec.cost_kgs:
                try:
                    cost_value = safe_eval(rec.cost_kgs, context)
                    rec.cost_kgs = cost_value
                except Exception:
                    rec.cost_kgs = 0



