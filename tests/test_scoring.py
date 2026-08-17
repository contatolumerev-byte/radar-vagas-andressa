import unittest

from scoring import score_job


class ScoringTest(unittest.TestCase):
    def test_remote_customer_success_is_autoapply(self):
        result = score_job({
            "title": "Analista de Customer Success",
            "location": "Brasil",
            "work_mode": "Remoto",
            "salary_min": 3200,
            "description": "Onboarding, retenção e relacionamento com carteira de clientes via CRM.",
        })
        self.assertEqual(result.decision, "AUTOAPLICAR")
        self.assertGreaterEqual(result.score, 85)

    def test_hunting_is_blocked(self):
        result = score_job({
            "title": "Consultora Comercial Hunter",
            "location": "Fortaleza",
            "work_mode": "Presencial",
            "salary_min": 3000,
            "description": "Hunting e cold call.",
        })
        self.assertEqual(result.decision, "BLOQUEADA")
        self.assertTrue(result.blocks)

    def test_low_salary_is_blocked(self):
        result = score_job({
            "title": "Assistente Comercial",
            "location": "Fortaleza",
            "work_mode": "Presencial",
            "salary_min": 2200,
            "description": "Atendimento inbound e pós-venda.",
        })
        self.assertEqual(result.decision, "BLOQUEADA")

    def test_presential_outside_fortaleza_is_blocked(self):
        result = score_job({
            "title": "Analista de Relacionamento",
            "location": "São Paulo",
            "work_mode": "Presencial",
            "salary_min": 3500,
            "description": "Relacionamento e retenção.",
        })
        self.assertEqual(result.decision, "BLOQUEADA")

    def test_adjacent_operations_role_enters_daily_review(self):
        result = score_job({
            "title": "Analista de Operações Júnior",
            "location": "Brasil",
            "work_mode": "Remoto",
            "salary_min": 3500,
            "description": "Gestão de processos, projetos, indicadores e dashboards em Excel.",
        })
        self.assertGreaterEqual(result.score, 70)
        self.assertIn(result.decision, {"AUTOAPLICAR", "REVISAR"})

    def test_revops_role_is_prioritized(self):
        result = score_job({
            "title": "Analista de RevOps Júnior",
            "location": "Brasil",
            "work_mode": "Remoto",
            "salary_min": 4500,
            "description": "CRM, HubSpot, indicadores, automação e processos comerciais.",
        })
        self.assertEqual(result.decision, "AUTOAPLICAR")


if __name__ == "__main__":
    unittest.main()
