import React from 'react';
import {Link,useNavigate,useParams,useSearchParams} from 'react-router-dom';
import {ArrowLeft,FileSearch,ListChecks,Wrench} from 'lucide-react';
import {useAuth} from '../../../lib/auth';
import {Button} from '../../../components/ui/button';
import {MasterCrumbs} from '../../../components/master/MasterShared';
import {HeldFixer} from '../../../components/books/HeldFixer';
import {AllQuestions} from '../../../components/books/AllQuestions';
import {TryAsStudent} from '../../../components/master/TryAsStudent';

export default function FixMock(){
 const {bookId,mockId}=useParams();const {user}=useAuth();const nav=useNavigate();const owner=user.role==='owner';
 const [params]=useSearchParams();const all=owner&&params.get('all')==='1';
 const tools=q=>nav(`/super-admin/upload?book=${bookId}&${q}`);
 const here=`/super-admin/fix/${bookId}/${mockId}`;
 return <div className="admin-page master-page" data-testid="fix-mock-page">
  <MasterCrumbs last={all?'Edit questions':'Fix'}/>
  <div className="admin-actions">
   {all?<Button variant="outline" onClick={()=>nav(-1)} data-testid="fix-mock-back"><ArrowLeft size={16}/>Back</Button>:<Button asChild variant="outline"><Link to="/super-admin/fix" data-testid="fix-mock-back"><ArrowLeft size={16}/>All mocks to fix</Link></Button>}
   <TryAsStudent m={{kind:'book_mock',id:mockId}} size="default"/>
   {owner&&(all?<Button asChild variant="ghost"><Link to={here} data-testid="fix-mock-only-marked"><Wrench size={16}/>Only marked questions</Link></Button>:<Button asChild variant="ghost"><Link to={here+'?all=1'} data-testid="fix-mock-all-questions"><ListChecks size={16}/>All questions</Link></Button>)}
   {owner&&<Button asChild variant="ghost"><Link to={`/super-admin/upload?book=${bookId}`} data-testid="fix-mock-page-tools"><FileSearch size={16}/>Page tools for a difficult PDF</Link></Button>}
  </div>
  {all?<AllQuestions bookId={bookId} mockId={mockId} onOpenPage={n=>tools('page='+n)}/>
   :<HeldFixer bookId={bookId} mockId={mockId} onOpenPage={owner?n=>tools('page='+n):null} onOpenRules={owner?()=>tools('mock='+mockId):null}/>}
 </div>;
}
