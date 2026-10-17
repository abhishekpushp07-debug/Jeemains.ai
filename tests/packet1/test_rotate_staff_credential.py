"""CLI safety validation in-process, under the exact UUID fixture only."""
import importlib.util
import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import pytest

pytestmark = pytest.mark.asyncio(loop_scope='session')
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def cli():
    spec = importlib.util.spec_from_file_location('isolated_staff_cli', ROOT/'backend/tools/rotate_staff_credential.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def args(account_id, **changes):
    value = {'account_id':account_id,'expected_generation':0,'apply':False,
             'confirm_revoke':False,'confirm_fenced_deployment':False}
    return Namespace(**{**value,**changes})


async def seeded(clean_db, role='reviewer'):
    uid = str(uuid4())
    await clean_db.tejas_users.insert_one({'id':uid,'role':role,'credential_generation':0,
        'email':f'synthetic-cli-{uid}@example.com','password_hash':'SYNTHETIC-NONFUNCTIONAL-HASH'})
    return uid


def forbid_sensitive_paths(cli, monkeypatch):
    def forbidden_prompt(*a,**k):
        raise AssertionError('A dry-run or denied operation must not request a replacement secret')
    async def forbidden_rotation(*a,**k):
        raise AssertionError('A dry-run or denied operation must not reach the mutator')
    monkeypatch.setattr(cli.getpass,'getpass',forbidden_prompt)
    monkeypatch.setattr(cli,'rotate_staff_credential',forbidden_rotation)


async def test_cli_dry_run_no_prompt_no_mutation(cli, clean_db, monkeypatch, capsys):
    uid = await seeded(clean_db)
    before = await clean_db.tejas_users.find_one({'id':uid})
    forbid_sensitive_paths(cli,monkeypatch)
    await cli.run(args(uid))
    raw = capsys.readouterr().out
    assert json.loads(raw)['mode'] == 'DRY_RUN_NO_MUTATION'
    assert json.loads(raw)['expected_generation'] == 0
    assert json.loads(raw)['next_generation'] == 1
    assert set(json.loads(raw)) == {'mode','account_id','expected_generation','next_generation','warning'}
    assert before == await clean_db.tejas_users.find_one({'id':uid})
    assert before['email'] not in raw and 'SYNTHETIC-NONFUNCTIONAL-HASH' not in raw


@pytest.mark.parametrize('revoke,fenced,tty',[(False,True,True),(True,False,True),(True,True,False)])
async def test_cli_each_safety_gate_denies_without_mutation(cli,clean_db,monkeypatch,revoke,fenced,tty):
    uid = await seeded(clean_db)
    before = await clean_db.tejas_users.find_one({'id':uid})
    forbid_sensitive_paths(cli,monkeypatch)
    monkeypatch.setattr(cli.sys,'stdin',SimpleNamespace(isatty=lambda:tty))
    with pytest.raises(ValueError,match='Apply requires'):
        await cli.run(args(uid,apply=True,confirm_revoke=revoke,confirm_fenced_deployment=fenced))
    assert before == await clean_db.tejas_users.find_one({'id':uid})


async def test_cli_wrong_generation_and_student_deny(cli,clean_db,monkeypatch):
    uid = await seeded(clean_db)
    before = await clean_db.tejas_users.find_one({'id':uid})
    forbid_sensitive_paths(cli,monkeypatch)
    with pytest.raises(ValueError,match='Expected generation'):
        await cli.run(args(uid,expected_generation=1))
    assert before == await clean_db.tejas_users.find_one({'id':uid})
    student = await seeded(clean_db,'student')
    student_before = await clean_db.tejas_users.find_one({'id':student})
    with pytest.raises(ValueError,match='No eligible staff'):
        await cli.run(args(student))
    assert student_before == await clean_db.tejas_users.find_one({'id':student})
