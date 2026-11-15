import React from 'react';
import {Link,useNavigate,useParams} from 'react-router-dom';
import {ArrowLeft,FileSearch} from 'lucide-react';
import {useAuth} from '../../../lib/auth';
import {Button} from '../../../components/ui/button';
import {MasterCrumbs} from '../../../components/master/MasterShared';
import {HeldFixer} from '../../../components/books/HeldFixer';
import {TryAsStudent} from '../../../components/master/TryAsStudent';

export default function FixMock(){
 const {bookId,mockId}=useParams();const {user}=useAuth();const nav=useNavigate();const owner=user.role==='owner';
 const tools=q=>nav(`/super-admin/upload?book=${bookId}&${q}`);
 return <div className="admin-page master-page" data-testid="fix-mock-page">
  <MasterCrumbs last="Fix"/>
  <div className="admin-actions"><Button asChild variant="outline"><Link to="/super-admin/fix" data-testid="fix-mock-back"><ArrowLeft size={16}/>All mocks to fix</Link></Button><TryAsStudent m={{kind:'book_mock',id:mockId}} size="default"/>{owner&&<Button asChild variant="ghost"><Link to={`/super-admin/upload?book=${bookId}`} data-testid="fix-mock-page-tools"><FileSearch size={16}/>Page tools for a difficult PDF</Link></Button>}</div>
  <HeldFixer bookId={bookId} mockId={mockId} onOpenPage={owner?n=>tools('page='+n):null} onOpenRules={owner?()=>tools('mock='+mockId):null}/>
 </div>;
}
