import { useEffect, useState } from "react";
import type { Account } from "../types";

interface Props {
  accountId: string;
  onChange: (id: string) => void;
}

// Fallback accounts in case API is unavailable
const FALLBACK_ACCOUNTS: Account[] = [
  { id: "acc_001", name: "Amadou Diallo", country: "Senegal", currency: "XOF", region: "West Africa (WAEMU)" },
  { id: "acc_009", name: "Chinedu Okafor", country: "Nigeria", currency: "NGN", region: "West Africa" },
  { id: "acc_012", name: "Wanjiku Kamau", country: "Kenya", currency: "KES", region: "East Africa" },
  { id: "acc_016", name: "Oluwaseun Adeyemi", country: "United Kingdom", currency: "GBP", region: "Diaspora" },
];

export function AccountSelector({ accountId, onChange }: Props) {
  const [accounts, setAccounts] = useState<Account[]>(FALLBACK_ACCOUNTS);

  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
    fetch(`${apiBase}/accounts`)
      .then((res) => res.json())
      .then((data) => {
        if (data.accounts?.length) setAccounts(data.accounts);
      })
      .catch(() => {
        /* keep fallback */
      });
  }, []);

  // Group by region
  const grouped = accounts.reduce<Record<string, Account[]>>((acc, account) => {
    const region = account.region || "Other";
    if (!acc[region]) acc[region] = [];
    acc[region].push(account);
    return acc;
  }, {});

  // Stable region order
  const regionOrder = [
    "West Africa (WAEMU)",
    "West Africa",
    "East Africa",
    "Southern Africa",
    "North Africa",
    "Diaspora",
  ];
  const sortedRegions = regionOrder.filter((r) => grouped[r]);

  return (
    <select
      value={accountId}
      onChange={(e) => onChange(e.target.value)}
      className="text-xs bg-white border border-gray-200 rounded-lg px-2 py-1.5 text-gray-700 focus:outline-none focus:ring-1 focus:ring-relay-500"
    >
      {sortedRegions.map((region) => (
        <optgroup key={region} label={region}>
          {(grouped[region] ?? []).map((acc) => (
            <option key={acc.id} value={acc.id}>
              {acc.name} ({acc.country} · {acc.currency})
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  );
}
