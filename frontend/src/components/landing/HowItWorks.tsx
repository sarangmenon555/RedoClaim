const FLOW = ["Upload", "Extract", "Retrieve", "Analyse", "Explain", "Verify"];

const STEPS = [
  {
    title: "Your Documents",
    desc: "Policy, CIS, rejection letter and other relevant documents.",
  },
  {
    title: "Document Processing",
    desc: "Relevant text and information are extracted.",
  },
  {
    title: "Knowledge Retrieval",
    desc: "Relevant policy and regulatory information is retrieved.",
  },
  {
    title: "AI Analysis",
    desc: "The system compares the available information and generates an explanation.",
  },
  {
    title: "Source-Supported Response",
    desc: "The user receives an understandable explanation with relevant references.",
  },
  {
    title: "Human Or Official Verification",
    desc: "Users are directed to official channels when formal action is required.",
  },
];

export default function HowItWorks({ id, title = "How RedoClaim Works" }: { id?: string; title?: string }) {
  return (
    <section id={id} className="border-y py-20" style={{ borderColor: "var(--surface-4)", background: "var(--surface-1)" }}>
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>
            {title}
          </h2>
          <div className="flex items-center justify-center gap-x-2 gap-y-1 flex-wrap text-sm font-medium" style={{ color: "#A78BFA" }}>
            {FLOW.map((word, i) => (
              <span key={word} className="flex items-center gap-2">
                {word}
                {i < FLOW.length - 1 && <span style={{ color: "var(--text-tertiary)" }}>→</span>}
              </span>
            ))}
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {STEPS.map((step, i) => (
            <div key={step.title} className="card p-5" style={{ background: "var(--surface-2)" }}>
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mb-4"
                style={{ background: "rgba(139,92,246,0.15)", color: "#C4B5FD", border: "1px solid rgba(139,92,246,0.25)" }}
              >
                {i + 1}
              </div>
              <h3 className="font-semibold mb-2" style={{ color: "var(--text-primary)" }}>{step.title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{step.desc}</p>
            </div>
          ))}
        </div>

        <p className="text-xs text-center mt-8 max-w-2xl mx-auto leading-relaxed" style={{ color: "var(--text-tertiary)" }}>
          RedoClaim output is AI-assisted information, not a legal, regulatory or insurance determination.
        </p>
      </div>
    </section>
  );
}
