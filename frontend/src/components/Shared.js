import React, { useEffect, useState } from "react";
import { SourceDetailViewer } from './SourceDetailViewer';
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowUpRight,
  ArrowRight,
  UserRound,
  ChevronDown,
  Loader2,
  BookOpen,
  LogOut,
  CheckCircle2,
  AlertCircle,
  ZoomIn,
} from "lucide-react";
import { useAuth } from "../lib/auth";
import { API, post } from "../lib/api";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { toast } from "sonner";
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Skeleton } from './ui/skeleton';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuLabel, DropdownMenuItem, DropdownMenuSeparator } from './ui/dropdown-menu';
export const Logo = ({testId='brand-home'}) => {
  const {user}=useAuth();
  return <Link to={user?'/home':'/'} className="logo simple-brand official-brand" aria-label="JEELIVE.AI home" data-testid={testId}><img className="official-logo" src="/brand/jeelive-vector.svg" alt="JEELIVE.AI — Score 200+ with AI" width="1415" height="565" decoding="async" data-testid={testId+'-image'}/></Link>;
};
export function Header() {
  const {user,logout}=useAuth();const nav=useNavigate();
  async function signOut(){try{if(await logout())nav('/')}catch(e){toast.error(e.message)}}
  return <header className="site-header simple-header" data-testid="simple-header"><div className="container header-inner"><Logo testId={user?'app-header-logo':'public-header-logo'}/><div className="header-actions simple-header-actions"><span className="header-free-label" data-testid="header-free-label">100% free</span>{user&&<Button asChild variant="ghost" className="header-my-tests"><Link to="/profile" data-testid="header-my-tests"><BookOpen size={17}/>My Tests</Link></Button>}{user?<DropdownMenu><DropdownMenuTrigger asChild><Button variant="outline" className="account-trigger" aria-label="Open account menu" data-testid="app-header-profile-menu"><UserRound size={19}/><ChevronDown size={14}/></Button></DropdownMenuTrigger><DropdownMenuContent align="end" className="account-menu" data-testid="account-menu"><DropdownMenuLabel data-testid="account-menu-label">Your space</DropdownMenuLabel><DropdownMenuItem asChild><Link to="/profile" data-testid="nav-profile">Profile · My Tests</Link></DropdownMenuItem><DropdownMenuItem asChild><Link to="/home" data-testid="nav-home">Home</Link></DropdownMenuItem><DropdownMenuItem asChild><Link to="/saved-drafts" data-testid="nav-saved-drafts">Saved drafts</Link></DropdownMenuItem><DropdownMenuItem asChild><Link to="/competitions" data-testid="nav-competitions">Competitions</Link></DropdownMenuItem>{['owner','reviewer'].includes(user.role)&&<DropdownMenuItem asChild><Link to="/studio" data-testid="nav-studio">Content Studio</Link></DropdownMenuItem>}<DropdownMenuSeparator/><DropdownMenuItem data-testid="logout" onSelect={signOut}><LogOut size={16}/>Sign out</DropdownMenuItem></DropdownMenuContent></DropdownMenu>:<><Button asChild variant="ghost" className="public-login-link"><Link to="/login" data-testid="public-header-login-link">Log in</Link></Button><Button asChild className="btn btn-primary"><Link to="/login" data-testid="public-header-start-free-button">Start free<ArrowUpRight size={16}/></Link></Button></>}</div></div></header>;
}
export const Footer = () => {
 const {user}=useAuth();
 return <footer className={'simple-footer '+(!user?'simple-footer-public':'')} data-testid="site-footer"><div className="container">{!user&&<div className="simple-footer-top"><Logo testId="footer-brand-home"/><p data-testid="footer-free-description">Big ambitions. Zero fees.<br/>100% free for all students.</p><Button asChild variant="ghost"><Link to="/owner-login" data-testid="footer-studio">Content Studio<ArrowUpRight size={15}/></Link></Button></div>}<div className="simple-footer-bottom"><span data-testid="footer-copyright">© {new Date().getFullYear()} JEELIVE.AI</span><nav aria-label="Legal information"><Link to="/privacy" data-testid="footer-privacy">Privacy</Link><Link to="/accessibility" data-testid="footer-accessibility">Accessibility</Link></nav></div>{!user&&<p className="simple-footer-disclosure" data-testid="footer-independent-notice">Independent practice. Not affiliated with NTA, BITS Pilani or COMEDK. Preparation targets are not prediction guarantees.</p>}</div></footer>;
};
export const Loading = ({ text = "Loading your workspace…" }) => (
  <div className="loading" role="status" data-testid="workspace-loading">
    <Loader2 className="spin" aria-hidden="true" />
    <span>{text}</span>
    <Skeleton className="loading-skeleton" />
  </div>
);
export const ErrorBox = ({ error, retry }) =>
  error ? (
    <div className="error-box" role="alert" data-testid="request-error">
      <AlertCircle size={19} />
      <div>
        {typeof error === "string" ? error : error.message}
        {retry && (
          <Button
            data-testid="retry-error"
            className="text-button"
            onClick={retry}
          >
            Try again <ArrowRight size={15} />
          </Button>
        )}
      </div>
    </div>
  ) : null;
