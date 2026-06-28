import SectionHeader from "../components/SectionHeader.jsx";

const recommendations = [
  {
    title: "Protect High-Value Loyalists",
    role: "Protect",
    evidence: "630 customers, 22.68% customer share, 65.35% future revenue share, 86.98% retention, and £2,592.06 average future spend.",
    action: "Prioritize service recovery, loyalty benefits, early access, and low-friction reorder prompts. Losing a small number of these customers can outweigh gains from much larger low-value groups.",
  },
  {
    title: "Grow Regular Mid-Value Customers",
    role: "Grow",
    evidence: "1,031 customers, 37.11% customer share, 18.51% future revenue share, 62.46% retention, and £448.70 average future spend.",
    action: "Use cross-sell bundles and timed reminders. This group is large enough that modest conversion or basket-size gains can matter, but campaign cost should remain disciplined.",
  },
  {
    title: "Reactivate At-Risk Inactive Customers Selectively",
    role: "Reactivate",
    evidence: "697 customers, 25.09% customer share, 10.65% future revenue share, 52.22% retention, and 127.04 average recency days.",
    action: "Use CLV ranking to choose which inactive customers justify incentives. Avoid broad discounting because nearly 47.78% have zero future spend.",
  },
  {
    title: "Nurture New / One-Time Customers Cheaply",
    role: "Nurture",
    evidence: "420 customers, 15.12% customer share, 5.48% future revenue share, 35.95% retention, and £326.20 average future spend.",
    action: "Use low-cost welcome journeys and product education rather than expensive incentives. The group has the weakest retention and should not receive equal spend.",
  },
  {
    title: "Allocate Budget By CLV Rank",
    role: "Prioritize",
    evidence: "The top 10% predicted CLV customers captured 57.10% of future revenue; the top 20% captured 72.73%.",
    action: "Use ranked campaign tiers rather than a single retention threshold. Retention tells whether customers return; CLV ranking tells where the revenue concentration sits.",
  },
];

export default function Recommendations() {
  return (
    <div>
      <SectionHeader eyebrow="Recommendations" title="Actions Tied To Evidence, Not Generic Campaign Ideas">
        These recommendations translate the CLV and segmentation findings into campaign priorities. They remain hypotheses for business testing, but each recommendation is tied to saved segment metrics or CLV lift evidence from the project artifacts.
      </SectionHeader>
      <div className="grid gap-4 lg:grid-cols-2">
        {recommendations.map((item) => (
          <div key={item.title} className="glass rounded-lg p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-[#744210]">{item.role}</p>
            <h3 className="mt-2 text-xl font-semibold text-[#172033]">{item.title}</h3>
            <p className="mt-3 text-sm leading-6 text-[#4b5563]"><span className="font-semibold text-[#172033]">Evidence:</span> {item.evidence}</p>
            <p className="mt-3 text-sm leading-6 text-[#4b5563]"><span className="font-semibold text-[#172033]">Recommended use:</span> {item.action}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
