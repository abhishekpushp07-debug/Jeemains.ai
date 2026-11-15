import React from 'react';
import {AdminHeading} from '../../../components/admin/AdminShared';
import {MasterCrumbs} from '../../../components/master/MasterShared';
import {QuestionReportsPanel} from '../../../components/studio/QuestionReportsPanel';

export default function ReportsPage(){
 return <div className="admin-page master-page" data-testid="reports-page">
  <MasterCrumbs last="Student reports"/>
  <AdminHeading testId="reports-title" title="Student reports" text="Questions students marked as wrong. Review each one; scores change only when you correct a key."/>
  <section className="admin-panel"><QuestionReportsPanel/></section>
 </div>;
}
