declare module "plotly.js" {
  export type Data = any;
  export type Layout = any;
  const Plotly: any;
  export default Plotly;
}

declare module "plotly.js-dist-min" {
  const Plotly: any;
  export default Plotly;
}

declare module "react-plotly.js/factory" {
  import type { ComponentType } from "react";
  import type Plotly from "plotly.js";
  const createPlotlyComponent: (plotly: typeof Plotly) => ComponentType<any>;
  export default createPlotlyComponent;
}
