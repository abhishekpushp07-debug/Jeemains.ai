"""BITSAT full mocks imported from the owner-supplied combined PDF; Studio sees live and held-back status."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from .auth import staff
from .db import db, now

router = APIRouter(prefix='/api', tags=['Full mocks'])
mock_books = db.tejas_mock_books


class MockStatus(BaseModel):
    number: int
    set_id: str
    title: str
    status: str
    reasons: list[str] = []
    main_count: int = 0
    bonus_count: int = 0
    keys: int = 0
    sections: dict[str, int] = {}
    pages: list[int] = []


class MockBookView(BaseModel):
    id: str
    title: str
    source_name: str
    source_sha256: str
    pages: int
    live: int
    held: int
    end_at: float | None = None
    mocks: list[MockStatus]
    server_now: float


class MockBookList(BaseModel):
    items: list[MockBookView]


@router.get('/studio/mock-books', response_model=MockBookList)
async def list_mock_books(u=Depends(staff)):
    rows = await mock_books.find({}, {'_id': 0}).sort('created_at', -1).limit(20).to_list(20)
    return MockBookList(items=[MockBookView(**{k: r.get(k) for k in MockBookView.model_fields if k != 'server_now'},
        server_now=now()) for r in rows])
