interface Props {
  onSelect: (query: string) => void;
}

interface QueryGroup {
  label: string;
  queries: string[];
}

const SAMPLE_QUERIES: QueryGroup[] = [
  {
    label: "English",
    queries: [
      "What is my account balance?",
      "Show me my last 5 transactions",
      "How much is the fee to send money to Nigeria?",
      "Find the nearest agent in Nairobi",
      "What's the exchange rate from GBP to NGN?",
      "I was charged twice for a transaction",
    ],
  },
  {
    label: "French",
    queries: [
      "Quel est mon solde?",
      "Montrez-moi mes 3 dernieres transactions",
      "Combien coute l'envoi de 100 000 FCFA en Cote d'Ivoire?",
      "Trouvez un agent a Casablanca",
      "Quelle est la politique de remboursement?",
    ],
  },
  {
    label: "Swahili",
    queries: [
      "Salio yangu ni kiasi gani?",
      "Nionyeshe miamala yangu ya hivi karibuni",
      "Ada ya kutuma pesa Tanzania ni kiasi gani?",
      "Nataka kupata msaada kuhusu malipo",
    ],
  },
];

export function SampleQueries({ onSelect }: Props) {
  return (
    <div className="px-4 py-6">
      <p className="text-sm text-gray-500 text-center mb-4">
        Try a sample query to get started
      </p>
      <div className="space-y-4 max-w-lg mx-auto">
        {SAMPLE_QUERIES.map((group) => (
          <div key={group.label}>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              {group.label}
            </h3>
            <div className="flex flex-wrap gap-2">
              {group.queries.map((query) => (
                <button
                  key={query}
                  onClick={() => onSelect(query)}
                  className="text-xs bg-white border border-gray-200 hover:border-relay-300 hover:bg-relay-50 text-gray-700 px-3 py-1.5 rounded-full transition-colors"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
