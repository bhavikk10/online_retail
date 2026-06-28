import DataPipeline from "./DataPipeline.jsx";
import DatasetExplorer from "./DatasetExplorer.jsx";
import SectionHeader from "../components/SectionHeader.jsx";

export default function DataAndPipeline() {
  return (
    <div>
      <SectionHeader eyebrow="Data & Pipeline" title="From Online Retail II Rows To Reviewable Model Tables">
        This section combines the pipeline map with representative record inspection. The project starts from cleaned Online Retail II purchases, builds customer-level retention and CLV tables, and copies representative CSV, JSON, and plot artifacts into public dashboard folders for reproducible review.
      </SectionHeader>
      <div className="space-y-10">
        <DataPipeline />
        <DatasetExplorer />
      </div>
    </div>
  );
}
