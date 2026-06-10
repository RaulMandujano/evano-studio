import { faqs, type Faq } from "@/content/site";

type FaqListProps = {
  /** Optionally limit how many questions to show (e.g. a preview on the home page). */
  limit?: number;
  items?: Faq[];
};

/** Renders a list of FAQ entries. Used on both the home page and /faq. */
export function FaqList({ limit, items }: FaqListProps) {
  const list = (items ?? faqs).slice(0, limit ?? undefined);

  return (
    <div className="faq-list">
      {list.map((f) => (
        <div key={f.question} className="faq-item">
          <h3 className="faq-q">{f.question}</h3>
          <p className="faq-a">{f.answer}</p>
        </div>
      ))}
    </div>
  );
}
