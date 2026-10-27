import React from "react";
import { BiologyDiagram, Diagram as BioDiagramSpec } from "@/src/components/BiologyDiagram";
import { ScientificDiagram, ScientificDiagramSpec } from "./ScientificDiagram";
import { T } from "./ui";
export type RapidDiagramSpec = BioDiagramSpec | ScientificDiagramSpec;
export function RapidDiagram({ diagram, testID = "rf-scientific-diagram", ...props }: { diagram?: RapidDiagramSpec | null; testID?: string; compact?: boolean; height?: number }) {
  if (!diagram) return null;
  if (["ydse", "ellipse", "charged_ring"].includes(diagram.kind)) return <ScientificDiagram spec={diagram as ScientificDiagramSpec} testID={testID} />;
  if (["plant_cell", "animal_cell", "neuron", "human_heart", "flower", "dna", "chloroplast", "mitochondrion", "nephron", "leaf_section"].includes(diagram.kind)) return <BiologyDiagram diagram={diagram as BioDiagramSpec} testID={testID} {...props} />;
  return <T testID={`${testID}-unavailable`}>This diagram cannot be displayed. Please exit and choose another round.</T>;
}