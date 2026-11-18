import exported from "../assets/website-2026-10-26/design-tokens.json";

// Unmodified owner export, not independently invented colour values.
export const websiteDesign = exported.viewports["390"];
export const componentStyle = (name: keyof typeof websiteDesign.other_component_states) => websiteDesign.other_component_states[name].style;
