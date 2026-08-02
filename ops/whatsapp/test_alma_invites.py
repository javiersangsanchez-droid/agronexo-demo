import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import alma_invites as alma


class AlmaInvitesTest(unittest.TestCase):
    def test_normalizes_colombian_number(self):
        self.assertEqual(alma.normalize_phone('+57 300 123 4567'), '573001234567')

    def test_rejects_short_number(self):
        with self.assertRaises(ValueError):
            alma.normalize_phone('123')

    def test_template_is_marketing_spanish_and_discloses_demo(self):
        payload = alma.template_definition()
        body = payload['components'][0]['text']
        self.assertEqual(payload['category'], 'MARKETING')
        self.assertEqual(payload['language'], 'es_CO')
        self.assertIn('versión demo', body)
        self.assertIn('Javier Sánchez', body)
        self.assertIn('{{1}}', body)
        self.assertIn('{{2}}', body)

    def test_invitation_uses_approved_template(self):
        payload = alma.invitation_payload('+57 300 123 4567', 'María', alma.DEFAULT_LINK)
        self.assertEqual(payload['type'], 'template')
        self.assertEqual(payload['template']['name'], alma.TEMPLATE_NAME)
        parameters = payload['template']['components'][0]['parameters']
        self.assertEqual(parameters[0]['text'], 'María')
        self.assertEqual(parameters[1]['text'], alma.DEFAULT_LINK)

    def test_does_not_print_token_in_payload(self):
        payload = alma.invitation_payload('573001234567', 'Ana', alma.DEFAULT_LINK)
        self.assertNotIn('token', json.dumps(payload).lower())


if __name__ == '__main__':
    unittest.main()
