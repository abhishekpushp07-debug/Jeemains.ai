from typing import Literal
from pydantic import Field,model_validator
from .astra import StrictModel

class SectionRules(StrictModel):
    name:str=Field(min_length=1,max_length=100)
    question_numbers:list[int]=Field(default_factory=list,max_length=600)
    correct:float|None=Field(default=None,gt=0,le=100,allow_inf_nan=False)
    wrong:float|None=Field(default=None,ge=-100,le=0,allow_inf_nan=False)
    skipped:float|None=Field(default=None,ge=-100,le=100,allow_inf_nan=False)

class PaperRules(StrictModel):
    title:str=Field(min_length=1,max_length=160)
    exam:Literal['JEE Main','BITSAT','COMEDK']|None=None
    test_kind:Literal['mock','chapter','practice']|None=None
    subject:str|None=Field(default=None,max_length=100)
    duration_minutes:int|None=Field(default=None,ge=0,le=600)
    expected_questions:int|None=Field(default=None,ge=1,le=600)
    correct:float|None=Field(default=None,gt=0,le=100,allow_inf_nan=False)
    wrong:float|None=Field(default=None,ge=-100,le=0,allow_inf_nan=False)
    skipped:float|None=Field(default=None,ge=-100,le=100,allow_inf_nan=False)
    sections:list[SectionRules]=Field(default_factory=list,max_length=20)
    instruction_evidence:str=Field(default='',max_length=5000)
    optional_question_policy:str=Field(default='',max_length=1500)
    ambiguities:list[str]=Field(default_factory=list,max_length=20)
    source_type:Literal['practice','pyq','unknown']='unknown'
    source_year:int|None=Field(default=None,ge=2000,le=2026)

class DetectedQuestion(StrictModel):
    paper_label:str=Field(min_length=1,max_length=160)
    number:int=Field(ge=1,le=9999)
    type:Literal['mcq','integer']
    text:str=Field(min_length=1,max_length=15000)
    options:dict[str,str]=Field(default_factory=dict,max_length=8)
    subject:str=Field(default='',max_length=100)
    topic:str=Field(default='',max_length=160)
    section:str=Field(default='',max_length=100)
    accessible_description:str=Field(default='',max_length=15000)
    supplied_answer:str=Field(default='',max_length=40)
    rect:list[float]=Field(min_length=4,max_length=4)
    complete:bool=True
    continues_previous:bool=False
    issues:list[str]=Field(default_factory=list,max_length=12)
    @model_validator(mode='after')
    def bounds(self):
        if not all(0<=x<=1 for x in self.rect) or self.rect[0]>=self.rect[2] or self.rect[1]>=self.rect[3]:raise ValueError('Source rectangle must be normalized x0,y0,x1,y1.')
        if any(not k or len(k)>8 or len(v)>12000 for k,v in self.options.items()):raise ValueError('Invalid option labels/text.')
        return self

class DetectedKey(StrictModel):
    paper_label:str=Field(min_length=1,max_length=160)
    number:int=Field(ge=1,le=9999)
    answer:str=Field(min_length=1,max_length=40)

class ExtractedPage(StrictModel):
    paper_rules:list[PaperRules]=Field(default_factory=list,max_length=8)
    questions:list[DetectedQuestion]=Field(default_factory=list,max_length=35)
    answer_keys:list[DetectedKey]=Field(default_factory=list,max_length=200)
    has_more_questions:bool=False
    issues:list[str]=Field(default_factory=list,max_length=20)

class RuleCheck(StrictModel):
    papers:list[PaperRules]=Field(default_factory=list,max_length=8)

class Clarification(StrictModel):
    rules:PaperRules
    note:str=Field(min_length=5,max_length=2000)
    accept_question_count:bool=False
    practice_all_questions:bool=False

class QuestionRepair(StrictModel):
    text:str=Field(min_length=1,max_length=15000)
    type:Literal['mcq','integer']
    options:dict[str,str]=Field(default_factory=dict,max_length=8)
    supplied_answer:str=Field(default='',max_length=40)
    accessible_description:str=Field(default='',max_length=15000)
    use_corrected_text:bool=False
    note:str=Field(min_length=10,max_length=2000)

class WorkBudget(StrictModel):
    max_ai_questions:int=Field(ge=1,le=3000)
    approve_ai_work:bool

class DailyBudget(StrictModel):
    daily_call_limit:int=Field(ge=0,le=10000)
    approve_usage:bool
