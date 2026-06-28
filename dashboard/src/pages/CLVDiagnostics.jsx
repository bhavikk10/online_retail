import React from "react";
import CaveatCard from "../components/CaveatCard.jsx";
import DataTable from "../components/DataTable.jsx";
import EvidenceNote from "../components/EvidenceNote.jsx";
import LoadingState from "../components/LoadingState.jsx";
import PlotCard from "../components/PlotCard.jsx";
import SectionHeader from "../components/SectionHeader.jsx";
import { fetchCsv } from "../utils/fetchCsv.js";
import { useAsyncResource } from "../utils/fetchJson.js";
import { paths } from "../utils/filePaths.js";

export default function CLVDiagnostics() {
  const { data, loading } = useAsyncResource(
    async () => ({
      residuals: await fetchCsv(paths.data.clvResiduals),
      zero: await fetchCsv(paths.data.zeroDiagnostics),
      errors: await fetchCsv(paths.data.clvErrorDecile),
    }),
    [],
    React,
  );
  if (loading) return <LoadingState />;
  return (
    <div>
      <SectionHeader eyebrow="CLV Diagnostics" title="Ranking Is The Business Use, Exact Spend Is The Hard Part">
        The CLV model is strongest as a prioritization model. It does not need to predict every customer's exact future spend perfectly to be useful; it needs to rank customers well enough that marketing resources can be focused on the highest-value group.
      </SectionHeader>
      <div className="grid gap-5 xl:grid-cols-3">
        <PlotCard title="Zero-spender predicted CLV distribution" src={paths.plots.zeroDistribution} caption="1,071 customers had zero future spend, so some positive expected value on zero-spenders is expected rather than automatically wrong." />
        <PlotCard title="Residuals versus predicted CLV" src={paths.plots.clvResiduals} caption="Extreme high-value customers create the largest errors and explain why ranking and lift matter more than RMSE alone." />
        <PlotCard title="Actual versus predicted CLV" src={paths.plots.clvActual} caption="The model captures broad value ordering, but individual customer spend remains noisy and right-skewed." />
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <EvidenceNote title="Expected value reading">
          Future spend is zero-heavy and right-skewed. A customer can receive positive expected CLV and still spend zero in the observed 90-day window. That is why lift, top-decile capture, and ranking checks are more useful for campaign allocation than demanding perfect customer-level spend prediction.
        </EvidenceNote>
        <CaveatCard title="Whale underprediction">
          The model underpredicts some extreme high-spend customers. This is visible in the diagnostic plots rather than hidden. The business use remains prioritization: the top 10% predicted customers captured about 57.10% of future revenue, and the top 20% captured about 72.73%.
        </CaveatCard>
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <DataTable title="Zero-spender diagnostics" rows={Array.isArray(data.zero) ? data.zero : []} importantColumns={["Customer_ID", "ActualCLV", "PredictedCLV", "PredictionError"]} recordLabel="Customer-level diagnostic records" maxHeight="24rem" />
        <DataTable title="Error by actual CLV decile" rows={Array.isArray(data.errors) ? data.errors : []} importantColumns={["ActualCLVDecile", "MAE", "MeanActualCLV", "MeanPredictedCLV"]} sampleOnly={false} maxHeight="24rem" />
      </div>
    </div>
  );
}
