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

    def test_ai_creator_role_enters_daily_queue(self):
        result = score_job({
            "title": "AI Creator Júnior",
            "location": "Brasil",
            "work_mode": "Remoto",
            "salary_min": 3500,
            "description": "Criação de aplicativos internos com IA generativa, Streamlit, Supabase e automação de processos.",
        })
        self.assertGreaterEqual(result.score, 70)
        self.assertIn(result.decision, {"AUTOAPLICAR", "REVISAR"})

    def test_machine_learning_engineer_is_blocked(self):
        result = score_job({
            "title": "Machine Learning Engineer",
            "location": "Brasil",
            "work_mode": "Remoto",
            "salary_min": 8000,
            "description": "Modelagem, MLOps, Python e IA generativa.",
        })
        self.assertEqual(result.decision, "BLOQUEADA")

    def test_remote_customer_service_enters_daily_queue(self):
        result = score_job({
            "title": "Assistente de Atendimento ao Cliente",
            "location": "Brasil",
            "work_mode": "Remoto",
            "salary_min": 2800,
            "description": "Atendimento, relacionamento, registro em CRM e suporte ao cliente de segunda a sexta.",
        })
        self.assertGreaterEqual(result.score, 70)
        self.assertIn(result.decision, {"AUTOAPLICAR", "REVISAR"})

    def test_small_business_inbound_consultant_enters_daily_queue(self):
        result = score_job({
            "title": "Consultora Comercial",
            "location": "Fortaleza",
            "work_mode": "Presencial",
            "salary_min": 3000,
            "description": "Atendimento inbound de pequenas empresas, relacionamento, propostas, carteira de clientes e CRM.",
        })
        self.assertGreaterEqual(result.score, 70)
        self.assertIn(result.decision, {"AUTOAPLICAR", "REVISAR"})

    def test_telemarketing_stays_blocked(self):
        result = score_job({
            "title": "Agente de Atendimento",
            "location": "Fortaleza",
            "work_mode": "Presencial",
            "salary_min": 2800,
            "description": "Atendimento por telemarketing em call center.",
        })
        self.assertEqual(result.decision, "BLOQUEADA")


if __name__ == "__main__":
    unittest.main()
