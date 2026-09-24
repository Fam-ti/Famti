from odoo import models, fields


class ScrapGrade(models.Model):
    _name = "scrap.grade"
    _description = "Scrap Grade"
    _order = 'sequence, id'

    name = fields.Char(string="Scrap Grade",required=True)
    sequence = fields.Integer(string='Sequence', default=10)

    active = fields.Boolean(string="Active",default=True)

    _sql_constraints = [
        (
            "unique_scrap_grade_name",
            "unique(name)",
            "Scrap Grade name must be unique."
        )
    ]