import React from "react";
import { useLocation, Link } from "react-router-dom";
import { PageTitle } from "../components/Shared";
export default function Info() {
  const accessibility = useLocation().pathname === "/accessibility";
  return (
    <div className="container page reading-page">
      <PageTitle
        eyebrow="THE TEJAS STANDARD"
        title={
          accessibility
            ? "A place for different ways of learning."
            : "Simple access. Clear expectations."
        }
        description={
          accessibility
            ? "Accessibility is part of the learning experience—not an optional extra."
            : "How mobile-number entry, saved practice and content permissions work."
        }
      />
      {accessibility ? (
        <article className="card reading-content">
          <h2>Reading and interaction</h2>
          <p>
            jeemains.ai supports keyboard navigation, visible focus, labelled inputs,
            touch-friendly controls and meaningful status labels—not colour
            alone. The interface respects reduced motion. Mobile is a compact
            practice adaptation, not a claim of faithful official exam
            simulation.
          </p>
          <h2>Mathematics and diagrams</h2>
          <p>
            Reviewed text can include accessible KaTeX mathematics. Complex
            source notation and diagrams remain high-resolution images with
            zoom. Publication requires reviewed text equivalents for
            source-image questions and solutions; automated extraction is never
            accessibility approval.
          </p>
          <h2>Answer states and interruptions</h2>
          <p>
            Unvisited, visited, saved, marked for review and pending responses
            are distinguished. Drafts remain on your device until acknowledged.
            Only server-accepted answers before the deadline count. The
            server—not the device clock—controls acceptance.
          </p>
          <h2>Known boundaries</h2>
          <p>
            Formal accessibility certification and a fully tagged accessible PDF
            are not claimed. Source-image descriptions still require careful
            human review. The on-screen solution review supplies the reviewed
            text equivalent.
          </p>
          <h2>Before starting</h2>
          <p>
            Use the device check. If notation or an essential figure is missing,
            do not guess. Ask the content owner to correct it before attempting
            the paper.
          </p>
        </article>
      ) : (
        <article className="card reading-content">
          <h2>Phone number only—not verified identity</h2>
          <p>
            Students enter a mobile number with no OTP, password, email or name.
            India is the default country; international numbers can include a +
            country code. We normalize the number so different spacing formats
            reopen the same profile.
          </p>
          <div className="notice">
            <strong>
              Anyone entering the same phone number can access that profile’s
              saved attempts, answers, results and downloadable personal
              reports, from any device. This is convenience access, not secure
              or verified identity.
            </strong>
          </div>
          <h2>What we store</h2>
          <p>
            The normalized phone number, entry acknowledgement, essential
            session records, exam preference, answers, attempt deadlines,
            results and report-processing records. Staff accounts separately
            store email and a securely hashed password. We do not collect
            payment details, send OTPs or use advertising trackers.
          </p>
          <h2>Session boundaries</h2>
          <p>
            HttpOnly cookies maintain a session after entry. A session cannot
            fetch a different profile’s records by changing an attempt URL.
            However, re-entering another known number intentionally opens that
            number’s profile. Do not use this flow for confidential or
            identity-sensitive assessment.
          </p>
          <h2>Staff and answer-key protection</h2>
          <p>
            Content Studio uses separate authorized staff credentials. A
            phone-only session cannot upload papers, change keys or publish
            content. Raw question papers, keys and solution PDFs remain in
            private application-controlled storage. Unreleased keys are excluded
            from the active player.
          </p>
          <h2>Source rights and downloads</h2>
          <p>
            Upload, audience publication and personal-report redistribution
            permissions are recorded separately. Reports contain every question,
            response and matched solution in the attempt order. A downloaded
            copy is outside application controls; use it only for permitted
            personal study.
          </p>
          <h2>Corrections and withdrawal</h2>
          <p>
            Withdrawing a set stops new starts. Existing attempts keep the
            original content and marking profile. Reviewed grading corrections
            create a labelled new score version rather than overwriting
            historical responses. Storage does not currently provide certified
            permanent erasure; withdrawal is not physical deletion.
          </p>
          <h2>Your device</h2>
          <p>
            Local storage holds pending drafts across recoverable connection
            interruptions. Signing out removes these local drafts and revokes
            the current session. Submit or reconnect before signing out if you
            have unsaved responses.
          </p>
          <h2>Consent and younger learners</h2>
          <p>
            Continuing acknowledges storage of your number and practice records
            under this deliberately unverified access model. Obtain parent or
            guardian permission where required. Use your existing relationship
            with the platform owner for support; no email recovery or
            identity-verification service is included.
          </p>
          <h2>Retention and honest results</h2>
          <p>
            Records remain available for practice history until an authorized
            retention or access action. No fixed automatic deletion period,
            official percentile, admission outcome, verified identity or proven
            high-concurrency capacity is claimed.
          </p>
        </article>
      )}
      <Link to="/exams" className="btn btn-primary" data-testid="info-explore">
        Explore practice
      </Link>
    </div>
  );
}
