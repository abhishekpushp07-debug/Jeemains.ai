"""Operator-only explicit credential rotation. Never accepts passwords in argv.

Dry-run is the default. --apply --confirm-revoke --confirm-fenced-deployment are required for mutation.
This utility is NOT invoked automatically by the app or by a scheduled task.
"""
import argparse
import asyncio
import getpass
import json
from pathlib import Path
import sys
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1]/'.env', override=False)
from tejas.db import users, client
from tejas.staff_credentials import generation, rotate_staff_credential


async def run(args):
    account_id = str(UUID(args.account_id))
    account = await users.find_one({'id':account_id,'role':{'$in':['owner','reviewer']}},
        {'_id':0,'id':1,'role':1,'credential_generation':1})
    if account is None:
        raise ValueError('No eligible staff account found')
    current = generation(account)
    if current != args.expected_generation:
        raise ValueError('Expected generation does not match; inspect safely before applying')
    if not args.apply:
        print(json.dumps({'mode':'DRY_RUN_NO_MUTATION','account_id':account_id,
            'expected_generation':current,'next_generation':current+1,
            'warning':'Use an approved protected terminal and secret handoff. Applying revokes prior staff sessions; keep phone/student sessions unchanged.'}))
        return
    if not args.confirm_revoke or not args.confirm_fenced_deployment or not sys.stdin.isatty():
        raise ValueError('Apply requires explicit revocation confirmation, confirmation that every serving auth node enforces generation fencing, and a protected interactive terminal')
    password = getpass.getpass('New staff secret (not echoed): ')
    repeated = getpass.getpass('Repeat new staff secret: ')
    if password != repeated:
        raise ValueError('Replacement entries differ')
    receipt = await rotate_staff_credential(account_id,current,password,str(uuid4()))
    password = repeated = None
    print(receipt.model_dump_json())


def main():
    parser = argparse.ArgumentParser(description='Safe staff credential generation rotation; dry-run by default')
    parser.add_argument('--account-id',required=True)
    parser.add_argument('--expected-generation',type=int,required=True)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--confirm-revoke',action='store_true')
    parser.add_argument('--confirm-fenced-deployment',action='store_true')
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except Exception:
        # Never echo exceptions containing secrets/connection strings/driver data.
        raise SystemExit('Rotation did not complete cleanly. Inspect the account generation and opaque operation receipt through the protected operator channel before retrying; never assume a network error means no commit.')
    finally:
        client.close()


if __name__ == '__main__':
    main()
