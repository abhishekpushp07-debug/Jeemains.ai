import React from 'react';
import {NavLink,Navigate,Route,Routes,useLocation,useSearchParams} from 'react-router-dom';
import {LayoutGrid,Archive,UsersRound,ShieldCheck} from 'lucide-react';
import {useAuth} from '../../lib/auth';
import MasterHome from './master/MasterHome';
import MasterExam from './master/MasterExam';
import MasterType from './master/MasterType';
import WriteEditor from './master/WriteEditor';
import FixList from './master/FixList';
import FixMock from './master/FixMock';
import ReportsPage from './master/ReportsPage';
import ChapterSplit from './master/ChapterSplit';
import AdminStudents from './AdminStudents';
import AdminTeam from './AdminTeam';
import AdminLibrary from './AdminLibrary';
import BookPublishing from '../BookPublishing';
import {StorageBadge} from '../../components/master/StorageBadge';
import '../../book-publishing.css';

const LINKS=[['library','Library',Archive],['students','Students',UsersRound],['team','Team',ShieldCheck]];

function BookRepair(){
 const [params]=useSearchParams();
 return params.get('book')?<BookPublishing/>:<Navigate to="/super-admin" replace/>;
}

function TopBar({owner}){
 const loc=useLocation();
 return <div className="master-topbar" data-testid="super-admin-topbar">
  <NavLink to="/super-admin" end className={()=>'master-home-link'+(['/super-admin','/super-admin/'].includes(loc.pathname)||loc.pathname.includes('/exam/')||loc.pathname.includes('/write/')?' is-active':'')} data-testid="admin-nav-master"><LayoutGrid size={17} aria-hidden="true"/><span>SUPER ADMIN</span><strong>Master</strong></NavLink>
  {owner?<nav className="master-links" aria-label="Super Admin">{LINKS.map(([to,label,Icon])=><NavLink key={to} to={'/super-admin/'+to} data-testid={'admin-nav-'+to}><Icon size={15} aria-hidden="true"/>{label}</NavLink>)}<StorageBadge/></nav>:<p className="master-scope" data-testid="reviewer-scope-note">Reviewer: mocks to fix and student reports.</p>}
 </div>;
}

export default function AdminWorkspace(){
 const {user}=useAuth();const owner=user.role==='owner';
 const gate=el=>owner?el:<Navigate to="/super-admin" replace/>;
 return <div className="container page master-shell" data-testid="super-admin-page">
  <TopBar owner={owner}/>
  <section className="admin-main">
   <Routes>
    <Route index element={<MasterHome/>}/>
    <Route path="exam/:slug" element={gate(<MasterExam/>)}/>
    <Route path="exam/:slug/:sid" element={gate(<MasterType/>)}/>
    <Route path="write/:id" element={<WriteEditor/>}/>
    <Route path="fix" element={<FixList/>}/>
    <Route path="fix/:bookId/:mockId" element={<FixMock/>}/>
    <Route path="reports" element={<ReportsPage/>}/>
    <Route path="chapters/:id" element={gate(<ChapterSplit/>)}/>
    <Route path="upload" element={gate(<BookRepair/>)}/>
    <Route path="library" element={gate(<AdminLibrary/>)}/>
    <Route path="students" element={gate(<AdminStudents/>)}/>
    <Route path="team" element={gate(<AdminTeam/>)}/>
    <Route path="*" element={<Navigate to="/super-admin" replace/>}/>
   </Routes>
  </section>
 </div>;
}
