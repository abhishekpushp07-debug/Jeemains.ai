import React from 'react';
import {Link,useNavigate,useParams,useSearchParams} from 'react-router-dom';
import {ArrowLeft,FileSearch,ListChecks,Wrench} from 'lucide-react';
import {useAuth} from '../../../lib/auth';
import {usePageTitle} from '../../../lib/pageMeta';
import {Button} from '../../../components/ui/button';
import {MasterCrumbs} from '../../../components/master/MasterShared';
import {HeldFixer} from '../../../components/books/HeldFixer';
import {AllQuestions} from '../../../components/books/AllQuestions';
import {TryAsStudent} from '../../../components/master/TryAsStudent';
import {DuplicateAlert} from '../../../components/master/Duplicates';

export default function FixMock(){
 const {bookId,mockId}=useParams();const {user}=useAuth();const nav=useNavigate();const owner=user.role==='owner';
 const [params]=useSearchParams();const all=owner&&params.get('all')==='1';
 usePageTitle(all?'Sawaal edit karo':'Fix');
 const tools=q=>nav(`/super-admin/upload?book=${bookId}&${q}`);
 const here=`/super-admin/fix/${bookId}/${mockId}`;
 return <div className="admin-page master-page" data-testid="fix-mock-page">
  <MasterCrumbs last={all?'Sawaal edit karo':'Fix'}/>
  <div className="admin-actions">
   {all?<Button variant="outline" onClick={()=>nav(-1)} data-testid="fix-mock-back"><ArrowLeft size={16}/>Wapas</Button>:<Button asChild variant="outline"><Link to="/super-admin/fix" data-testid="fix-mock-back"><ArrowLeft size={16}/>Fix wale saare mock</Link></Button>}
   <TryAsStudent m={{kind:'book_mock',id:mockId}} size="default"/>
   {owner&&(all?<Button asChild variant="ghost"><Link to={here} data-testid="fix-mock-only-marked"><Wrench size={16}/>Sirf marked sawaal</Link></Button>:<Button asChild variant="ghost"><Link to={here+'?all=1'} data-testid="fix-mock-all-questions"><ListChecks size={16}/>Saare sawaal</Link></Button>)}
   {owner&&<Button asChild variant="ghost"><Link to={`/super-admin/upload?book=${bookId}`} data-testid="fix-mock-page-tools"><FileSearch size={16}/>Mushkil PDF ke page tools</Link></Button>}
  </div>
  <DuplicateAlert mockId={mockId}/>
  {all?<AllQuestions bookId={bookId} mockId={mockId} onOpenPage={n=>tools('page='+n)}/>
   :<HeldFixer bookId={bookId} mockId={mockId} onOpenPage={owner?n=>tools('page='+n):null} onOpenRules={owner?()=>tools('mock='+mockId):null}/>}
 </div>;
}
