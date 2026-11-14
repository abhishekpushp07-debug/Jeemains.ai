import React from 'react';
import {NavLink,Navigate,Route,Routes} from 'react-router-dom';
import {LayoutDashboard,FolderTree,UploadCloud,ClipboardCheck,CalendarClock,UsersRound,ShieldCheck,Archive} from 'lucide-react';
import {useAuth} from '../../lib/auth';
import AdminOverview from './AdminOverview';
import AdminContent from './AdminContent';
import AdminUpload from './AdminUpload';
import UploadWizard from './UploadWizard';
import AdminReview from './AdminReview';
import AdminSchedule from './AdminSchedule';
import AdminStudents from './AdminStudents';
import AdminTeam from './AdminTeam';
import AdminLibrary from './AdminLibrary';
import '../../book-publishing.css';

const NAV=[['','Overview',LayoutDashboard,true],['content','Exams & Content',FolderTree,true],['upload','Upload',UploadCloud,true],['review','Review',ClipboardCheck,false],['schedule','Schedule & Live',CalendarClock,true],['library','Library',Archive,true],['students','Students',UsersRound,true],['team','Team',ShieldCheck,true]];

export default function AdminWorkspace(){
 const {user}=useAuth();const owner=user.role==='owner';
 const gate=el=>owner?el:<Navigate to="/super-admin/review" replace/>;
 return <div className="container page admin-shell" data-testid="super-admin-page">
  <aside className="admin-nav" aria-label="Super Admin">
   <span className="admin-nav-label" data-testid="super-admin-eyebrow">SUPER ADMIN</span>
   <nav>{NAV.filter(([, , , ownerOnly])=>owner||!ownerOnly).map(([to,label,Icon])=><NavLink key={label} to={'/super-admin'+(to?'/'+to:'')} end={!to} data-testid={'admin-nav-'+(to||'overview')}><Icon size={18} aria-hidden="true"/><span>{label}</span></NavLink>)}</nav>
   {!owner&&<p className="admin-nav-note" data-testid="reviewer-scope-note">Reviewer access covers review work only.</p>}
  </aside>
  <section className="admin-main">
   <Routes>
    <Route index element={gate(<AdminOverview/>)}/>
    <Route path="content" element={gate(<AdminContent/>)}/>
    <Route path="upload" element={gate(<AdminUpload/>)}/>
    <Route path="upload/new" element={gate(<UploadWizard/>)}/>
    <Route path="review" element={<AdminReview/>}/>
    <Route path="schedule" element={gate(<AdminSchedule/>)}/>
    <Route path="library" element={gate(<AdminLibrary/>)}/>
    <Route path="students" element={gate(<AdminStudents/>)}/>
    <Route path="team" element={gate(<AdminTeam/>)}/>
    <Route path="*" element={<Navigate to="/super-admin" replace/>}/>
   </Routes>
  </section>
 </div>;
}
