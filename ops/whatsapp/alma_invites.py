#!/usr/bin/env python3
"""Register and send the approved ALMA AgroNexo WhatsApp Cloud template.

Secrets are read from the isolated almaagronexo profile .env and are never
printed. This script deliberately requires an approved Meta template for
outbound-first messages outside the 24-hour service window.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_ENV = Path('/opt/data/profiles/almaagronexo/.env')
DEFAULT_LINK = 'https://javiersangsanchez-droid.github.io/agronexo-demo/'
TEMPLATE_NAME = 'invitacion_demo_agronexo'
LANGUAGE = 'es_CO'
GRAPH_VERSION = 'v20.0'


def load_env(path: Path) -> dict[str, str]:
    values = dict(os.environ)
    if path.exists():
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            values.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return values


def normalize_phone(value: str) -> str:
    number = re.sub(r'\D', '', value)
    if not 10 <= len(number) <= 15:
        raise ValueError('El destinatario debe incluir código de país y tener entre 10 y 15 dígitos')
    return number


def graph_request(url: str, token: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors='replace')
        raise RuntimeError(f'Meta Graph API respondió HTTP {exc.code}: {body}') from exc


def template_definition() -> dict:
    return {
        'name': TEMPLATE_NAME,
        'language': LANGUAGE,
        'category': 'MARKETING',
        'components': [
            {
                'type': 'BODY',
                'text': (
                    'Hola {{1}}. Soy ALMA, asistente de AgroNexo. Javier Sánchez me pidió '
                    'compartirte una versión demo para que la analices y luego le cuentes tus '
                    'observaciones. Puedes revisarla aquí: {{2}}. Responde este mensaje y con '
                    'gusto te guío por la demostración.'
                ),
                'example': {'body_text': [['María', DEFAULT_LINK]]},
            }
        ],
    }


def invitation_payload(recipient: str, name: str, link: str) -> dict:
    return {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': normalize_phone(recipient),
        'type': 'template',
        'template': {
            'name': TEMPLATE_NAME,
            'language': {'code': LANGUAGE},
            'components': [{
                'type': 'body',
                'parameters': [
                    {'type': 'text', 'text': name},
                    {'type': 'text', 'text': link},
                ],
            }],
        },
    }


def require(env: dict[str, str], *keys: str) -> list[str]:
    missing = [key for key in keys if not env.get(key)]
    if missing:
        raise RuntimeError('Faltan credenciales en el perfil ALMA: ' + ', '.join(missing))
    return [env[key] for key in keys]


def main() -> int:
    parser = argparse.ArgumentParser(description='Operaciones de invitación WhatsApp para ALMA')
    parser.add_argument('--env', type=Path, default=DEFAULT_ENV)
    parser.add_argument('--dry-run', action='store_true', help='Validar sin llamar a Meta')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('register-template', help='Registrar la plantilla en Meta para aprobación')
    send = sub.add_parser('send', help='Enviar una plantilla ya aprobada')
    send.add_argument('--recipient', required=True, help='Número con código de país')
    send.add_argument('--name', required=True, help='Nombre de la persona invitada')
    send.add_argument('--link', default=DEFAULT_LINK)
    args = parser.parse_args()
    env = load_env(args.env)

    if args.command == 'register-template':
        payload = template_definition()
        if args.dry_run:
            print(json.dumps({'valid': True, 'operation': 'register-template', 'template': payload}, ensure_ascii=False))
            return 0
        waba_id, token = require(env, 'WHATSAPP_CLOUD_WABA_ID', 'WHATSAPP_CLOUD_ACCESS_TOKEN')
        result = graph_request(f'https://graph.facebook.com/{GRAPH_VERSION}/{waba_id}/message_templates', token, payload)
        print(json.dumps({'ok': True, 'template_id': result.get('id'), 'status': result.get('status', 'submitted')}))
        return 0

    payload = invitation_payload(args.recipient, args.name, args.link)
    if args.dry_run:
        print(json.dumps({'valid': True, 'operation': 'send', 'template': TEMPLATE_NAME, 'recipient_digits': len(payload['to'])}))
        return 0
    phone_id, token = require(env, 'WHATSAPP_CLOUD_PHONE_NUMBER_ID', 'WHATSAPP_CLOUD_ACCESS_TOKEN')
    result = graph_request(f'https://graph.facebook.com/{GRAPH_VERSION}/{phone_id}/messages', token, payload)
    message_id = (result.get('messages') or [{}])[0].get('id')
    print(json.dumps({'ok': True, 'message_id': message_id}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(1)
