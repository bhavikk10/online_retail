import { useState } from "react";
import { Boxes, Brain, FolderTree, Gauge, GitBranch, LineChart } from "lucide-react";
import Layout from "./components/Layout.jsx";
import RouteErrorBoundary from "./components/RouteErrorBoundary.jsx";
import Overview from "./pages/Overview.jsx";
import DataAndPipeline from "./pages/DataAndPipeline.jsx";
import CustomerValue from "./pages/CustomerValue.jsx";
import Segmentation from "./pages/Segmentation.jsx";
import Forecasting from "./pages/Forecasting.jsx";
import ModelReviewAppendix from "./pages/ModelReviewAppendix.jsx";

export const navItems = [
  { id: "overview", label: "Overview", icon: Gauge, component: Overview },
  { id: "data-pipeline", label: "Data & Pipeline", icon: GitBranch, component: DataAndPipeline },
  { id: "customer-value", label: "Customer Value", icon: Brain, component: CustomerValue },
  { id: "customer-segments", label: "Customer Segments", icon: Boxes, component: Segmentation },
  { id: "revenue-forecast", label: "Revenue Forecast", icon: LineChart, component: Forecasting },
  { id: "model-review", label: "Model Review & Appendix", icon: FolderTree, component: ModelReviewAppendix },
];

export default function App() {
  const [activePage, setActivePage] = useState("overview");
  const Active = navItems.find((item) => item.id === activePage)?.component || Overview;
  return (
    <Layout activePage={activePage} setActivePage={setActivePage}>
      <RouteErrorBoundary routeKey={activePage}>
        <Active />
      </RouteErrorBoundary>
    </Layout>
  );
}
