import React from 'react';
import {useAuth} from '../lib/auth';
import {ExamBreadcrumbs} from '../components/exams/ExamNavigation';
import {DraftRecoveryPanel} from '../components/offline/DraftRecoveryPanel';
export default function SavedDrafts(){const {user}=useAuth();return <div className="container page" data-testid="saved-drafts-page"><ExamBreadcrumbs section={{label:'Saved drafts'}}/><DraftRecoveryPanel userId={user.id}/></div>}
