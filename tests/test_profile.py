import unittest

from resume_profile import headline_for_job, resume_header


class ProfileHeadlineTest(unittest.TestCase):
    def test_customer_success_headline(self):
        headline = headline_for_job({
            "title": "Analista de Customer Success",
            "description": "Relacionamento B2B, adoção e retenção em plataforma SaaS.",
        })
        self.assertEqual(headline, "Customer Success | Customer Experience | Relacionamento B2B | SaaS")

    def test_sales_ops_headline(self):
        headline = headline_for_job({
            "title": "Analista de Sales Operations",
            "description": "Gestão do CRM e indicadores do funil comercial.",
        })
        self.assertEqual(headline, "Revenue Operations | Sales Operations | CRM | Inteligência Comercial")

    def test_generic_role_uses_description(self):
        headline = headline_for_job({
            "title": "Analista Júnior",
            "description": "Mapeamento de processos, projetos e indicadores operacionais.",
        })
        self.assertEqual(headline, "Projetos | Processos | Operações | Indicadores")

    def test_contact_information_stays_fixed(self):
        header = resume_header({"title": "Analista de CRM", "description": "Lifecycle"})
        self.assertEqual(header["email"], "contato.andressafreire@gmail.com")
        self.assertEqual(header["location"], "Fortaleza – CE")


if __name__ == "__main__":
    unittest.main()
