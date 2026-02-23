import type { Account } from "../types";

interface Props {
  accountId: string;
  onChange: (id: string) => void;
}

const ACCOUNTS: Account[] = [
  { id: "acc_001", name: "Amadou Diallo", country: "Senegal" },
  { id: "acc_002", name: "Fatou Ndiaye", country: "Senegal" },
  { id: "acc_003", name: "Moussa Traore", country: "Mali" },
  { id: "acc_004", name: "Aissatou Bah", country: "Cote d'Ivoire" },
  { id: "acc_005", name: "Ibrahim Keita", country: "Burkina Faso" },
  { id: "acc_006", name: "Mariama Sow", country: "Senegal" },
  { id: "acc_007", name: "Ousmane Coulibaly", country: "Mali" },
  { id: "acc_008", name: "Kadiatou Diarra", country: "Cote d'Ivoire" },
];

export function AccountSelector({ accountId, onChange }: Props) {
  return (
    <select
      value={accountId}
      onChange={(e) => onChange(e.target.value)}
      className="text-xs bg-white border border-gray-200 rounded-lg px-2 py-1.5 text-gray-700 focus:outline-none focus:ring-1 focus:ring-relay-500"
    >
      {ACCOUNTS.map((acc) => (
        <option key={acc.id} value={acc.id}>
          {acc.name} ({acc.country})
        </option>
      ))}
    </select>
  );
}