export const Empty = ({ title, children, action }) => (
  <div className="empty-state">
    <span className="empty-icon">
      <BookOpen size={30} />
    </span>
    <h3>{title}</h3>
    <p>{children}</p>
    {action}
  </div>
);
export const Badge = ({ children, tone = "" }) => (
  <span className={"badge " + tone}>{children}</span>
);
export const PageTitle = ({ eyebrow, title, description, action }) => (
  <div className="page-title">
    <div>
      {eyebrow && <span className="eyebrow">{eyebrow}</span>}
      <h1>{title}</h1>
      {description && <p>{description}</p>}
    </div>
    {action}
  </div>
);
export function Field({ label, id, children, hint, ...props }) {
  return (
    <label className="field" htmlFor={id}>
      <span>{label}</span>
      {children || <Input id={id} data-testid={id} {...props} />}{" "}
      {hint && <small>{hint}</small>}
    </label>
  );
}
export function SelectField({ label, value, onChange, options, id }) {
  return (
    <div className="field">
      <label id={id + "-label"}>{label}</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger
          className="select-trigger"
          aria-labelledby={id + "-label"}
          data-testid={id}
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem
              key={o.value || o}
              value={o.value || o}
              data-testid={id + "-" + (o.value || o)}
            >
              {o.label || o}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
export function Confirm({
  open,
  onClose,
  title,
  children,
  onConfirm,
  button = "Confirm",
  busy = false,
}) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="tejas-dialog">
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription asChild>
          <div className="dialog-description">{children}</div>
        </DialogDescription>
        <div className="button-row">
          <Button
            className="btn btn-secondary"
            data-testid="confirm-cancel"
            onClick={onClose}
          >
            Go back
          </Button>
          <Button
            className="btn btn-primary"
            data-testid="confirm-accept"
            disabled={busy}
            onClick={onConfirm}
          >
            {busy ? <Loader2 size={17} className="spin" /> : null}
            {button}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
export function SourceImage({ path, alt = "Source region", onError, onLoad, readable = false, testId = 'source' }) {
  const [failed, setFailed] = useState(false);
  const [v, setV] = useState(0);
  const [zoom, setZoom] = useState(false);
  const [refreshed,setRefreshed]=useState(false);
  useEffect(()=>{setFailed(false);setRefreshed(false);setV(0);},[path]);
  return (
    <div className="source-image">
      {failed ? (
        <ErrorBox
          error="This source image did not load. Do not guess missing content."
          retry={() => {
            setFailed(false);
            setRefreshed(false);
            setV(v + 1);
          }}
        />
      ) : readable ? <SourceDetailViewer key={path} inline testId={testId} src={API + path + (path.includes('?') ? '&' : '?') + 'v=' + v} alt={alt} onExpand={()=>setZoom(true)} onLoad={()=>onLoad?.()} onError={async()=>{onError?.();if(!refreshed){setRefreshed(true);try{await post('/auth/refresh');setV(n=>n+1);return;}catch{}}setFailed(true)}}/> : (
        <Button
          className="image-button"
          data-testid={testId+'-zoom'}
          aria-label="Enlarge source image"
          onClick={() => setZoom(true)}
        >
          <img
            src={API + path + (path.includes("?") ? "&" : "?") + "v=" + v}
            alt={alt}
            loading={readable ? 'eager' : 'lazy'}
            onLoad={onLoad}
            onError={async () => {
              onError?.();
              if(!refreshed){setRefreshed(true);try{await post('/auth/refresh');setV(n=>n+1);return;}catch{}}
              setFailed(true);
            }}
          />
          <span>
            <ZoomIn size={14} /> Enlarge
          </span>
        </Button>
      )}
      <Dialog open={zoom} onOpenChange={setZoom}>
        <DialogContent className="image-dialog">
          <DialogTitle>Source detail</DialogTitle>
          <DialogDescription>
            Zoom in and drag to read the original notation. No formula transcription is substituted.
          </DialogDescription>
          <SourceDetailViewer src={API + path + (path.includes('?') ? '&' : '?') + 'v=' + v} alt={alt} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
export const CheckLine = ({ children }) => (
  <span className="check-line">
    <CheckCircle2 size={16} />
    {children}
  </span>
);
