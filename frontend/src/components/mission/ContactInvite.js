// Mission "Contacts se dost chuno": the phone browser's own contact picker (Android Chrome). Only the friends the student
// picks are sent, saved with their consent; each one gets a WhatsApp button with the student's own link.
import React, { useEffect, useState } from 'react';
import { Loader2, MessageCircle, Trash2, UserPlus } from 'lucide-react';
import { api, del, post } from '../../lib/api';
import { track } from '../../lib/track';

const CAN = typeof window !== 'undefined' && 'contacts' in navigator && 'ContactsManager' in window;
const wa = (phone, text) => `https://wa.me/${phone.replace(/\D/g, '')}?text=${encodeURIComponent(text)}`;
const shape = c => ({ name: (c.name?.[0] || '').slice(0, 120), tel: (c.tel || []).filter(Boolean).slice(0, 6).map(t => String(t).slice(0, 40)) });

function ContactRow({ c, text, onRemove }) {
  return <li data-testid={`mission-contact-${c.id}`}>
    <span><b>{c.name || c.phone}</b>{c.name ? <small>{c.phone}</small> : null}</span>
    <a href={wa(c.phone, text)} target="_blank" rel="noopener noreferrer" className="ms-contacts-wa" data-testid={`mission-contact-wa-${c.id}`}><MessageCircle size={15} />Bhejo</a>
    <button type="button" className="ms-contacts-del" onClick={() => onRemove(c.id)} aria-label={`${c.name || c.phone} hatao`} data-testid={`mission-contact-remove-${c.id}`}><Trash2 size={15} /></button>
  </li>;
}

export function ContactInvite({ text }) {
  const [items, setItems] = useState([]), [busy, setBusy] = useState(false), [note, setNote] = useState('');
  useEffect(() => { if (CAN) api('/mission/contacts').then(r => setItems(r.items)).catch(() => {}); }, []);
  if (!CAN) return null;
  const pick = async () => {
    if (busy) return;
    setBusy(true); setNote('');
    try {
      const chosen = await navigator.contacts.select(['name', 'tel'], { multiple: true });
      const list = chosen.map(shape).filter(c => c.tel.length).slice(0, 100);
      if (!list.length) { if (chosen.length) setNote('Chune gaye contacts mein mobile number nahi mila.'); return; }
      const r = await post('/mission/contacts', { contacts: list });
      setItems(r.items); track('contacts_pick');
      setNote(r.full ? `${r.saved} dost jude. Ek account mein ${r.max} dost tak jud sakte hain.` : `${r.saved} dost jude. Ab har dost ko WhatsApp par bhejo.`);
    } catch (e) { if (e?.status) setNote(e.message || 'Contacts nahi jude. Dobara try karo.'); }
    finally { setBusy(false); }
  };
  const remove = async id => {
    setItems(xs => xs.filter(x => x.id !== id));
    try { await del('/mission/contacts/' + id); } catch { setNote('Hataya nahi gaya. Dobara try karo.'); api('/mission/contacts').then(r => setItems(r.items)).catch(() => {}); }
  };
  return <section className="ms-contacts" data-testid="mission-contacts">
    <button type="button" className="ms-contacts-pick" onClick={pick} disabled={busy} data-testid="mission-contacts-pick">
      {busy ? <Loader2 size={20} className="animate-spin" /> : <UserPlus size={20} />}<span><b>Contacts se dost chuno</b><small>Jinhe invite karna hai, sirf unhe chuno</small></span></button>
    <p className="ms-contacts-consent" data-testid="mission-contacts-consent">Aap jo dost chunoge, unka naam aur number JEELIVE ke paas save hoga taaki team dekh sake kise invite kiya gaya. Kisi ko bhi kabhi bhi hata sakte ho.</p>
    {note ? <p className="ms-contacts-note" role="status" data-testid="mission-contacts-note">{note}</p> : null}
    {items.length ? <ul className="ms-contacts-list" data-testid="mission-contacts-list">{items.map(c => <ContactRow key={c.id} c={c} text={text} onRemove={remove} />)}</ul> : null}
  </section>;
}
