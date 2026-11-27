// One analysis section that cannot draw (the website's answer with a field missing or of the wrong kind) shows a short
// note in its own place; the other sections, the bottom bar and the rest of the app keep working. Without it the
// app-level boundary (src/components/error-boundary.tsx) replaces the whole app, and students cannot get a new app
// before JEE Main, so a fix on the website must be enough. A fresh answer from the website (a new `key`) draws again.
import React, { Component, type ErrorInfo, type PropsWithChildren } from "react";
import { ErrorBox } from "@/src/components/ui";

type Props = PropsWithChildren<{ testID: string; onRetry?: () => void }>;

export class SectionGuard extends Component<Props, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[analysis] a section could not draw:", error, info.componentStack ?? "");
  }

  render() {
    if (!this.state.failed) return this.props.children;
    const { onRetry } = this.props;
    // Retry asks the website again and draws once more (a fresh answer also gets a new key from Workspace).
    const retry = () => { onRetry?.(); this.setState({ failed: false }); };
    return <ErrorBox testID={this.props.testID} error="Yeh hissa abhi nahi khul paaya. Baaki analysis aur Solutions chalu hain." retry={retry} />;
  }
}
