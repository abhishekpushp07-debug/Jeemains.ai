import React, { lazy, Suspense, useEffect } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  useLocation,
  useParams,
  Navigate,
} from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { Button } from './components/ui/button';
import { AuthProvider, useAuth } from "./lib/auth";
import "./lib/theme";
import { BottomTabs } from './components/BottomTabs';
import { Header, Footer, Loading, Empty } from "./components/Shared";
import Landing from "./features/Landing";
import "./App.css";
import "./exam-refinement.css";
import "./simple-navigation.css";
import "./full-mocks.css";
import "./result-analysis.css";
const Auth = lazy(() => import("./features/Auth"));
const Exams = lazy(() => import("./features/Exams"));
const AdminWorkspace = lazy(() => import('./features/admin/AdminWorkspace'));
const BookSeries = lazy(() => import('./features/BookSeries'));
const Profile = lazy(() => import('./features/Profile'));
import './learning-workspace.css';
import './bitsat-branches.css';
import './live-series.css';
import './series-streak.css';
import './exam-light.css';
import './vibrant-ui.css';
import './pyq.css';
import './admin.css';
import './master.css';
import './cut-tool.css';
import './analysis2.css';
import './app-theme.css';
const Rank = lazy(() => import('./features/Rank'));
const Mission = lazy(() => import('./features/Mission'));
const PyqCatalogue = lazy(() => import('./features/PyqCatalogue'));
const LiveSeries = lazy(() => import('./features/LiveSeries'));
const Home = lazy(() => import("./features/Home"));
const ExamHub = lazy(() => import("./features/ExamHub"));
const ExamSection = lazy(() => import("./features/ExamSection"));
const ExamHistory = lazy(() => import("./features/ExamHistory"));
const SavedDrafts = lazy(() => import("./features/SavedDrafts"));
const SetDetail = lazy(() => import("./features/SetDetail"));
const Player = lazy(() => import("./features/Player"));
const Results = lazy(() => import("./features/Results"));
const Competitions = lazy(() => import('./features/Competitions'));
const Compare = lazy(() => import('./features/Compare'));
const StudioImport = lazy(() => import('./features/StudioImport'));
const ChapterBookStudio = lazy(() => import('./features/ChapterBookStudio'));
const Info = lazy(() => import("./features/Info"));
const SectionPreview = lazy(() => import('./features/SectionPreview'));
const SeriesPage = lazy(() => import('./features/SeriesPage'));
function Protected({ children, staff = false }) {
  const { user, checking } = useAuth();
  const loc = useLocation();
  if (checking) return <Loading />;
  if (!user)
    return (
      <Navigate
        to={
          (staff ? "/owner-login?next=" : "/login?next=") +
          encodeURIComponent(loc.pathname + loc.search)
        }
        replace
      />
    );
  if (staff && !["owner", "reviewer"].includes(user.role))
    return (
      <Navigate
        to={
          "/owner-login?next=" + encodeURIComponent(loc.pathname + loc.search)
        }
        replace
      />
    );
  return children;
}
const STALE_RELOAD = 'tejas-stale-reload';
class Boundary extends React.Component {
  state = { error: false, reloading: false };
  static getDerivedStateFromError() {
    return { error: true };
  }
  componentDidCatch(error) {
    // A tab opened before a deploy asks for screen files that no longer exist: reload once to get the new ones.
    if (error?.name !== 'ChunkLoadError' && !/Loading (CSS )?chunk|dynamically imported module/i.test(error?.message || '')) return;
    if (Date.now() - Number(sessionStorage.getItem(STALE_RELOAD) || 0) < 60000) return;
    sessionStorage.setItem(STALE_RELOAD, String(Date.now()));
    this.setState({ reloading: true });
    window.location.reload();
  }
  render() {
    if (this.state.reloading) return <Loading />;
    return this.state.error ? (
      <div className="container section">
        <h1>We couldn’t open this screen.</h1>
        <p>Your saved attempts are retained. Reload to try again.</p>
        <Button
          className="btn btn-primary"
          data-testid="reload-app"
          onClick={() => window.location.reload()}
        >
          Reload screen
        </Button>
      </div>
    ) : (
      this.props.children
    );
  }
}
function PlayerRoute() {
  const {id} = useParams();
  const {user} = useAuth();
  return <Player key={`${user.id}:${id}`} />;
}
function LegacyUploads() {
  const loc = useLocation();
  return <Navigate to={'/super-admin/upload' + loc.search} replace />;
}
function StudioHome() {
  return <Navigate to="/super-admin" replace />;
}
function Shell() {
  const loc = useLocation();
  const { user } = useAuth();
  const player = loc.pathname.startsWith("/attempts/");
  const tabs = !!user && !player;
  useEffect(() => {
    document.body.classList.toggle('has-tabs', tabs);
  }, [tabs]);
  useEffect(() => {
    if (!loc.hash) window.scrollTo(0, 0);
  }, [loc.pathname, loc.hash]);
  return (
    <>
      <a className="skip-link" href="#main" data-testid="skip-content">
        Skip to content
      </a>
      {!player && <Header />}
      <main id="main" style={!player?{minHeight:'calc(100svh - 72px)'}:undefined}>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/series/all-india-jee" element={<LiveSeries />} />
            <Route path="/series/:seriesId" element={<SeriesPage />} />
            <Route path="/exams" element={<Exams />} />
            <Route path="/preview/s/:token" element={<SectionPreview />} />
            <Route path="/exams/:examSlug" element={<Protected><ExamHub /></Protected>} />
            <Route path="/exams/jee-main/pyq" element={<Protected><PyqCatalogue /></Protected>} />
            <Route path="/exams/:examSlug/mocks" element={<Protected><ExamSection kind="mocks" /></Protected>} />
            <Route path="/exams/:examSlug/chapters" element={<Protected><ExamSection kind="chapters" /></Protected>} />
            <Route path="/exams/:examSlug/results" element={<Protected><ExamHistory /></Protected>} />
            <Route path="/exams/:examSlug/:sectionSlug" element={<Protected><ExamSection /></Protected>} />
            <Route path="/super-admin/uploads" element={<LegacyUploads />} />
            <Route path="/book-series" element={<Protected><BookSeries /></Protected>} />
            <Route path="/book-series/:id" element={<Protected><BookSeries /></Protected>} />
            <Route path="/super-admin/*" element={<Protected staff><AdminWorkspace /></Protected>} />
            <Route path="/profile" element={<Protected><Profile /></Protected>} />
            <Route path="/rank" element={<Rank />} />
            <Route path="/mission" element={<Protected><Mission /></Protected>} />
            <Route path="/my-tests" element={<Navigate to="/profile" replace />} />
            <Route path="/saved-drafts" element={<Protected><SavedDrafts /></Protected>} />
            <Route path="/login" element={<Auth />} />
            <Route path="/signup" element={<Auth />} />
            <Route path="/forgot-pin" element={<Auth />} />
            <Route path="/owner-login" element={<Auth staff />} />
            <Route
              path="/home"
              element={
                <Protected>
                  <Home />
                </Protected>
              }
            />
            <Route path="/sets/:id" element={<SetDetail />} />
            <Route
              path="/attempts/:id"
              element={
                <Protected>
                  <PlayerRoute />
                </Protected>
              }
            />
            <Route
              path="/results/:id"
              element={
                <Protected>
                  <Results />
                </Protected>
              }
            />
            <Route
              path="/studio"
              element={
                <Protected staff>
                  <StudioHome />
                </Protected>
              }
            />
            <Route path="/competitions" element={<Protected><Competitions /></Protected>} />
            <Route path="/competitions/:id" element={<Protected><Competitions /></Protected>} />
            <Route path="/competitions/:id/compare/:key" element={<Protected><Compare /></Protected>} />
            <Route path="/studio/chapter-books/:id" element={<Protected staff><ChapterBookStudio /></Protected>} />
            <Route path="/studio/imports/:id" element={<Protected staff><StudioImport /></Protected>} />
            <Route
              path="/studio/:id"
              element={
                <Protected staff>
                  <StudioHome />
                </Protected>
              }
            />
            <Route path="/privacy" element={<Info />} />
            <Route path="/accessibility" element={<Info />} />
            <Route
              path="*"
              element={
                <div className="container page" data-testid="not-found-page"><Empty title="This page isn’t here">
                  Use Explore exams to find an available practice set.
                </Empty></div>
              }
            />
          </Routes>
        </Suspense>
      </main>
      {!player && <Footer />}
      {tabs && <BottomTabs />}
      <Toaster position="top-center" visibleToasts={3} closeButton offset={{ top: 'var(--space-24)' }} mobileOffset={{ top: 'calc(var(--space-16) + var(--space-4))', left: 'var(--space-4)', right: 'var(--space-4)' }} />
    </>
  );
}
export default function App() {
  return (
    <Boundary>
      <BrowserRouter>
        <AuthProvider>
          <Shell />
        </AuthProvider>
      </BrowserRouter>
    </Boundary>
  );
}
